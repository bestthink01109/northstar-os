import zipfile
import os
import shutil
from lxml import etree

def get_sheet_map(xlsx_path):
    """
    Excel内の「シート名」と「XMLファイル名(sheetN.xml)」の対応マップを取得する
    """
    sheet_map = {}
    temp_dir = f"temp_map_{os.path.basename(xlsx_path)}"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        with zipfile.ZipFile(xlsx_path, 'r') as z:
            z.extract("xl/workbook.xml", temp_dir)
            z.extract("xl/_rels/workbook.xml.rels", temp_dir)
            
            # workbook.xml から name と rId を取得
            wb_tree = etree.parse(os.path.join(temp_dir, "xl/workbook.xml"))
            ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
                  "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
            
            sheets = wb_tree.xpath("//main:sheet", namespaces=ns)
            
            # rels から rId と Target(sheetN.xml) の対応を取得
            rel_tree = etree.parse(os.path.join(temp_dir, "xl/_rels/workbook.xml.rels"))
            rel_ns = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}
            rels = rel_tree.xpath("//rel:Relationship", namespaces=rel_ns)
            id_to_file = {r.get("Id"): os.path.basename(r.get("Target")) for r in rels}
            
            for s in sheets:
                name = s.get("name")
                r_id = s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
                sheet_file = id_to_file.get(r_id)
                if sheet_file:
                    sheet_map[name] = sheet_file
    finally:
        shutil.rmtree(temp_dir)
    return sheet_map

def inject_images(original_xlsx, generated_xlsx, final_xlsx):
    """
    original_xlsx から画像情報を抽出し、generated_xlsx に注入して final_xlsx を作成する
    """
    print(f"画像注入プロセス開始: {original_xlsx} -> {generated_xlsx}")
    
    orig_map = get_sheet_map(original_xlsx)
    gen_map = get_sheet_map(generated_xlsx)
    
    temp_orig = "temp_orig_inject"
    temp_gen = "temp_gen_inject"
    for d in [temp_orig, temp_gen]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)

    with zipfile.ZipFile(original_xlsx, 'r') as z: z.extractall(temp_orig)
    with zipfile.ZipFile(generated_xlsx, 'r') as z: z.extractall(temp_gen)

    # 1. 共通パーツのコピー (media, drawings)
    for folder in ["xl/drawings", "xl/media"]:
        src = os.path.join(temp_orig, folder)
        if os.path.exists(src):
            dst = os.path.join(temp_gen, folder)
            if os.path.exists(dst): shutil.rmtree(dst)
            shutil.copytree(src, dst)
            
    # 2. VML 等のコピー
    for f in os.listdir(os.path.join(temp_orig, "xl")):
        if f.startswith("vmlDrawing") or f.endswith(".vml"):
            shutil.copy2(os.path.join(temp_orig, "xl", f), os.path.join(temp_gen, "xl", f))

    # 3. 各シートの紐付け情報を移植
    for sheet_name, orig_file in orig_map.items():
        if sheet_name in gen_map:
            gen_file = gen_map[sheet_name]
            print(f"  Transferring drawings: {sheet_name} ({orig_file} -> {gen_file})")
            
            # relsファイルの移植
            orig_rel_path = os.path.join(temp_orig, "xl/worksheets/_rels", f"{orig_file}.rels")
            if os.path.exists(orig_rel_path):
                gen_rel_dir = os.path.join(temp_gen, "xl/worksheets/_rels")
                if not os.path.exists(gen_rel_dir): os.makedirs(gen_rel_dir)
                shutil.copy2(orig_rel_path, os.path.join(gen_rel_dir, f"{gen_file}.rels"))
            
            # sheetN.xml 自体の中にある <drawing> タグの移植
            # (openpyxlが削除してしまっているため、オリジナルからタグだけをコピーする)
            orig_xml = os.path.join(temp_orig, "xl/worksheets", orig_file)
            gen_xml = os.path.join(temp_gen, "xl/worksheets", gen_file)
            
            if os.path.exists(orig_xml) and os.path.exists(gen_xml):
                o_tree = etree.parse(orig_xml)
                g_tree = etree.parse(gen_xml)
                g_root = g_tree.getroot()
                
                ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                drawings = o_tree.xpath("//main:drawing", namespaces=ns)
                legacy = o_tree.xpath("//main:legacyDrawing", namespaces=ns)
                
                if drawings or legacy:
                    # openpyxlが中途半端に作っているタグがあれば削除
                    for d in g_root.xpath("//main:drawing", namespaces=ns): d.getparent().remove(d)
                    for d in g_root.xpath("//main:legacyDrawing", namespaces=ns): d.getparent().remove(d)
                    # 移植
                    for d in drawings: g_root.append(d)
                    for d in legacy: g_root.append(d)
                    g_tree.write(gen_xml, encoding="UTF-8", xml_declaration=True)

    # 4. Content_Types.xml のマージ
    # 生成されたファイルの [Content_Types].xml をベースにし、画像関連の Override/Default を追加する
    orig_ct_path = os.path.join(temp_orig, "[Content_Types].xml")
    gen_ct_path = os.path.join(temp_gen, "[Content_Types].xml")
    
    if os.path.exists(orig_ct_path) and os.path.exists(gen_ct_path):
        o_ct_tree = etree.parse(orig_ct_path)
        g_ct_tree = etree.parse(gen_ct_path)
        g_ct_root = g_ct_tree.getroot()
        ct_ns = {"ct": "http://schemas.openxmlformats.org/package/2006/content-types"}
        
        # オリジナルにある drawings や vml の定義を、生成ファイル側になければ追加
        for item in o_ct_tree.xpath("//ct:Override", namespaces=ct_ns):
            part = item.get("PartName")
            if "drawings" in part or "vmlDrawing" in part:
                if not g_ct_root.xpath(f'//ct:Override[@PartName="{part}"]', namespaces=ct_ns):
                    g_ct_root.append(item)
        
        for item in o_ct_tree.xpath("//ct:Default", namespaces=ct_ns):
            ext = item.get("Extension")
            if ext in ["vml", "wmf", "png", "jpg", "jpeg", "rels"]:
                if not g_ct_root.xpath(f'//ct:Default[@Extension="{ext}"]', namespaces=ct_ns):
                    g_ct_root.append(item)
        
        g_ct_tree.write(gen_ct_path, encoding="UTF-8", xml_declaration=True)

    # ZIP再圧縮
    with zipfile.ZipFile(final_xlsx, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(temp_gen):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, temp_gen)
                z.write(full, rel)

    shutil.rmtree(temp_orig)
    shutil.rmtree(temp_gen)
    print(f"完了: {final_xlsx}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3:
        inject_images(sys.argv[1], sys.argv[2], sys.argv[3])

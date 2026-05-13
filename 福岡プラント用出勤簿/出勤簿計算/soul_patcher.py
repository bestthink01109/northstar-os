import zipfile
import shutil
import os
from lxml import etree

def soul_patch(original_xlsx, temp_xlsx, output_xlsx):
    """
    original_xlsx の画像やレイアウト（XML構造全体）を維持しつつ、
    temp_xlsx (openpyxlで生成したもの) からシート内容だけを「移植」する。
    特に、openpyxlが削除してしまう <drawing> タグをオリジナルのものと差し替える。
    """
    print(f"魂のパッチを開始: {original_xlsx} -> {output_xlsx}")
    
    temp_orig = "temp_orig_soul"
    temp_new = "temp_new_soul"
    for d in [temp_orig, temp_new]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)

    with zipfile.ZipFile(original_xlsx, 'r') as z: z.extractall(temp_orig)
    with zipfile.ZipFile(temp_xlsx, 'r') as z: z.extractall(temp_new)

    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    # xl/worksheets/ 内の各 sheetN.xml を処理
    ws_dir = os.path.join(temp_orig, "xl", "worksheets")
    for file in os.listdir(ws_dir):
        if not file.endswith(".xml") or file.startswith("_"): continue
        
        orig_path = os.path.join(ws_dir, file)
        new_path = os.path.join(temp_new, "xl", "worksheets", file)
        
        # 実績シートは構造が大きく変わっているため、丸ごと差し替える（画像はない前提）
        # それ以外のシート（個人用など）は、デザインと画像を保護するため外科手術パッチを行う
        is_jisseki = (file == "sheet1.xml") # 実績が sheet1.xml である前提

        if is_jisseki:
            print(f"  Replacing {file} (Jisseki structure update)...")
            shutil.copy2(new_path, orig_path)
        else:
            print(f"  Surgically patching {file} (Employee sheet)...")
            # オリジナルと新（openpyxl製）の両方をパース
            orig_tree = etree.parse(orig_path)
            new_tree = etree.parse(new_path)
            
            orig_root = orig_tree.getroot()
            new_root = new_tree.getroot()

            # 新しいシートから全セル(<c>)を取得してオリジナルへ反映
            for new_c in new_root.xpath("//main:c", namespaces=ns):
                cell_ref = new_c.get("r")
                orig_c_list = orig_root.xpath(f'//main:c[@r="{cell_ref}"]', namespaces=ns)
                
                if orig_c_list:
                    orig_c = orig_c_list[0]
                    # 数式 <f> を同期
                    new_f = new_c.find("main:f", namespaces=ns)
                    if new_f is not None:
                        orig_f = orig_c.find("main:f", namespaces=ns)
                        if orig_f is None:
                            orig_v = orig_c.find("main:v", namespaces=ns)
                            orig_f = etree.Element("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}f")
                            if orig_v is not None:
                                orig_c.insert(orig_c.index(orig_v), orig_f)
                            else:
                                orig_c.append(orig_f)
                        
                        # 重要：共有数式(shared)などの属性があると、個別の数式書き換えと矛盾してエラーになるためクリア
                        orig_f.attrib.clear()
                        orig_f.text = new_f.text
                        orig_v = orig_c.find("main:v", namespaces=ns)
                        if orig_v is not None: orig_v.text = ""

            # 保存
            orig_tree.write(orig_path, encoding="UTF-8", xml_declaration=True)

    # 5. calcChain.xml の削除
    calc_chain = os.path.join(temp_orig, "xl", "calcChain.xml")
    if os.path.exists(calc_chain):
        os.remove(calc_chain)

    # ZIPに固め直す (temp_orig の構造をそのまま使用)
    with zipfile.ZipFile(output_xlsx, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(temp_orig):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, temp_orig)
                z.write(full, rel)

    shutil.rmtree(temp_orig)
    shutil.rmtree(temp_new)
    print(f"パッチ完了: {output_xlsx}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3:
        soul_patch(sys.argv[1], sys.argv[2], sys.argv[3])

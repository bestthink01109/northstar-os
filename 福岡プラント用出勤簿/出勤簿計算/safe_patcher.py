import zipfile
import os
import shutil
from lxml import etree

def patch_xlsx_formulas(source_xlsx, target_xlsx, sheet_name_to_id, cell_updates):
    """
    ExcelファイルをZIPとして扱い、特定のセルの数式(f)と値(v)だけをXMLレベルで書き換える。
    これにより、openpyxlで消失するWMF画像やデザインを完全に保持する。
    """
    temp_dir = "temp_xml_patch"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    with zipfile.ZipFile(source_xlsx, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # 各シートのXMLを更新
    for sheet_name, updates in cell_updates.items():
        sheet_id = sheet_name_to_id.get(sheet_name)
        if not sheet_id:
            continue
        
        xml_path = os.path.join(temp_dir, "xl", "worksheets", f"sheet{sheet_id}.xml")
        if not os.path.exists(xml_path):
            continue

        print(f"  Patching sheet: {sheet_name} (sheet{sheet_id}.xml)")
        
        # XMLのパース (Namespaceを維持)
        parser = etree.XMLParser(remove_blank_text=False)
        tree = etree.parse(xml_path, parser)
        root = tree.getroot()
        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

        for cell_ref, (formula, value) in updates.items():
            # <c r="C38"> などのセルを探す
            cells = root.xpath(f'//main:c[@r="{cell_ref}"]', namespaces=ns)
            if cells:
                c_node = cells[0]
                # 数式 <f> を更新
                f_node = c_node.find("main:f", namespaces=ns)
                if f_node is None:
                    # <v>がある場合はその前に挿入
                    v_node = c_node.find("main:v", namespaces=ns)
                    f_node = etree.Element("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}f")
                    if v_node is not None:
                        c_node.insert(c_node.index(v_node), f_node)
                    else:
                        c_node.append(f_node)
                f_node.text = formula
                
                # 値 <v> をクリア（Excelに再計算させるため）
                v_node = c_node.find("main:v", namespaces=ns)
                if v_node is not None:
                    v_node.text = "" # 念のため空に
            else:
                print(f"    Warning: Cell {cell_ref} not found in {sheet_name}")

    # ZIPに固め直す
    with zipfile.ZipFile(target_xlsx, 'w', zipfile.ZIP_DEFLATED) as zip_out:
        for root_dir, dirs, files in os.walk(temp_dir):
            for file in files:
                full_path = os.path.join(root_dir, file)
                rel_path = os.path.relpath(full_path, temp_dir)
                zip_out.write(full_path, rel_path)

    shutil.rmtree(temp_dir)
    print(f"Done! Patched file saved as: {target_xlsx}")

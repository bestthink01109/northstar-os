import zipfile
import os
import shutil
import re

def get_sheet_map(xlsx_path):
    sheet_map = {}
    temp_dir = f"temp_map_{os.path.basename(xlsx_path)}"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    try:
        with zipfile.ZipFile(xlsx_path, 'r') as z:
            z.extract("xl/workbook.xml", temp_dir)
            z.extract("xl/_rels/workbook.xml.rels", temp_dir)
            with open(os.path.join(temp_dir, "xl/workbook.xml"), 'r', encoding='utf-8') as f:
                wb_content = f.read()
            with open(os.path.join(temp_dir, "xl/_rels/workbook.xml.rels"), 'r', encoding='utf-8') as f:
                rel_content = f.read()
            sheet_matches = re.findall(r'<sheet [^>]*name="([^"]*)" [^>]*r:id="([^"]*)"', wb_content)
            rel_matches = re.findall(r'<Relationship [^>]*Id="([^"]*)" [^>]*Target="worksheets/([^"]*)"', rel_content)
            id_to_file = {r_id: f_name for r_id, f_name in rel_matches}
            for name, r_id in sheet_matches:
                f_name = id_to_file.get(r_id)
                if f_name: sheet_map[name] = f_name
    finally:
        shutil.rmtree(temp_dir)
    return sheet_map

def surgical_regex_patch(original_xlsx, generated_xlsx, final_xlsx):
    print(f"超精密パッチ開始: {original_xlsx} -> {final_xlsx}")
    orig_map = get_sheet_map(original_xlsx)
    gen_map = get_sheet_map(generated_xlsx)
    temp_orig, temp_gen = "temp_orig_regex", "temp_gen_regex"
    for d in [temp_orig, temp_gen]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)
    with zipfile.ZipFile(original_xlsx, 'r') as z: z.extractall(temp_orig)
    with zipfile.ZipFile(generated_xlsx, 'r') as z: z.extractall(temp_gen)

    template_drawings, template_legacies, template_rels = [], [], None
    for name, orig_file in orig_map.items():
        orig_xml_path = os.path.join(temp_orig, "xl/worksheets", orig_file)
        with open(orig_xml_path, 'r', encoding='utf-8') as f: content = f.read()
        ds = re.findall(r'<drawing [^>]*/>|<drawing [^>]*>.*?</drawing>', content, re.DOTALL)
        ls = re.findall(r'<legacyDrawing [^>]*/>|<legacyDrawing [^>]*>.*?</legacyDrawing>', content, re.DOTALL)
        if ds or ls:
            template_drawings, template_legacies = ds, ls
            orig_rel_file = os.path.join(temp_orig, "xl/worksheets/_rels", f"{orig_file}.rels")
            if os.path.exists(orig_rel_file):
                with open(orig_rel_file, 'r', encoding='utf-8') as f: template_rels = f.read()
            print(f"  Template for images identified: {name}")
            break

    for name, gen_file in gen_map.items():
        gen_xml_path = os.path.join(temp_gen, "xl/worksheets", gen_file)
        if not os.path.exists(gen_xml_path): continue
        print(f"  Processing sheet: {name}")
        with open(gen_xml_path, 'r', encoding='utf-8') as f: gen_xml = f.read()

        if name in orig_map:
            orig_file = orig_map[name]
            orig_xml_path = os.path.join(temp_orig, "xl/worksheets", orig_file)
            with open(orig_xml_path, 'r', encoding='utf-8') as f: orig_xml = f.read()
            gen_cells = re.findall(r'<c r="([A-Z0-9]+)"[^>]*>(.*?)</c>|<c r="([A-Z0-9]+)"[^/>]*/\s*>', gen_xml, re.DOTALL)
            for match in gen_cells:
                r_ref, new_content = match[0] or match[2], match[1] or ""
                cell_pattern = rf'(<c r="{r_ref}"[^>]*>)(.*?)(</c>)|(<c r="{r_ref}"[^/>]*/\s*>)'
                def replace_cell(m):
                    if m.group(4):
                        return f'{m.group(4).replace("/>", ">")}{new_content}</c>' if new_content else m.group(4)
                    return f'{m.group(1)}{new_content}{m.group(3)}'
                orig_xml = re.sub(cell_pattern, replace_cell, orig_xml, flags=re.DOTALL)
            with open(gen_xml_path, 'w', encoding='utf-8') as f: f.write(orig_xml)
            orig_rel_file = os.path.join(temp_orig, "xl/worksheets/_rels", f"{orig_file}.rels")
            if os.path.exists(orig_rel_file):
                gen_rel_dir = os.path.join(temp_gen, "xl/worksheets/_rels")
                if not os.path.exists(gen_rel_dir): os.makedirs(gen_rel_dir)
                shutil.copy2(orig_rel_file, os.path.join(gen_rel_dir, f"{gen_file}.rels"))
        else:
            print(f"    New sheet detected. Injecting template images.")
            if template_drawings or template_legacies:
                if 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"' not in gen_xml:
                    gen_xml = gen_xml.replace('<worksheet', '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"', 1)
                gen_xml = re.sub(r'<drawing [^>]*/>|<drawing [^>]*>.*?</drawing>', '', gen_xml, flags=re.DOTALL)
                gen_xml = re.sub(r'<legacyDrawing [^>]*/>|<legacyDrawing [^>]*>.*?</legacyDrawing>', '', gen_xml, flags=re.DOTALL)
                insert_pos = gen_xml.rfind('</worksheet>')
                gen_xml = gen_xml[:insert_pos] + "".join(template_drawings) + "".join(template_legacies) + gen_xml[insert_pos:]
                with open(gen_xml_path, 'w', encoding='utf-8') as f: f.write(gen_xml)
                if template_rels:
                    gen_rel_dir = os.path.join(temp_gen, "xl/worksheets/_rels")
                    if not os.path.exists(gen_rel_dir): os.makedirs(gen_rel_dir)
                    with open(os.path.join(gen_rel_dir, f"{gen_file}.rels"), 'w', encoding='utf-8') as f: f.write(template_rels)

    for folder in ["xl/drawings", "xl/media"]:
        src, dst = os.path.join(temp_orig, folder), os.path.join(temp_gen, folder)
        if os.path.exists(src):
            if os.path.exists(dst): shutil.rmtree(dst)
            shutil.copytree(src, dst)
    cc = os.path.join(temp_gen, "xl/calcChain.xml")
    if os.path.exists(cc): os.remove(cc)
    with zipfile.ZipFile(final_xlsx, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(temp_gen):
            for f in files:
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, temp_gen))
    shutil.rmtree(temp_orig)
    shutil.rmtree(temp_gen)
    print(f"パッチ完了: {final_xlsx}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3: surgical_regex_patch(sys.argv[1], sys.argv[2], sys.argv[3])

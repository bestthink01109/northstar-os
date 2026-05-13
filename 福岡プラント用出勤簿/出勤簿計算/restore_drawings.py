import zipfile
import shutil
import os

def restore_drawings(original_xlsx, output_xlsx):
    """
    original_xlsx から画像関連のフォルダと定義(rels)を抽出し、
    output_xlsx (openpyxl等で生成され画像が消えたファイル) へ書き戻す。
    """
    temp_orig = "temp_orig_zip"
    temp_out = "temp_out_zip"
    
    for d in [temp_orig, temp_out]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)

    with zipfile.ZipFile(original_xlsx, 'r') as z:
        z.extractall(temp_orig)
    with zipfile.ZipFile(output_xlsx, 'r') as z:
        z.extractall(temp_out)

    # 1. 画像データと描画定義をコピー
    for folder in ["xl/drawings", "xl/media"]:
        src = os.path.join(temp_orig, folder)
        dst = os.path.join(temp_out, folder)
        if os.path.exists(src):
            if os.path.exists(dst): shutil.rmtree(dst)
            shutil.copytree(src, dst)
    
    # 2. VML（コメントや古い画像形式）のコピー
    for file in os.listdir(os.path.join(temp_orig, "xl")):
        if file.startswith("vmlDrawing") or file.endswith(".vml"):
            shutil.copy2(os.path.join(temp_orig, "xl", file), os.path.join(temp_out, "xl", file))

    # 3. ワークシートと図面の紐付け(rels)を復元
    src_rels_dir = os.path.join(temp_orig, "xl/worksheets/_rels")
    dst_rels_dir = os.path.join(temp_out, "xl/worksheets/_rels")
    if os.path.exists(src_rels_dir):
        if not os.path.exists(dst_rels_dir): os.makedirs(dst_rels_dir)
        for rel_file in os.listdir(src_rels_dir):
            shutil.copy2(os.path.join(src_rels_dir, rel_file), os.path.join(dst_rels_dir, rel_file))

    # 4. コンテンツタイプ（画像が含まれることを宣言）を復元
    # ※ 本来はマージが必要だが、構造が変わっていなければオリジナルを優先
    shutil.copy2(os.path.join(temp_orig, "[Content_Types].xml"), os.path.join(temp_out, "[Content_Types].xml"))

    # ZIPに固め直す
    final_xlsx = output_xlsx.replace(".xlsx", "_復元済.xlsx")
    with zipfile.ZipFile(final_xlsx, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(temp_out):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, temp_out)
                z.write(full, rel)

    shutil.rmtree(temp_orig)
    shutil.rmtree(temp_out)
    print(f"画像復元完了: {final_xlsx}")
    return final_xlsx

if __name__ == "__main__":
    restore_drawings("【出勤簿】202604_old.xlsx", "【出勤簿】202604_計算式適用済.xlsx")

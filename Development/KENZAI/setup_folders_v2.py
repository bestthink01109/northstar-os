import os

def create_folders():
    base_dir = os.path.expanduser("~/Library/CloudStorage/GoogleDrive-bestthink01109@gmail.com/マイドライブ")
    
    # 新しい親フォルダと子フォルダ
    kenzai_dir = os.path.join(base_dir, "🏢【KENZAI】給与計算")
    input_dir = os.path.join(kenzai_dir, "📥 01_ここに入力データをポン（生データ用）")
    output_dir = os.path.join(kenzai_dir, "📤 02_ここから完成品を取る（出力用）")
    
    folders = [
        kenzai_dir,
        input_dir,
        output_dir,
        os.path.join(input_dir, "平野工業"),
        os.path.join(input_dir, "福岡プラント機工"),
        os.path.join(input_dir, "純青"),
        os.path.join(output_dir, "平野工業"),
        os.path.join(output_dir, "福岡プラント機工"),
        os.path.join(output_dir, "純青"),
    ]
    
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"作成成功: {folder}")
        except Exception as e:
            print(f"エラー: {folder} - {e}")

if __name__ == "__main__":
    create_folders()

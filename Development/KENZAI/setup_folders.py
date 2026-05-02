import os

def create_folders():
    base_dir = os.path.expanduser("~/Library/CloudStorage/GoogleDrive-bestthink01109@gmail.com/マイドライブ")
    
    folders = [
        os.path.join(base_dir, "平野工業"),
        os.path.join(base_dir, "福岡プラント機工"),
        os.path.join(base_dir, "純青"),
        os.path.join(base_dir, "Development", "平野工業"),
        os.path.join(base_dir, "Development", "福岡プラント機工"),
        os.path.join(base_dir, "Development", "純青"),
    ]
    
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"作成成功: {folder}")
        except Exception as e:
            print(f"エラー: {folder} - {e}")

if __name__ == "__main__":
    create_folders()

import os
import glob
import csv
import json
import time
import subprocess
import datetime
import unicodedata
import urllib.parse

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
except ImportError:
    print("エラー: 必要なライブラリがインストールされていません。")
    print("ターミナルで以下のコマンドを実行してください:")
    print("pip install google-generativeai python-dotenv")
    exit(1)

# .envファイルから環境変数を読み込む
load_dotenv()

# ==========================================
# 1. 設定周り
# ==========================================
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY or API_KEY == "ここにAPIキーを貼り付けてください":
    print("エラー: .env ファイルに Gemini API キーが設定されていません。")
    exit(1)

genai.configure(api_key=API_KEY)

# 精度が高く安定している 1.5 Pro を使用
# JSON形式での出力を厳密に要求します
model = genai.GenerativeModel(
    'gemini-1.5-pro-latest',
    generation_config={"response_mime_type": "application/json"}
)

INPUT_DIR = "タイムカードスクショ/処理前"
OUTPUT_DIR = "202603CSV"   # 必要に応じて変更可能
MASTER_CSV = "社員マスター.csv"

# ==========================================
# 2. マスター読み込み
# ==========================================
def load_master():
    master_data = {}
    if not os.path.exists(MASTER_CSV):
        print(f"警告: マスターファイル {MASTER_CSV} が見つかりません。")
        return master_data
        
    # encodingの自動判定（Windowsの文字化け対策）
    try:
        f = open(MASTER_CSV, 'r', encoding='cp932')
        reader = list(csv.DictReader(f))
    except UnicodeDecodeError:
        f = open(MASTER_CSV, 'r', encoding='utf-8-sig')
        reader = list(csv.DictReader(f))
        
    for row in reader:
        name = unicodedata.normalize('NFC', row.get('氏名', '').strip().replace(' ', '').replace('　', ''))
        if not name:
            continue
        master_data[name] = {
            'code': row.get('社員コード', ''),
            'category': row.get('社員/パート', ''),
            'teiji': row.get('定時時間', ''),
            'yukyu_time': row.get('有給付与時間', '')
        }
    f.close()
    return master_data

# ==========================================
# 3. 画像変換 (Mac専用 sips コマンド利用)
# ==========================================
def convert_heic_to_jpg(heic_path):
    """Macのsipsコマンドを使ってHEICを一時JPGに変換(爆速です)"""
    jpg_path = heic_path.rsplit('.', 1)[0] + "_temp.jpg"
    try:
        subprocess.run(["sips", "-s", "format", "jpeg", heic_path, "--out", jpg_path], check=True, capture_output=True)
        return jpg_path
    except Exception as e:
        print(f"画像変換エラー ({heic_path}): {e}")
        return None

def upload_to_gemini(path):
    print(f"      -> 画像をAIに送信中: {os.path.basename(path)}...")
    file = genai.upload_file(path)
    return file

# ==========================================
# 4. AI(Gemini)によるOCR抽出
# ==========================================
def extract_timecard_data(gemini_files):
    prompt_text = """
    あなたはプロの文字起こしAIです。提供された画像（タイムカードの前半・後半）から、出退勤データを抽出してください。
    出力は必ず以下の形式のJSON配列のみを返してください。
    
    [
      {"day": 1, "in": "08:15", "out": "17:30", "paid_leave": false, "absence": false},
      {"day": 2, "in": "", "out": "", "paid_leave": true, "absence": false}
    ]
    
    ルール:
    - 画像の中の「日付」ごとの出勤時間と退出時間（HH:MM形式）を抽出。
    - 何も打刻が無く、特記事項も無い日はJSON配列に含めないでください。
    - 手書きで「有給」「休」の記載や、有給スタンプがある日は `paid_leave: true` にしてください。
    - 手書きで「欠勤」の記載がある日は `absence: true` にしてください。
    - 手書き文字が枠外にはみ出ている場合でも、その行の日付のものとして扱ってください。
    """
    
    try:
        response = model.generate_content(gemini_files + [prompt_text])
        data = json.loads(response.text)
        return data
    except Exception as e:
        print(f"      [エラー詳細] プロンプト送信・解析中にエラー: {e}")
        return []

# ==========================================
# 5. ALIGN FIRST ルールエンジン適用
# ==========================================
def apply_business_rules(raw_data, employee_info, year, month):
    """
    定時丸め、水日休みの欠勤判定、有給処理を適用する
    """
    processed = {}
    
    # JSONの配列を辞書に変換
    for row in raw_data:
        day = row.get('day')
        if not day: continue
        try:
            day = int(day)
        except:
            continue
            
        processed[day] = {
            'shukkin': row.get('in', '').replace('：', ':'),
            'taikin': row.get('out', '').replace('：', ':'),
            'yukyu': '1' if row.get('paid_leave') else '',
            'kekkin': '1' if row.get('absence') else '',
            'yukyu_jikan': ''
        }
        
    teiji_str = employee_info.get('teiji', '')
    is_shain = (employee_info.get('category') == '社員')
    master_yukyu_time = employee_info.get('yukyu_time', '')
    
    # 月の最終日を取得
    if month == 12:
        last_day = 31
    else:
        last_day = (datetime.date(year, month+1, 1) - datetime.timedelta(days=1)).day
    
    # 定時時間の計算用パース
    teiji_minutes = None
    if teiji_str and ':' in teiji_str:
        h, m = map(int, teiji_str.split(':'))
        teiji_minutes = h * 60 + m

    final_rows = []
    
    for day in range(1, last_day + 1):
        dt = datetime.date(year, month, day)
        is_wed_or_sun = dt.weekday() in (2, 6) # 2=水曜, 6=日曜
        
        row = processed.get(day, {'shukkin': '', 'taikin': '', 'yukyu': '', 'kekkin': '', 'yukyu_jikan': ''})
        
        # --- ルール①: 有給処理 ---
        if row['yukyu']:
            if not is_shain and master_yukyu_time:
                # パートの場合、マスターから有給時間を引っ張ってくる
                row['yukyu_jikan'] = master_yukyu_time
            # 有給の日は出退勤の時間を消す（給与らくだ仕様）
            row['shukkin'] = ''
            row['taikin'] = ''
            
        # --- ルール②: 定時丸め処理 ---
        elif row['shukkin'] and teiji_minutes is not None:
            try:
                shukkin_h, shukkin_m = map(int, row['shukkin'].split(':'))
                act_minutes = shukkin_h * 60 + shukkin_m
                if act_minutes < teiji_minutes:
                    # 定時より前に打刻していれば、定時時間に丸める
                    row['shukkin'] = teiji_str
            except:
                pass
                
        # --- ルール③: 欠勤判定（社員・水日以外で出勤なし・有給なし） ---
        if is_shain and not is_wed_or_sun:
            if not row['shukkin'] and not row['yukyu']:
                # 平日なのに無打刻なら欠勤
                row['kekkin'] = '1'

        final_rows.append({
            '日付': f"{month}月{day}日",
            '出勤時間': row['shukkin'],
            '退出時間': row['taikin'],
            '有給': row['yukyu'],
            '欠勤': row['kekkin'],
            '有給時間': row['yukyu_jikan']
        })
        
    return final_rows

# ==========================================
# メイン処理
# ==========================================
def main():
    print("=" * 60)
    print("給与らくだ タイムカード一括OCR・自動CSV生成システム")
    print("=" * 60)
    
    # フォルダ準備
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    master = load_master()
    if not master:
        print("処理を中断します。")
        return
        
    # 画像一覧の取得と絞り込み
    all_files = glob.glob(os.path.join(INPUT_DIR, "*.*"))
    grouped_images = {}
    
    for fpath in all_files:
        if fpath.lower().endswith(('.heic', '.jpg', '.jpeg', '.png')):
            basename = os.path.basename(fpath).rsplit('.', 1)[0]
            # 正規化 (Mac濁点対策)
            basename = unicodedata.normalize('NFC', basename)
            
            # 「松井美香_前半」のような形式から名前を抽出
            if '_' in basename:
                name = basename.split('_')[0]
                # パート8_松井美香 のような形式の対策
                if name.startswith('社員') or name.startswith('パート'):
                    pass # もしそのままファイル名にするなら抽出ロジックを追加
            else:
                name = basename
                
            # 文字列整形（空白除去など）
            name = name.strip().replace(' ', '').replace('　', '')
            
            # もし「パート8_松井美香」のようにプレフィックスがついている場合名前だけに
            if '_' in name: name = name.split('_')[1]
                
            if name not in grouped_images:
                grouped_images[name] = []
            grouped_images[name].append(fpath)
            
    if not grouped_images:
        print(f"画像が見つかりません。フォルダ '{INPUT_DIR}' を確認してください。")
        return
        
    print(f"{len(grouped_images)}名分のタイムカード処理を開始します...\n")
    
    for name, files in grouped_images.items():
        print(f"▶ {name} さんの処理を開始...")
        
        # マスターから情報検索
        emp_info = master.get(name)
        if not emp_info:
            # プレフィックス付きで探す（例:社員1_矢吹幸子等で登録されている場合の保険）
            for m_name, m_info in master.items():
                if name in m_name:
                    emp_info = m_info
                    break
        
        if not emp_info:
            print(f"  [警告] 社員マスターに '{name}' の情報が見つかりません。スキップします。")
            continue
            
        print(f"  [属性] コード:{emp_info['code']}, {emp_info['category']}, 定時:{emp_info['teiji']}")
        
        gemini_files = []
        temp_jpgs = []
        
        # 画像変換とアップロード
        for fpath in sorted(files): # 前半・後半が順番になるようにソート
            process_path = fpath
            if fpath.lower().endswith('.heic'):
                process_path = convert_heic_to_jpg(fpath)
                if process_path: temp_jpgs.append(process_path)
            
            if process_path:
                g_file = upload_to_gemini(process_path)
                gemini_files.append(g_file)
                time.sleep(1) # API制限回避
                
        # AIで読み取り
        print(f"  [AI] 文字読み取り・JSON抽出中...")
        time.sleep(5)  # API制限(Rate Limit 429)回避のため5秒待機
        raw_data = extract_timecard_data(gemini_files)
        
        # ルール適用
        final_csv_data = apply_business_rules(raw_data, emp_info, 2026, 3)
        
        # CSV出力
        csv_filename = f"{emp_info['code']}_{name}.csv"
        csv_path = os.path.join(OUTPUT_DIR, csv_filename)
        
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['日付', '出勤時間', '退出時間', '有給', '欠勤', '有給時間'])
            writer.writeheader()
            writer.writerows(final_csv_data)
            
        print(f"  [完了] {csv_path} を出力しました！\n")
        
        # 一時ファイルの削除
        for g_file in gemini_files:
            genai.delete_file(g_file.name)
        for t_jpg in temp_jpgs:
            if os.path.exists(t_jpg):
                os.remove(t_jpg)
                
    print("=" * 60)
    print("すべての処理が完了しました！")
    print(f"出力先: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()

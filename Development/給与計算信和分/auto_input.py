"""
給与らくだ タイムカード全自動入力スクリプト（完全版）
======================================================

機能:
- 給与明細書一覧から全従業員を順番に処理
- 従業員ごとに設定変更（勤怠パターン・遅刻早退・休憩時間）を自動適用
- 座標クリック方式で高速データ入力
- チェックボックスの現在状態をピクセル色で判定
- 明細書き込み・更新まで全自動

フロー:
  一覧「開く」→ 明細「勤怠」→ 設定変更 → データ入力
  → 「明細へ書き込み」→ 「更新」→ 「閉じる」→ 次の人

使い方:
1. 給与らくだの給与明細書一覧画面を開く
2. コマンドプロンプトで実行:
   python auto_input.py データフォルダ名

例:
   python auto_input.py 202603

データフォルダ内に従業員名.csvを配置してください。
例: 池田秦幸.csv, 古賀恒好.csv

緊急停止: マウスを画面の左上隅に素早く移動 or Ctrl+C
"""

import pyautogui
import pyperclip
import csv
import sys
import time
import os
import glob
import unicodedata

# pyautoguiの安全設定
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.08

# Escキーで強制停止するためのフラグ
STOP_FLAG = False

def start_escape_listener():
    """Escキーで強制停止するリスナーを開始"""
    global STOP_FLAG
    try:
        import keyboard
        def on_escape(e):
            global STOP_FLAG
            STOP_FLAG = True
        keyboard.on_press_key('esc', on_escape)
    except ImportError:
        print("  ※ 'keyboard'モジュール未インストール。Escキー停止は無効です。")
        print("    pip install keyboard でインストールできます。")
        print("    緊急停止はマウスを画面左上隅へ移動してください。")

def check_stop():
    """強制停止フラグを確認"""
    if STOP_FLAG:
        print("\n")
        print("!" * 60)
        print("  Escキーが押されました。プログラムを停止します。")
        print("!" * 60)
        sys.exit(0)

# ========================================
# 座標設定
# ========================================
COORDS = {
    # 給与明細書一覧画面
    'list_first_open': (415, 224),
    'list_close': (1861, 953),
    # 給与明細書画面
    'meisai_kintai': (979, 953),
    'meisai_update': (1527, 952),
    'meisai_close': (1857, 951),
    # タイムカード入力画面
    'settings_button': (749, 795),
    'meisai_kakikomi': (759, 952),
    # タイムカード入力画面 - 1行目セル座標
    'row1_shukkin': (193, 177),
    'row1_taikin': (442, 184),
    'row1_memo': (544, 181),
    'row1_yukyu_jikan': (1696, 180),
    'row1_yukyu_check': (1773, 181),
    'row1_kekkin_check': (1829, 182),
    # 設定ダイアログ - パターン
    'pattern_a': (604, 185),
    'pattern_b': (600, 221),
    'pattern_c': (602, 256),
    'pattern_d': (598, 287),
    'pattern_e': (602, 323),
    # 設定ダイアログ - タブ
    'tab_shukei_jikan': (879, 184),
    'tab_hayade_chikoku': (992, 188),
    # 設定ダイアログ - チェックボックス・入力欄
    'chikoku_checkbox': (800, 416),
    'break_start': (820, 638),
    'break_end': (928, 635),
    'ok_button': (1108, 774),
}

ROW_HEIGHT = 41.5    # タイムカード入力画面の1行の高さ
LIST_ROW_HEIGHT = 41.5  # 給与明細書一覧の1行の高さ（計算により完全に一致することが判明）

PATTERN_COORDS = {
    'A': COORDS['pattern_a'],
    'B': COORDS['pattern_b'],
    'C': COORDS['pattern_c'],
    'D': COORDS['pattern_d'],
    'E': COORDS['pattern_e'],
}


# ========================================
# 従業員マスター（給与明細書一覧の表示順）
# ========================================
EMPLOYEE_MASTER = [
    {'index': 0, 'code': '社員1', 'name': '矢吹幸子', 'pattern': 'B', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 1, 'code': '社員2', 'name': '山口拓郎', 'pattern': 'A', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 2, 'code': 'パート3', 'name': '川口紀美子', 'pattern': 'A', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '4:00'},
    {'index': 3, 'code': '社員4', 'name': '松井嘉子', 'pattern': 'A', 'chikoku_on': False, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 4, 'code': '社員3', 'name': '宮崎ひとみ', 'pattern': 'B', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 5, 'code': 'N-001', 'name': 'スレスタスレンドラ', 'pattern': 'C', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 6, 'code': 'N-002', 'name': 'シャヒガガン', 'pattern': 'C', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 7, 'code': '社員6', 'name': '古賀恒好', 'pattern': 'C', 'chikoku_on': False, 'break_time': '12:00-13:00', 'yukyu_jikan': '8:00'},
    {'index': 8, 'code': '社員5', 'name': '永野富士代', 'pattern': 'A', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 9, 'code': '社員7', 'name': '池端龍司', 'pattern': 'C', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 10, 'code': 'パート4', 'name': '小松京子', 'pattern': 'B', 'chikoku_on': False, 'break_time': '12:00-13:00', 'yukyu_jikan': '4:00'},
    {'index': 11, 'code': '', 'name': '松井慶信', 'pattern': 'B', 'chikoku_on': False, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 12, 'code': 'N-003', 'name': 'バンダリミラン', 'pattern': 'C', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 13, 'code': '社員9', 'name': '立石章一', 'pattern': 'E', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 14, 'code': '社員12', 'name': '西田政代', 'pattern': 'B', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 15, 'code': '業務委託-1', 'name': '羽山寿男', 'pattern': 'B', 'chikoku_on': False, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 16, 'code': '社員10', 'name': '森龍翔', 'pattern': 'A', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 17, 'code': '社員14', 'name': '野口明子', 'pattern': 'A', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 18, 'code': '社員8', 'name': '池田泰幸', 'pattern': 'A', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 19, 'code': 'パート8', 'name': '松井美香', 'pattern': 'B', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '3:30'},
    {'index': 20, 'code': 'パート9', 'name': '松井睦', 'pattern': 'B', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '3:30'},
    {'index': 21, 'code': '社員16', 'name': '松井学', 'pattern': 'A', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 22, 'code': '社員15', 'name': '松井美香', 'pattern': 'A', 'chikoku_on': True, 'break_time': '13:00-14:00', 'yukyu_jikan': ''},
    {'index': 23, 'code': '社員17', 'name': '松井健司', 'pattern': 'A', 'chikoku_on': True, 'break_time': '13:00-14:00', 'yukyu_jikan': ''},
    {'index': 24, 'code': 'パート10', 'name': 'プラナクマリ', 'pattern': 'B', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '3:30'},
    {'index': 25, 'code': 'パート12', 'name': '二ノ宮信好', 'pattern': 'A', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '8:00'},
    {'index': 26, 'code': '社員18', 'name': '田島晋一', 'pattern': 'A', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '8:00'},
    {'index': 27, 'code': '社員19', 'name': '上田秀治', 'pattern': 'A', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '8:00'},
]


# ========================================
# ユーティリティ関数
# ========================================
def click(pos, pause=0.3):
    """座標をクリックして少し待つ"""
    check_stop()
    pyautogui.moveTo(pos[0], pos[1], duration=0.2)
    pyautogui.click(pos[0], pos[1])
    time.sleep(pause)


def check_for_error():
    """
    エラーダイアログが表示されていないか確認する。
    画面中央付近にダイアログが出現すると、その背景色がグレーになる。
    また、確認ダイアログのOKボタンが出ている場合も検出する。
    エラー検出時はプログラムを停止する。
    """
    try:
        import pygetwindow as gw
        active = gw.getActiveWindow()
        if active and active.title:
            title = active.title
            # エラーや確認ダイアログが最前面に来ている場合
            if title in ['確認', 'エラー', 'Error', '警告']:
                print("\n")
                print("!" * 60)
                print("  エラーダイアログを検出しました！")
                print(f"  ダイアログタイトル: {title}")
                print("  プログラムを停止します。")
                print("  給与らくだの画面を確認してください。")
                print("!" * 60)
                sys.exit(1)
    except Exception:
        pass


def safe_type_time(time_str):
    """時刻入力後にエラーチェックを行う"""
    type_time(time_str)
    time.sleep(0.15)
    check_for_error()


def safe_type_japanese(text):
    """日本語入力後にエラーチェックを行う"""
    type_japanese(text)
    time.sleep(0.15)
    check_for_error()


def type_time(time_str):
    """時刻をコロンなしで入力する（例: '8:15' → '815'）"""
    if time_str and time_str.strip():
        clean = time_str.strip().replace(':', '')
        pyautogui.typewrite(clean, interval=0.03)
        time.sleep(0.05)


def type_japanese(text):
    """日本語テキストをクリップボード経由で入力する"""
    if text and text.strip():
        pyperclip.copy(text.strip())
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)


def get_row_pos(base_key, row_index):
    """1行目の座標からrow_index行分ずらした座標を返す（row_index: 0始まり）"""
    base = COORDS[base_key]
    return (base[0], int(base[1] + ROW_HEIGHT * row_index))


def get_list_open_pos(employee_index):
    """給与明細書一覧でのN番目の「開く」ボタン座標（employee_index: 0始まり）"""
    base = COORDS['list_first_open']
    return (base[0], base[1] + LIST_ROW_HEIGHT * employee_index)


def is_checkbox_checked(pos):
    """チェックボックスの状態をピクセル色で判定"""
    screenshot = pyautogui.screenshot()
    pixel = screenshot.getpixel((pos[0], pos[1]))
    brightness = (pixel[0] + pixel[1] + pixel[2]) / 3
    return brightness < 128


def set_checkbox(pos, desired_state):
    """チェックボックスを目的の状態に設定（True=ON, False=OFF）"""
    current = is_checkbox_checked(pos)
    if current != desired_state:
        click(pos, pause=0.2)


# ========================================
# 設定変更
# ========================================
def apply_settings(employee):
    """従業員に合わせて設定ダイアログを操作する"""
    pattern = employee.get('pattern', 'A')
    chikoku_on = employee.get('chikoku_on', True)
    break_time = employee.get('break_time', '12:00-13:00')

    # 設定ボタンをクリック
    click(COORDS['settings_button'], pause=0.5)

    # 勤怠パターンを選択
    if pattern in PATTERN_COORDS:
        click(PATTERN_COORDS[pattern], pause=0.3)

    # 早出/遅刻タブ
    click(COORDS['tab_hayade_chikoku'], pause=0.3)

    # 遅刻早退チェックボックス
    set_checkbox(COORDS['chikoku_checkbox'], chikoku_on)
    time.sleep(0.2)

    # 集計時間タブ
    click(COORDS['tab_shukei_jikan'], pause=0.3)

    # 休憩時間設定（ダブルクリックで時間部分を選択して上書き）
    break_parts = break_time.split('-')
    if len(break_parts) == 2:
        # 開始時間の「時」部分をダブルクリックで選択→上書き
        start_hour = break_parts[0].strip().split(':')[0]
        pyautogui.doubleClick(COORDS['break_start'][0], COORDS['break_start'][1])
        time.sleep(0.1)
        pyautogui.typewrite(start_hour, interval=0.03)

        # 終了時間の「時」部分をダブルクリックで選択→上書き
        end_hour = break_parts[1].strip().split(':')[0]
        pyautogui.doubleClick(COORDS['break_end'][0], COORDS['break_end'][1])
        time.sleep(0.1)
        pyautogui.typewrite(end_hour, interval=0.03)

    # OK
    click(COORDS['ok_button'], pause=0.5)


# ========================================
# タイムカードデータ入力（座標クリック方式）
# ========================================
def input_timecard(data, employee, max_day=31):
    """
    座標クリック方式でタイムカードデータを高速入力する。
    画面は13行表示で、Page Downで最下行が先頭に移動する。
    ページ分割: 1-12日(ページ1) → PgDn → 13-24日(ページ2) → PgDn → 25-31日(ページ3)
    """
    master_yukyu_jikan = employee.get('yukyu_jikan', '')

    # ページ定義: (開始日, 終了日)
    pages = [
        (1, 12),
        (13, 24),
        (25, max_day),
    ]

    for page_idx, (page_start, page_end) in enumerate(pages):
        # 2ページ目以降はPage Down
        if page_idx > 0:
            pyautogui.press('pagedown')
            time.sleep(0.3)

        for day in range(page_start, page_end + 1):
            if day > max_day:
                break

            # このページ内での行番号（0始まり）
            row_idx = day - page_start

            if day not in data:
                continue

            d = data[day]
            shukkin = d.get('shukkin', '')
            taikin = d.get('taikin', '')
            yukyu = d.get('yukyu', '')
            yukyu_jikan = d.get('yukyu_jikan', '') or master_yukyu_jikan
            kekkin = d.get('kekkin', '')

            has_work = bool(shukkin and shukkin.strip() and taikin and taikin.strip())
            is_yukyu = bool(yukyu and yukyu.strip() == '1')
            is_kekkin = bool(kekkin and kekkin.strip() == '1')

            if has_work:
                click(get_row_pos('row1_shukkin', row_idx), pause=0.2)
                safe_type_time(shukkin)
                click(get_row_pos('row1_taikin', row_idx), pause=0.2)
                safe_type_time(taikin)
                print(f"    {day}日: {shukkin} - {taikin}")

            elif is_yukyu:
                click(get_row_pos('row1_memo', row_idx), pause=0.2)
                safe_type_japanese('有給')
                if yukyu_jikan and yukyu_jikan.strip():
                    click(get_row_pos('row1_yukyu_jikan', row_idx), pause=0.2)
                    safe_type_time(yukyu_jikan)
                set_checkbox(get_row_pos('row1_yukyu_check', row_idx), True)
                print(f"    {day}日: 有給")

            elif is_kekkin:
                click(get_row_pos('row1_memo', row_idx), pause=0.2)
                safe_type_japanese('欠勤')
                set_checkbox(get_row_pos('row1_kekkin_check', row_idx), True)
                print(f"    {day}日: 欠勤")


# ========================================
# CSV読み込み
# ========================================
def load_csv(filepath):
    """CSVを読み込み、日付をキーにした辞書を返す"""
    data = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            day_str = row.get('日付', '')
            day_num = None
            if '月' in day_str and '日' in day_str:
                try:
                    day_num = int(day_str.split('月')[1].split('日')[0])
                except ValueError:
                    pass
            if day_num is None:
                try:
                    day_num = int(day_str)
                except ValueError:
                    continue
            data[day_num] = {
                'day': day_num,
                'shukkin': row.get('出勤時間', ''),
                'taikin': row.get('退出時間', ''),
                'yukyu': row.get('有給', ''),
                'kekkin': row.get('欠勤', ''),
                'yukyu_jikan': row.get('有給時間', ''),
            }
    return data


# ========================================
# メイン処理
# ========================================
def main():
    if len(sys.argv) < 2:
        print("使い方: python auto_input.py データフォルダ名")
        print("例:     python auto_input.py 202603")
        print()
        print("データフォルダ内にCSVファイルを配置してください。")
        print("CSVファイル名: 社員コード_氏名.csv")
        print("例: 社員8_池田秦幸.csv, 社員6_古賀恒好.csv")
        sys.exit(1)

    data_folder = sys.argv[1]

    if not os.path.isdir(data_folder):
        print(f"エラー: フォルダ '{data_folder}' が見つかりません。")
        sys.exit(1)

    # フォルダ内のCSVを検索し、マスターとマッチング
    csv_files = glob.glob(os.path.join(data_folder, '*.csv'))
    if not csv_files:
        print(f"エラー: フォルダ '{data_folder}' 内にCSVファイルがありません。")
        sys.exit(1)

    tasks = []
    for csv_path in csv_files:
        csv_name = os.path.splitext(os.path.basename(csv_path))[0]
        # Macの濁点・半濁点分離（NFD）をNFCへ正規化
        csv_name = unicodedata.normalize('NFC', csv_name)
        # 「社員コード_氏名」形式からコードと名前を分離
        if '_' in csv_name:
            file_code = csv_name.split('_', 1)[0]
            file_name = csv_name.split('_', 1)[1]
        else:
            file_code = ''
            file_name = csv_name
        matched = None
        for emp in EMPLOYEE_MASTER:
            # コードが一致すれば確定（同姓同名対策）
            if file_code and emp['code'] == file_code:
                matched = emp
                break
            # コードなしの場合は名前で一致
            if not file_code and emp['name'] == file_name:
                matched = emp
                break
        if matched:
            tasks.append({'employee': matched, 'csv_path': csv_path})
        else:
            print(f"警告: '{csv_name}.csv' に対応する従業員がマスターに見つかりません。スキップします。")

    if not tasks:
        print("エラー: 処理対象の従業員がいません。")
        sys.exit(1)

    # indexでソート（一覧の上から順に処理）
    tasks.sort(key=lambda t: t['employee']['index'])

    # 月の日数
    max_day = 31
    print(f"対象月の日数を入力してください（デフォルト: {max_day}）: ", end="")
    user_input = input().strip()
    if user_input:
        try:
            max_day = int(user_input)
        except ValueError:
            pass

    # 処理内容の確認
    print()
    print("=" * 60)
    print("  給与らくだ タイムカード全自動入力")
    print("=" * 60)
    print(f"\n対象月日数: {max_day}日")
    print(f"処理対象: {len(tasks)}名")
    print()
    for t in tasks:
        emp = t['employee']
        data = load_csv(t['csv_path'])
        work_days = sum(1 for d in data.values() if d.get('shukkin'))
        yukyu_days = sum(1 for d in data.values() if d.get('yukyu') == '1')
        kekkin_days = sum(1 for d in data.values() if d.get('kekkin') == '1')
        print(f"  [{emp['index']+1:2d}] {emp['name']}: パターン{emp['pattern']} "
              f"出勤{work_days}日 有給{yukyu_days}日 欠勤{kekkin_days}日 "
              f"遅刻{'ON' if emp['chikoku_on'] else 'OFF'} "
              f"休憩{emp['break_time']}")

    print()
    print("=" * 60)
    print("【重要】以下を確認してください:")
    print("  1. 給与らくだの給与明細書一覧画面が表示されている")
    print("  2. 一覧の先頭が1人目の従業員になっている")
    print("  3. IMEが半角英数モードになっている")
    print("=" * 60)
    print()
    input("準備ができたらEnterを押してください...")
    print()
    print("5秒後に開始します。給与らくだの画面に切り替えてください！")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print("  開始！")

    # Escキーリスナー開始
    start_escape_listener()

    current_list_page = 0  # 現在のリストのページ位置（Page Down回数）を記憶

    # ========================================
    # 全従業員の処理ループ
    # ========================================
    for task_idx, task in enumerate(tasks):
        check_stop()
        emp = task['employee']
        csv_path = task['csv_path']
        emp_index = emp['index']

        print(f"\n{'='*60}")
        print(f"  [{task_idx+1}/{len(tasks)}] {emp['name']} (パターン{emp['pattern']})")
        print(f"{'='*60}")

        data = load_csv(csv_path)
        if not data:
            print("  データなし、スキップ")
            continue

        # Page Downで必要な分だけページ送り（1ページ=14行移動）
        PAGE_STEP = 14
        target_page = emp_index // PAGE_STEP
        visible_index = emp_index - target_page * PAGE_STEP

        # 前の処理からページが変わる場合のみ、差分の回数だけPgDnを押す
        page_diff = target_page - current_list_page
        if page_diff > 0:
            for _ in range(page_diff):
                pyautogui.press('pagedown')
                time.sleep(0.3)
            current_list_page = target_page
        elif page_diff < 0:
            # 今回の仕様上発生しないはずですが念のため
            for _ in range(-page_diff):
                pyautogui.press('pageup')
                time.sleep(0.3)
            current_list_page = target_page

        open_pos = get_list_open_pos(visible_index)

        # 1. 一覧で「開く」
        print(f"  一覧から開く...")
        click(open_pos, pause=0.8)

        # 2. 明細画面で「勤怠」
        print(f"  勤怠画面へ...")
        click(COORDS['meisai_kintai'], pause=0.8)

        # 3. 設定変更
        print(f"  設定: パターン{emp['pattern']} 遅刻{'ON' if emp['chikoku_on'] else 'OFF'} 休憩{emp['break_time']}")
        apply_settings(emp)

        # 4. データ入力
        print(f"  データ入力中...")
        input_timecard(data, emp, max_day)

        # 5. 明細へ書き込み
        print(f"  明細へ書き込み...")
        click(COORDS['meisai_kakikomi'], pause=1.0)
        pyautogui.press('enter')
        time.sleep(0.5)

        # 6. 更新
        print(f"  更新...")
        click(COORDS['meisai_update'], pause=0.8)
        pyautogui.press('enter')
        time.sleep(0.5)

        # 7. 閉じる（一覧に戻る）
        print(f"  閉じる...")
        click(COORDS['meisai_close'], pause=0.8)

        print(f"  --> {emp['name']} 完了！")

    print()
    print("=" * 60)
    print(f"  全{len(tasks)}名の入力が完了しました！")
    print("  給与らくだの画面で内容を確認してください。")
    print("=" * 60)


if __name__ == '__main__':
    main()

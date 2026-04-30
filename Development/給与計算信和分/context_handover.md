# 給与らくだ タイムカード全自動入力プロジェクト - 引き継ぎコンテキスト

## プロジェクト概要

紙のタイムカード（MAX社 ER-Sカード）を撮影 → Claude OCRで読み取り → CSVに変換 → Pythonスクリプト（pyautogui）で「給与らくだ」に全自動入力するシステム。

Windows PCで給与らくだが動作。開発指示はMacのClaude.aiから行う。

---

## 現在の状況と残課題

### 成功していること
- タイムカードOCR読み取り精度は十分
- 1人分のデータ入力（座標クリック方式）は川口紀美子さんで成功済み
- タイムカード入力画面のページング（Page Down）は正常動作（1-12日→13-24日→25-31日）
- 設定ダイアログの操作（パターン選択、休憩時間変更）は動作
- Escキーでの緊急停止機能あり
- エラーダイアログ検出機能あり

### 未解決の課題（次セッションで対応必要）

#### 1. EMPLOYEE_MASTERのindex値が実際の一覧表示順と不一致
給与らくだの給与明細書一覧の実際の表示順（スクリーンショットから確認済み）:

ページ1（上から）:
```
index 0:  社員1    矢吹 幸子
index 1:  社員2    山口 拓郎
index 2:  パート3   川口 紀美子  ← 入力成功済み
index 3:  社員4    松井 嘉子
index 4:  社員3    宮崎 ひとみ
index 5:  N-001   スレスタ スレンドラ
index 6:  N-002   シャヒ ガガン
index 7:  社員6    古賀 恒好
index 8:  社員5    永野 富士代
index 9:  社員7    池端 龍司
index 10: パート4   小松 京子
index 11: （コードなし）松井 慶信
index 12: N-003   バンダリ ミラン
index 13: 社員9    立石 章一
```

ページ2（Page Down後）:
```
index 14: 社員12   西田 政代
index 15: 業務委託-1 葉山 寿男
index 16: パート5   イトウ エルシー ← マスターに未登録（要追加）
index 17: 社員10   森 龍翔
index 18: 社員14   野口 明子
index 19: 社員8    池田 秦幸
index 20: 社員11   武藤 信悟 ← マスターに未登録（要追加）
index 21: パート8   松井 美香（時給）
index 22: パート9   松井 睦
index 23: 社員16   松井 学
index 24: 社員15   松井美香（月給）
index 25: 社員17   松井 健司
index 26: パート10  プラナ クマリ
index 27: パート12  二ノ宮 信好
```

ページ3（Page Down後）:
```
index 28: 社員18   田島 晋一
index 29: 社員19   上田 秀治
```

★ 要確認: イトウエルシー（パート5）と武藤信悟（社員11）の設定情報（パターン、遅刻ON/OFF、休憩時間、有給時間）をBUN社長に聞く必要あり

#### 2. 一覧スクロールのバグ
530行目と533行目で open_pos が2回計算されている:
```python
open_pos = get_list_open_pos(visible_index)  # ← 530行目: Page Down後の正しい位置
# ...
open_pos = get_list_open_pos(emp_index)      # ← 533行目: これが上書きして台無しにしている！
```
533行目を削除すれば修正完了。

#### 3. タイムカード入力画面のページング微調整
現在の設定: ページ1(1-12日), ページ2(13-24日), ページ3(25-31日)
タイムカード入力画面のPage Down仕様: 最終行が先頭に来るオーバーラップ方式
→ 実際に13日が先頭に来るかBUN社長に確認済み。この設定でOK。

#### 4. チェックボックスのピクセル判定
設定ダイアログの遅刻早退チェックボックス:
- チェックあり: 色=(0,0,0) 明るさ=0
- チェックなし: 色=(255,255,255) 明るさ=255
- 座標: (800, 416)
- 判定ロジック: brightness < 128 → これは正常動作する

タイムカード入力画面の有給/欠勤チェックボックス:
- 同じロジックを使用しているが、まだ正式テストされていない
- 座標はget_row_posで動的計算

---

## 座標設定（実測値）

```python
COORDS = {
    # 給与明細書一覧画面
    'list_first_open': (417, 222),   # 実測: 矢吹幸子の「開く」ボタン
    'list_close': (1861, 953),
    # 給与明細書画面
    'meisai_kintai': (979, 953),     # 「勤怠」ボタン
    'meisai_update': (1527, 952),    # 「更新」ボタン
    'meisai_close': (1857, 951),     # 「閉じる」ボタン
    # タイムカード入力画面
    'settings_button': (749, 795),   # 「設定」ボタン
    'meisai_kakikomi': (759, 952),   # 「明細へ書き込み」ボタン
    # タイムカード入力画面 - 1行目セル座標
    'row1_shukkin': (193, 177),      # 出勤時間
    'row1_taikin': (442, 184),       # 退出時間（実測: 9日目 Y=506）
    'row1_memo': (544, 181),         # メモ
    'row1_yukyu_jikan': (1696, 180), # 有給時間
    'row1_yukyu_check': (1773, 181), # 有給チェックボックス
    'row1_kekkin_check': (1829, 182),# 欠勤チェックボックス
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
    'chikoku_checkbox': (800, 416),  # 実測
    'break_start': (820, 638),       # 実測: 休憩開始の「時」部分
    'break_end': (928, 635),         # 実測: 休憩終了の「時」部分
    'ok_button': (1108, 774),
}

ROW_HEIGHT = 41.5     # 実測: 1日目Y=177, 9日目Y=509, (509-177)/8=41.5
LIST_ROW_HEIGHT = 30   # 実測: 矢吹Y=222, ガガンY=432, (432-222)/7=30
```

---

## 処理フロー

### 全体フロー（全従業員一括処理）
```
給与明細書一覧（先頭にスクロール）
  → マウスホイール上方向に大量スクロールで先頭へ
  → Page Downで対象従業員の行まで移動
  → 「開く」クリック
    → 給与明細書画面
      → 「勤怠」クリック
        → タイムカード入力画面
          → 「設定」クリック → パターン選択 → 遅刻早退チェック → 休憩時間変更 → OK
          → データ入力（座標クリック方式、ページング対応）
          → 「明細へ書き込み」クリック（自動で明細書画面に戻る）
        → 「更新」クリック
        → 「閉じる」クリック（一覧に戻る）
  → 次の従業員へ
```

### タイムカード入力画面のページング
- 画面には13行分表示
- Page Downで最終行が先頭に移動（オーバーラップ方式）
- ページ分割: 1-12日(ページ1) → PgDn → 13-24日(ページ2) → PgDn → 25-31日(ページ3)
- 各ページ内でrow_idxが0からリセット

### 設定ダイアログの操作
- 勤怠パターン: 左側のA〜Eをクリック
- 早出/遅刻タブ → 遅刻早退チェックボックスをピクセル判定してON/OFF
- 集計時間タブ → 休憩時間の「時」部分をダブルクリックして上書き（分は常に00なので変更不要）
- OKクリック

### 給与明細書一覧のスクロール
- マウスホイール上方向 scroll(200) で先頭に戻す
- Page Downで1ページ=14行移動（オーバーラップなし）
- index // 14 = Page Down回数、index % 14 = 画面内の行番号

---

## CSVファイル仕様

### ファイル名規則
`社員コード_氏名.csv`
例: 社員8_池田秦幸.csv, パート8_松井美香.csv, 社員15_松井美香.csv

### CSV列構成
```
日付,出勤時間,退出時間,有給,欠勤,有給時間
3月2日,8:30,18:45,,,
3月14日,,,1,,          ← 有給（月給者）
3月14日,,,1,,4:00      ← 有給（時給者・有給時間入力あり）
3月8日,,,,1,           ← 欠勤
```

### 実出勤時間の列（オプション）
CSVに「実出勤時間」列を追加可能。スクリプトは「出勤時間」列のみを入力に使用。
定時より早く出勤した場合は出勤時間に定時を入力し、遅刻の場合は実際の出勤時間を入力する。

---

## 従業員マスター設定

### 各項目の意味
- code: 給与らくだの社員コード（CSVファイル名マッチに使用）
- name: 氏名
- pattern: 勤怠パターン A〜E
- chikoku_on: 遅刻早退を自動的に計算するチェック True=ON/False=OFF
  - 月給フルタイム: ON
  - 時給パート、短時間: OFF
- break_time: 休憩時間設定
  - 通常: 12:00-13:00
  - 午前中パート等: 13:00-14:00（実質休憩なしにする回避策）
- yukyu_jikan: 有給時間（時給者のみ）
  - 空文字: 不要（月給者）
  - '4:00', '8:00', '3:30' 等: 有給取得時にこの時間を有給時間欄に入力

### 勤怠パターンごとの設定（給与らくだ側）
パターンは全従業員共通で設定される（パターンC全体に影響等）。
そのため、各従業員処理前に毎回設定変更を行う。

### 社員の欠勤ルール
社員（月給）の場合、水曜・日曜以外の休みは有給でなければ欠勤扱い。
CSVの欠勤列に1を立てる。

---

## Windows PC環境

- OS: Windows 10 (Version 10.0.26200.8037)
- Python: 3.14.3 (64-bit)
- ユーザー: bestt
- デスクトップパス: C:\Users\bestt\OneDrive\デスクトップ\timecard
- インストール済みパッケージ: pyautogui, pyperclip, Pillow, keyboard
- 給与らくだ: 普及版 (BK-2001)

---

## 現在のスクリプト全文

### auto_input.py

```python
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
    'list_first_open': (417, 222),
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
LIST_ROW_HEIGHT = 30  # 給与明細書一覧の1行の高さ

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
    # ★★★ 要修正: 実際の一覧表示順に合わせてindexを振り直す ★★★
    # ★★★ イトウエルシー（パート5, index16）と武藤信悟（社員11, index20）を追加する ★★★
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
    {'index': 15, 'code': '業務委託-1', 'name': '葉山寿男', 'pattern': 'B', 'chikoku_on': False, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    # index 16: パート5 イトウエルシー ← 要追加（設定情報をBUN社長に確認）
    {'index': 17, 'code': '社員10', 'name': '森龍翔', 'pattern': 'A', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 18, 'code': '社員14', 'name': '野口明子', 'pattern': 'A', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 19, 'code': '社員8', 'name': '池田秦幸', 'pattern': 'A', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    # index 20: 社員11 武藤信悟 ← 要追加（設定情報をBUN社長に確認）
    {'index': 21, 'code': 'パート8', 'name': '松井美香', 'pattern': 'B', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '3:30'},
    {'index': 22, 'code': 'パート9', 'name': '松井睦', 'pattern': 'B', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '3:30'},
    {'index': 23, 'code': '社員16', 'name': '松井学', 'pattern': 'A', 'chikoku_on': True, 'break_time': '12:00-13:00', 'yukyu_jikan': ''},
    {'index': 24, 'code': '社員15', 'name': '松井美香', 'pattern': 'A', 'chikoku_on': True, 'break_time': '13:00-14:00', 'yukyu_jikan': ''},
    {'index': 25, 'code': '社員17', 'name': '松井健司', 'pattern': 'A', 'chikoku_on': True, 'break_time': '13:00-14:00', 'yukyu_jikan': ''},
    {'index': 26, 'code': 'パート10', 'name': 'プラナクマリ', 'pattern': 'B', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '3:30'},
    {'index': 27, 'code': 'パート12', 'name': '二ノ宮信好', 'pattern': 'A', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '8:00'},
    {'index': 28, 'code': '社員18', 'name': '田島晋一', 'pattern': 'A', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '8:00'},
    {'index': 29, 'code': '社員19', 'name': '上田秀治', 'pattern': 'A', 'chikoku_on': False, 'break_time': '13:00-14:00', 'yukyu_jikan': '8:00'},
]


# ========================================
# ユーティリティ関数
# ========================================
def click(pos, pause=0.3):
    """座標をクリックして少し待つ"""
    check_stop()
    pyautogui.click(pos[0], pos[1])
    time.sleep(pause)


def check_for_error():
    """エラーダイアログが表示されていないか確認し、検出時は停止"""
    try:
        import pygetwindow as gw
        active = gw.getActiveWindow()
        if active and active.title:
            title = active.title
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

    click(COORDS['settings_button'], pause=0.5)

    if pattern in PATTERN_COORDS:
        click(PATTERN_COORDS[pattern], pause=0.3)

    click(COORDS['tab_hayade_chikoku'], pause=0.3)

    set_checkbox(COORDS['chikoku_checkbox'], chikoku_on)
    time.sleep(0.2)

    click(COORDS['tab_shukei_jikan'], pause=0.3)

    # 休憩時間設定（ダブルクリックで時間部分を選択して上書き）
    break_parts = break_time.split('-')
    if len(break_parts) == 2:
        start_hour = break_parts[0].strip().split(':')[0]
        pyautogui.doubleClick(COORDS['break_start'][0], COORDS['break_start'][1])
        time.sleep(0.1)
        pyautogui.typewrite(start_hour, interval=0.03)

        end_hour = break_parts[1].strip().split(':')[0]
        pyautogui.doubleClick(COORDS['break_end'][0], COORDS['break_end'][1])
        time.sleep(0.1)
        pyautogui.typewrite(end_hour, interval=0.03)

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

    pages = [
        (1, 12),
        (13, 24),
        (25, max_day),
    ]

    for page_idx, (page_start, page_end) in enumerate(pages):
        if page_idx > 0:
            pyautogui.press('pagedown')
            time.sleep(0.3)

        for day in range(page_start, page_end + 1):
            if day > max_day:
                break

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

    csv_files = glob.glob(os.path.join(data_folder, '*.csv'))
    if not csv_files:
        print(f"エラー: フォルダ '{data_folder}' 内にCSVファイルがありません。")
        sys.exit(1)

    tasks = []
    for csv_path in csv_files:
        csv_name = os.path.splitext(os.path.basename(csv_path))[0]
        if '_' in csv_name:
            file_code = csv_name.split('_', 1)[0]
            file_name = csv_name.split('_', 1)[1]
        else:
            file_code = ''
            file_name = csv_name
        matched = None
        for emp in EMPLOYEE_MASTER:
            if file_code and emp['code'] == file_code:
                matched = emp
                break
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

    tasks.sort(key=lambda t: t['employee']['index'])

    max_day = 31
    print(f"対象月の日数を入力してください（デフォルト: {max_day}）: ", end="")
    user_input = input().strip()
    if user_input:
        try:
            max_day = int(user_input)
        except ValueError:
            pass

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
    print("  2. 一覧が先頭にスクロールされている")
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

    start_escape_listener()

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

        # 0. 一覧を先頭にスクロール
        list_x = COORDS['list_first_open'][0]
        list_y = COORDS['list_first_open'][1] + 100
        pyautogui.moveTo(list_x, list_y)
        time.sleep(0.2)
        pyautogui.scroll(200)
        time.sleep(0.5)

        # Page Downで正確にページ送り（1ページ=14行移動）
        PAGE_STEP = 14
        page_downs = emp_index // PAGE_STEP
        visible_index = emp_index - page_downs * PAGE_STEP

        for i in range(page_downs):
            pyautogui.press('pagedown')
            time.sleep(0.3)

        open_pos = get_list_open_pos(visible_index)

        # ★★★ バグ修正: 以下の行を削除すること ★★★
        # open_pos = get_list_open_pos(emp_index)  # ← これが上書きしてバグの原因

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
```

---

## 生成済みCSVファイル（202603フォルダ内）

### パート3_川口紀美子.csv（入力成功済み）
```
日付,出勤時間,退出時間,有給,欠勤,有給時間
3月2日,8:30,12:32,,,
3月3日,8:30,12:34,,,
3月5日,8:30,12:30,,,
3月6日,8:30,12:31,,,
3月7日,8:30,12:37,,,
3月9日,8:30,12:31,,,
3月10日,8:30,12:30,,,
3月12日,8:30,12:32,,,
3月13日,8:30,12:33,,,
3月14日,,,1,,4:00
3月16日,8:30,12:33,,,
3月17日,8:30,12:34,,,
3月19日,8:30,12:40,,,
3月20日,8:30,12:32,,,
3月21日,8:30,12:33,,,
3月23日,8:30,11:31,,,
3月24日,8:30,12:36,,,
3月26日,8:30,12:31,,,
3月27日,8:30,12:31,,,
3月28日,8:30,12:42,,,
3月30日,8:30,12:31,,,
3月31日,8:30,12:31,,,
```

### 社員12_西田政代.csv
```
日付,出勤時間,退出時間,有給,欠勤,有給時間
3月2日,9:00,17:59,,,
3月3日,10:11,17:49,,,
3月5日,9:00,17:58,,,
3月6日,9:00,18:01,,,
3月7日,9:00,17:59,,,
3月9日,9:19,17:57,,,
3月10日,9:00,18:01,,,
3月12日,9:04,17:50,,,
3月13日,9:00,12:37,,,
3月14日,,,1,,
3月16日,9:00,17:58,,,
3月17日,9:00,18:03,,,
3月19日,9:16,18:10,,,
3月20日,9:00,18:00,,,
3月21日,9:00,18:02,,,
3月23日,9:00,18:05,,,
3月24日,9:00,12:39,,,
3月26日,9:00,17:56,,,
3月27日,9:00,17:57,,,
3月28日,9:00,18:07,,,
3月30日,9:00,18:04,,,
3月31日,9:10,17:28,,,
```

### 社員15_松井美香.csv（社員の松井美香さん、定時8:30）
```
日付,出勤時間,退出時間,有給,欠勤,有給時間
3月2日,8:30,17:34,,,
3月3日,8:30,17:34,,,
3月5日,8:30,12:27,,,
3月6日,8:30,17:31,,,
3月7日,8:30,12:16,,,
3月8日,,,,1,
3月9日,8:30,17:39,,,
3月10日,9:55,17:32,,,
3月12日,8:30,17:31,,,
3月13日,9:55,11:23,,,
3月14日,,,,1,
3月16日,,,,1,
3月17日,8:30,17:34,,,
3月19日,8:30,17:39,,,
3月20日,8:30,17:33,,,
3月21日,,,,1,
3月23日,,,1,,
3月24日,8:30,17:38,,,
3月26日,8:30,17:04,,,
3月27日,,,,1,
3月28日,,,,1,
3月30日,8:30,17:35,,,
3月31日,8:30,12:39,,,
```

### N-002_シャヒガガン.csv（定時8:00）
```
日付,出勤時間,退出時間,有給,欠勤,有給時間
3月2日,8:00,18:39,,,
3月3日,8:00,18:47,,,
3月5日,8:00,17:34,,,
3月6日,8:00,18:17,,,
3月7日,8:00,18:00,,,
3月9日,8:00,18:30,,,
3月10日,8:00,18:09,,,
3月12日,8:00,17:35,,,
3月13日,8:00,18:47,,,
3月14日,8:00,18:06,,,
3月16日,8:00,18:08,,,
3月17日,8:00,18:21,,,
3月19日,8:00,18:01,,,
3月20日,8:00,18:09,,,
3月21日,8:00,18:16,,,
3月23日,8:00,18:47,,,
3月24日,8:00,18:38,,,
3月26日,8:00,18:23,,,
3月27日,8:00,18:35,,,
3月28日,8:00,17:55,,,
3月30日,,,1,,
3月31日,8:00,18:13,,,
```

---

## 次セッションでの作業手順

1. BUN社長にイトウエルシー（パート5）と武藤信悟（社員11）の設定情報を確認
2. EMPLOYEE_MASTERを実際の一覧順に修正（上記の正しいindex値で更新）
3. 533行目のバグ（open_posの二重計算）を修正
4. 3名（シャヒガガン、西田政代、松井美香）でテスト実行
5. 成功したら全従業員分のCSV作成フローを構築

---

## テスト時のチェックポイント

- 一覧が先頭にスクロールされているか
- IMEが半角英数モードか
- 対象従業員のデータがクリアされているか（チェックボックスも含む）
- 座標取得コマンド: `python -c "import pyautogui,time;time.sleep(5);print(pyautogui.position())"`
- ピクセル色確認: `python -c "import pyautogui,time;time.sleep(5);s=pyautogui.screenshot();p=s.getpixel(pyautogui.position());print(f'色={p} 明るさ={(p[0]+p[1]+p[2])/3:.0f}')"`

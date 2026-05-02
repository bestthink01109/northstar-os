# KENZAIシステム 完全引き継ぎコンテキスト書
最終更新: 2026-05-02
作成者: BUN_CEO / Antigravity (Google DeepMind)

---

## 1. システム概要

### 目的
平野工業（株式会社ベストシンク管理）の出勤簿Excelを読み込み、
BUN_CEO定義の労務ルールで残業を計算し、給与ソフト「給与楽だ」用CSVを自動生成する。

### 対象会社（マルチテナント）
| 会社ID | 会社名 | 状態 |
|---|---|---|
| hirano | 平野工業 | 本番稼働中 |
| fukuoka_plant | 福岡工場 | スタブ実装 |
| junsei | 純青 | スタブ実装 |

### プロジェクトパス
```
/Users/fuminariaksse/Desktop/antigravity Folder/company/Development/KENZAI/
```

### Google Driveパス
```
入力: マイドライブ/🏢【KENZAI】給与計算/📥 01_ここに入力データをポン（生データ用）/平野工業/
出力: マイドライブ/🏢【KENZAI】給与計算/📤 02_ここから完成品を取る（出力用）/平野工業/
```

---

## 2. ディレクトリ構成

```
KENZAI/
├── main.py                     # エントリーポイント（CLI）
├── hirano/
│   ├── config.py               # 平野工業設定（所定労働時間・半日定義等）
│   ├── employee_master.py      # 社員マスター（16名）
│   └── corrections.py          # 入力ミス補正値定義（AIなし・直接編集）
├── core/
│   ├── daily_calculator.py     # 日次残業計算
│   ├── weekly_allocator.py     # 週次残業振り分け（重要）
│   ├── monthly_aggregator.py   # 月次集計
│   └── validation.py           # 検証・差異検出
├── parsers/
│   └── excel_parser.py         # 出勤簿Excel読み込み
├── exporters/
│   ├── rakuda_csv.py           # 給与楽だ用CSV出力（21列）
│   ├── diff_report.py          # 差異レポートExcel出力
│   └── excel_clone_exporter.py # 計算済み出勤簿Excel出力
├── fukuoka_plant/              # スタブ
└── junsei/                     # スタブ
```

---

## 3. 入力Excelのフォーマット（平野工業）

ファイル名: `【出勤簿】YYYYMM.xlsx`
シート名: 社員名（例: 池田優紀、松岡颯太 等）

各シートの列構成（行3がヘッダー、行4〜が日次データ）:
```
col2  = 日付（datetime型）
col3  = 曜日
col4  = 工事場所（工場 / 現場 / 欠 / 有給 / 研修 等）
col6  = 現場名
col8  = 客先名
col10 = 出社時間（time型）
col12 = 現場開始時間（time型）
col14 = 現場終了時間（time型）
col16 = 退社時間（time型）
col18 = 勤務時間（数値）
col19 = 残業（数値）
col20 = 所内（法定内残業、数値）
col21 = 休出（数値）
col22 = 欠勤（数値）
col23 = 時間休（数値 or '半日' の文字列）
col24 = 作業内容
```

行番号と日付の対応: `row = day + 3`（4月1日=row4, 4月30日=row33）
集計行: row35（合計）、row37（出勤日数等）

注意: openpyxlでExcelを保存すると数式セルの値が消えるため、
      **Excelファイル本体は絶対に変更してはならない**。

---

## 4. 労務ルール（BUN_CEO定義・最重要）

### 4-1. 所定労働時間
- 平日（月〜金）: 7時間/日（7:00〜17:00の現場 → 実労8h - 休憩1h = 7h）
- 土曜日: 7時間/日（ただし法定内/外の振り分けあり）
- 週の法定労働時間上限: 40時間

### 4-2. 日次残業の計算
- 日次総労働時間 = t_end - t_start
- 日次残業 = 日次総労働時間 - 所定労働時間（7h）
- 休憩は除外済み（入退場時刻から直接計算）

### 4-3. 週次残業の振り分け（weekly_allocator.py の核心ロジック）

週単位（月〜日）で以下の処理を行う:

#### shortage_budget（週次不足枠バケツ）の計算
```
shortage_budget = 40h - Σ(その週の平日・土曜の所定労働時間)
```
不就労日（欠勤・全休有給・時間有給）が発生した場合、
その時間は shortage_budget に算入する（週の法定労働時間上限が減る）。

重要: 時間有給（time_off）も全休・欠勤と同様に shortage_budget に算入する。

#### 平日の残業振り分け（ot_in = 法定内残業）
週の法定外残業（ot_out）が発生する前に、
shortage_budget の範囲内で法定内残業（ot_in）に振り替える。

振り分け順序: 残業時間の多い日優先（同数の場合は後の日優先）

#### 土曜日の振り分け
時間有給（time_off）が含まれる土曜日:
- 時間有給分（shortage_budget で減った分）→ 所定労働時間（7h）まで法定内残業
- それ以外 → 法定外残業
上記を超えた分 → 休日出勤（ot_holiday）

### 4-4. 特殊フラグ
- is_special（平野珠美）: 平野工業オーナー妻。週次振り分けで特別扱いあり
- is_absent: 欠勤（place='欠'）
- is_paid: 有給（place='有給'）
- time_off: 時間有給（col23の数値または'半日'）
- 半日 = 3.5h（config で定義）

---

## 5. 出力仕様

### 給与楽だ CSV（21列固定）
ファイル名: `kintai6_YYYYMM.csv`（修正版: `【修正分】kintai6_YYYYMM.csv`）
エンコーディング: CP932（Shift-JIS）
列構成: 社員コード・勤務時間・残業・法定内残業・遅早など21列

### 差異レポート Excel
ファイル名: `差異レポート_平野工業_YYYYMM.xlsx`（修正版: `【修正分】〜`）
色の意味:
- 赤行: 計算値 ≠ Excel記載値（差異あり）
- 黄行: 要確認アラート（土曜time_off等、現場判断が必要）
- 白行: 差異なし

### 計算済み出勤簿 Excel
ファイル名: `【計算済】【出勤簿】YYYYMM.xlsx`（修正版: `【修正分】【計算済】〜`）

---

## 6. CLI の使い方

```bash
# 通常実行
python3 main.py --company hirano --month 202604

# 修正分実行（ファイル名に【修正分】を先頭付加）
python3 main.py --company hirano --month 202604 --suffix 【修正分】

# 全社一括
python3 main.py --all --month 202604
```

---

## 7. 入力ミス補正の仕組み（corrections.py）

Excelファイルは変更不可のため、パーサー読み取り後の dict に補正値を注入する。

ファイル: `hirano/corrections.py`

```python
CORRECTIONS = {
    202604: {
        '池田優紀': {
            30: {'excel_work': 3.5},   # 時間休3.5hのため7hは誤り
        },
        '松岡颯太': {
            24: {'t_start': 8.0},      # 出社8:00の入力漏れ
        },
        '有村正和': {
            21: {'excel_work': 2.5, 'excel_absence': 4.5},
        },
        '平野珠美': {
            28: {'excel_work': 4.0},   # 勤務4hの入力漏れ
        },
    },
}
```

補正は `apply_corrections(all_sheets, year, month)` で parse 直後に適用。
AIなしでBUN_CEOまたは担当者が直接編集できる。

---

## 8. 月次ルーチン（確定版フロー）

```
① 出勤簿Excel（【出勤簿】YYYYMM.xlsx）を入力フォルダに保存
        ↓
② python3 main.py --company hirano --month YYYYMM
        ↓
③ 差異レポート_平野工業_YYYYMM.xlsx を確認
        ↓
④ 差異レポートに「確定修正値」「理由」列へ直接入力（AIなし）
   ※未実装：現状は corrections.py を直接編集
        ↓
⑤ python3 main.py --company hirano --month YYYYMM --fix 差異レポートパス
   ※未実装：現状は --suffix 【修正分】 で再実行
        ↓
⑥ 【修正分】kintai6_YYYYMM.csv を給与楽だに取込
```

---

## 9. 現在の差異状況（2026年4月分）

### corrections.py で自動補正済み
| 社員 | 日 | 内容 |
|---|---|---|
| 池田優紀 | 30 | excel_work 7→3.5h |
| 松岡颯太 | 24 | t_start 9:00→8:00 |
| 有村正和 | 21 | 勤務1→2.5h、欠勤6→4.5h |
| 平野珠美 | 28 | excel_work 0→4.0h |

### 残存差異（システムが正しい、Excelが誤り）
| 社員 | 差異内容 | 理由 |
|---|---|---|
| 上田力也 | W2 ot_in/ot_out誤分類 | 4/11土曜time_off週のExcel入力誤り |
| 池田・有村・平野 | 集計行の合計値 | Excel集計セルが未修正（計算値は正） |
| 平誠矢・松岡・石井 | 土曜欠勤0.5h | 要確認アラート（黄色） |
| トゥン | Day25 ot_in/ot_out | W4分類誤り（システムが正しい） |

---

## 10. 未実装・将来対応事項

| 項目 | 優先度 | 概要 |
|---|---|---|
| --fix オプション | 高 | 差異レポートから修正値を読み込んで再実行 |
| 差異レポート「確定修正値」「理由」列 | 高 | BUN_CEOが直接入力する修正インターフェース |
| 修正済みExcelへのマーキング | 中 | 修正セル:赤文字+黄背景、シートタブ:黄色 |
| 福岡工場・純青の実装 | 低 | 現状スタブのみ |

---

## 11. 重要な設計上の注意点

1. openpyxlでExcelを保存すると数式セルの計算値が消える → Excelは読み取り専用
2. パーサーがyear/monthを取得できない場合 → CLI引数の値をフォールバックとして使用
3. 時間有給（time_off）は shortage_budget に算入する（欠勤と同様の扱い）
4. 平日残業のot_in振り分けは「残業時間の多い日優先・同数なら後の日優先」の順
5. 修正分ファイル名のプレフィックスは「【修正分】」を先頭に付ける

---

## 12. テスト実行コマンド

```bash
cd "/Users/fuminariaksse/Desktop/antigravity Folder/company/Development/KENZAI"
PYTHONPATH=. python3 main.py --company hirano --month 202604 --suffix 【修正分】
```

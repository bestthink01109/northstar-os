# KENZAI SS UI/UX改修（外販対応）
- layer: 3
- complexity: medium
- type: python

## 背景
現在のKENZAIスプレッドシートはBUN_CEOが手動でハンドリングしている前提の設計。
外販時はクライアントが自分で使うため、入力フォームの見やすさ・出力（出勤簿）の見栄えを改修する必要がある。

## 対象
```
/Users/fuminariaksse/Desktop/antigravity Folder/company/Development/KENZAI/
├── exporters/excel_clone_exporter.py  ← 出勤簿Excel出力
├── exporters/diff_report.py          ← 差異レポート出力
└── exporters/rakuda_csv_exporter.py  ← 給与らくだCSV出力
```

出力先スプレッドシート：
`マイドライブ/🏢【KENZAI】給与計算/📤 02_ここから完成品を取る（出力用）/`

## 実装内容

### 1. 出勤簿（Excel）の見栄え改修

`exporters/excel_clone_exporter.py` の出力レイアウト改善：

**現状の問題：**
- セルの書式が統一されていない
- ヘッダー行が見づらい
- 合計行の強調がない

**改修後：**
- ヘッダー行：背景色（#2E4057）+ 白文字 + 太字
- 勤務日の行：交互に薄い背景色（#F5F5F5）
- 合計行：背景色（#E8F0FE）+ 太字 + 上罫線
- 会社名・社員名・期間を見出しとして大きく表示
- 列幅を自動調整（日付・時刻列は固定幅）
- 会社ロゴ欄（左上に画像プレースホルダー）

### 2. 差異レポートの改修

`exporters/diff_report.py` の改善：

- 差異ありの行：赤背景（既存）
- 確認要の行：黄背景（既存）
- **新：** 差異なしの行は行自体を非表示にするオプション追加
- **新：** サマリー行を先頭に追加（差異件数・要確認件数を一目で確認）
- **新：** 修正後の値を入力するための「確定修正値」列に入力ガイドコメントを追加

### 3. 入力フォームの整備（Googleスプレッドシート用テンプレート）

新規：`exporters/ss_template_generator.py`

クライアント向けスプレッドシートのテンプレートを自動生成する：

```
シート構成：
├── 【入力】出勤データ    ← クライアントが入力するシート
│   ├── 説明コメント付き（各列の入力方法を明記）
│   ├── プルダウン（工事場所：工場/現場/欠/有給等）
│   └── 入力規則（時刻形式・数値のみ等）
├── 会社設定             ← チケット1で追加するシート
├── 【出力】出勤簿       ← 自動生成（閲覧専用）
└── 使い方ガイド        ← 操作マニュアル（1枚）
```

### 4. エラーメッセージの日本語化

現在：英語のエラーメッセージ
改修後：すべて日本語で、原因と対処法を明記

例：
```
変更前：KeyError: 'col10'
変更後：エラー：出社時間のデータが見つかりません（E列が空欄になっていませんか？）
```

## 完了条件
- 出勤簿Excelを開いたとき、プロが作ったような見栄えになっている
- 差異レポートのサマリーで問題点を一目で把握できる
- 入力シートにコメントやプルダウンがあり、初見でも使えるUIになっている
- エラーメッセージがすべて日本語で意味がわかる

## 優先実装順
1. 出勤簿Excelの見栄え改修（最優先）
2. エラーメッセージ日本語化
3. 差異レポート改修
4. 入力フォームテンプレート生成

## Codex引き渡しメモ
- openpyxlのStyleオブジェクトを使って書式を適用すること
- Excelファイル本体は変更不可ルールを引き続き守ること（出力ファイルのみ改修対象）
- テストは実際の202604データで見た目を確認すること

## Codex処理ログ
エラー: 2026-05-18 11:15:25
Error loading config.toml: unknown variant `auto-edit`, expected one of `untrusted`, `on-failure`, `on-request`, `granular`, `never`
in `approval_policy`

## Codex処理ログ
エラー: 2026-05-18 16:22:26
Error loading config.toml: unknown variant `auto-edit`, expected one of `untrusted`, `on-failure`, `on-request`, `granular`, `never`
in `approval_policy`

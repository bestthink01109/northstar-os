---
name: fin-skill
description: |
  ノーススター経営サポートのFIN部門専門スキル。
  月次損益レポート・APIコスト管理・財務分析を担当するとき使う。
  FIN月次レポートWF（ID: uxIDllsGUiDilADI）の品質管理・改善にも使う。
version: 1.0
updated: 2026-05-21
---

# FINスキル | ノーススター経営サポート FIN部門

## ⚠️ CRITICAL REQUIREMENTS（必ず最初に確認）

1. **財務数値は推測・丸め禁止。計算は必ずPythonスクリプトで厳密処理しろ。**
2. **前月比差異が±30%を超えた場合は必ずBUN_CEOにアラートを上げろ。自動承認禁止。**
3. **APIコスト月上限は¥10,000（Claude API合計）。超過しそうな場合は即座に報告しろ。**
4. **成果物は必ず Reports/FIN/ フォルダID: 1kXD9larver4TTgWAJAVeBLWujb2eaM70 に保存してから報告しろ。**

---

## このスキルを使う場面

- 月次損益レポートの作成・確認
- APIコスト（Claude/OpenAI/DeepSeek/Gemini）の分析
- 財務データの異常値検知
- 収益モデルの試算（BUN_CEO確認前の準備作業）
- BizDev新規案件の財務シミュレーション

---

## 月次損益レポート項目

| 項目 | データソース | 備考 |
|------|-----------|------|
| 売上高 | BUN_CEO手動入力 | 請求書ベース |
| APIコスト | 全社ボード/APIコストシート | 自動集計 |
| その他経費 | BUN_CEO手動入力 | 交通費・通信費等 |
| 純利益 | 売上高 − 総コスト | Pythonで計算 |
| 目標達成率 | 目標設定済みの場合 | 月200万円を2031年目標 |

---

## APIコスト管理（確定 2026-05-20）

| AI | 月単価目安 | 備考 |
|----|---------|------|
| Claude API | 変動（上限¥10,000） | DEV L2: ¥10-30 / L3: ¥100-800 |
| DeepSeek | 少額（差分監視中） | DEV QA専用 |
| Gemini | 無料枠内 | RSC部門 |
| OpenAI | 少額 | QA・System QA |

**月次上限：¥10,000（Claude API合計）を超えた時点でBUN_CEOに即報告。**

---

## 実行手順（この順番を守れ）

### 月次レポート作成
1. 全社ボードのAPIコストシートからAPI実績を取得する
2. BUN_CEOから売上・その他経費データを受け取る（推測禁止）
3. Pythonで損益計算を実行する（`scripts/monthly_calc.py`）
4. 前月比較・目標達成率を算出する
5. 異常値チェック（±30%超過項目を赤フラグ）
6. FIN_月次損益レポート_YYYYMMDD.md をType A形式で作成する
7. Reports/FIN/ に保存してからBUN_CEOに報告する

### 異常値検知時の対応
- ±30%超過 → BUN_CEOに即アラート（説明と仮説を添えて）
- APIコスト月1万円超 → 即座にアラート・コスト超過原因を特定
- 純利益マイナス → BUN_CEOに即報告（推測での原因特定は禁止）

---

## n8n FIN月次レポートWF（uxIDllsGUiDilADI）技術情報

- スケジュール：毎月1日 9:00 JST（cron: `0 9 1 * *`）
- 実行AI：Claude Sonnet（credential: 6RjA3eGBjtQkbNiy）
- QA：GPT-4o（credential: x2D3cGEreDX5TCzW）
- 出力先：Google Drive / Reports/FIN/

---

## 絶対にやってはいけないこと

- 財務数値を推測・丸めで計算すること
- 異常値をスルーして通常レポートとして提出すること
- BUN_CEOに確認せず収益目標を勝手に変更すること
- APIコスト超過を発見してから24時間以上報告を遅らせること

# Antigravity × GitHub 連携設定ガイド

NorthStar OSの思想とAntigravityを一致させるための情報パッケージ。  
**このファイルを読んでから、Antigravityにそのまま渡してください。**

---

## 1. GitHubリポジトリ

```
リポジトリ: github.com/bestthink01109/northstar-os（Private）
オーナー: bestthink01109
主要ブランチ: main
```

### Antigravityが読むべきファイル

| ファイル | 内容 | タイミング |
|---------|------|----------|
| `ANTIGRAVITY_PROMPT.md` | COOルール・セッション手順・出力フォーマット | セッション開始時に必ず読む |
| `NORTHSTAR_MANUAL.md` | システム全体の使用マニュアル | 参照用 |
| `Architecture_Plan_v3_完全版_20260501.md` | マスター設計書 | 深い判断が必要な時 |

### Antigravityが書き込むべきタイミング

- COOルールを変更・追記した時 → `ANTIGRAVITY_PROMPT.md` を更新
- マニュアルを更新した時 → `NORTHSTAR_MANUAL.md` を更新
- 新しいスクリプトを作った時 → `scripts/` に追加

---

## 2. ストレージポリシー（最重要・絶対ルール）

| 種別 | 保存先 | 具体例 |
|------|-------|-------|
| **データ**（生成・蓄積） | Google Drive | Dashboard、レポート、Signal_DB.csv、COO_Context |
| **マニュアル・設計書** | **GitHub** ← Antigravityの管轄 | NORTHSTAR_MANUAL.md、Architecture_Plan |
| **アプリ・スクリプト** | **GitHub** ← Antigravityの管轄 | scripts/drive.js、session_export.js |
| **機密情報**（キー・トークン） | **ローカルのみ** | APIキー、oauth_tokens.json（GitHub push禁止） |

> **データはGoogle Drive。マニュアル・アプリはGitHub。機密情報はローカルのみ。**

---

## 3. ファイル命名規則（絶対ルール）

### 基本ルール
- ファイル名末尾には必ず **`_YYYYMMDD`** 形式で当日の日付を付与する
- 省略不可

### 部門別プレフィックス

| 部門 | プレフィックス | 例 |
|------|------------|-----|
| DEV（開発） | `DEV_` | `DEV_KENZAIリリースノート_20260513.md` |
| RSC（リサーチ） | `RSC_` | `RSC_全ターゲット_20260513.md` |
| BizDev（事業開発） | `BIZ_` | `BIZ_市場スキャン_20260513.md` |
| FIN（財務） | `FIN_` | `FIN_月次レポート_202605.md` |
| OPS（業務） | `OPS_` | `OPS_シフト修正報告_20260513.md` |
| COO横断 | `COO_` | `COO_Context_20260513.md` |
| ダッシュボード | `Dashboard_` | `Dashboard_20260513.md` |

---

## 4. Google Drive フォルダID一覧（保存先）

成果物を保存する際は必ずこのフォルダIDを使用すること。

| 部門・用途 | フォルダID | 保存ファイル例 |
|-----------|-----------|--------------|
| Reports/（親） | `1uM990vQViDJ5BTer9_XGJZUZsJEKD3y_` | — |
| Reports/DEV/ | `1axzPX0xjgWxVLTHLQHZf-7kSLO2Q_9kZ` | DEV_*.md |
| Reports/RSC/ | `1I_68Pimq8jKjq6xfPMAeD22oeAHc8mTf` | RSC_*.md |
| Reports/RSC/FUKUOKA/ | `1QxbuEYftnqZh4GnqdWAZ7PEWJGZor0GW` | RSC_福岡_*.md |
| Reports/RSC/KUMAMOTO/ | `1q5SwCxPyGJNA_aJlsKUaU48rLcYgM1-k` | RSC_熊本_*.md |
| Reports/RSC/MHLW/ | `14lmvkwbJ3o4-xHxZ32R5edsYBhyNyuUt` | RSC_厚労省_*.md |
| Reports/RSC/AI/ | `131j6YvcknIA2KPfIXW_uR7xCsPS7Eqc8` | RSC_AI_*.md |
| Reports/BizDev/ | `1ItQqd-_I3ARoUkclvJc4pVU2HMMlq_dS` | BIZ_*.md |
| Reports/FIN/ | `1kXD9larver4TTgWAJAVeBLWujb2eaM70` | FIN_*.md |
| Reports/OPS/ | `1ahvEniXrxUiPH50yc1A1g6E4qcFdLccv` | OPS_*.md |
| research/Daily_Report/ | `1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8` | Dashboard_*.md、COO_Context_*.md |

### 特別ファイル（固定ID）

| ファイル | ID |
|---------|-----|
| Signal_DB.csv | `1iCRjElopMprCT8l-yPvriGWVjWizRXuh` |

### 成果物保存コマンド（参考）

```bash
node /Users/fuminariaksse/.config/gdrive-mcp/drive.js create \
  "BIZ_市場スキャン_20260513.md" \
  1ItQqd-_I3ARoUkclvJc4pVU2HMMlq_dS \
  /tmp/output.md
```

---

## 5. Googleカレンダー ID

| カレンダー | ID | 用途 |
|---------|-----|------|
| メインカレンダー | `bestthink01109@gmail.com` | 予定・ミーティング |
| BUN_CEOタスク | `a0c7e0a0c3b9038b4a54b546d6119480d08d047ac3676811ea6fd1b00da46dc2@group.calendar.google.com` | タスク（削除禁止・[完了]で永久保存） |

**ルール:**
- 予定 → メインカレンダー
- タスク → BUN_CEOタスクカレンダー（厳格分離）
- タスク削除禁止 → 必ず`[完了]`に書き換える

---

## 6. Antigravityの役割と範囲

### できること（GitHub経由）
- COOルール・マニュアルの参照・更新
- 設計書の読み込み・改訂提案
- スクリプトのレビュー・改善
- セッションでの戦略議論・判断支援
- GitHubファイルの作成・更新

### できないこと（ローカル操作は人間が実行する）
- `node drive.js` などのローカルコマンド実行
- `node session_apply.js` の実行
- Google Drive・カレンダーへの直接APIコール

### セッション終了時の必須出力形式

```
===SESSION_OUTPUT_START===

DASHBOARD_UPDATE:
（更新後のダッシュボード全文）
END_DASHBOARD

CALENDAR_ADD_TASK: タイトル | YYYY-MM-DD
CALENDAR_ADD_EVENT: タイトル | YYYY-MM-DD | HH:MM | calendarId
CALENDAR_COMPLETE: eventId
SIGNAL_DB: ランク(S/A/B/C) | シグナル本文 | DASHBOARD_SESSION

===SESSION_OUTPUT_END===
```

---

## 7. システム全体像

```
Claude Code（日常セッション・枠に余裕がある時）
  ↓ 枠が少ない時の代替
Antigravity ← GitHubでルール・マニュアルを参照・更新

n8n（VPS: 162.43.78.67:5678） ← 自動化（24/365稼働）
  06:00 RSCリサーチ巡回 → Reports/RSC/ + LINE送信
  07:00 朝ブリーフィング → LINE + Dashboard作成
  18:45 部門日次報告集約 → Reports/ + LINE
  19:00 夕リフレクション → LINE + Dashboard #7
  月08:00 BizDevスキャン → Reports/BizDev/ + LINE
  日03:00 n8nバックアップ → Reports/DEV/
  日04:00 Signal DB分析 → LINE
  1日09:00 FIN月次レポート → Reports/FIN/ + LINE

LINE（NorthStar @535qeekl） ← 社長への通知 + コマンド受付
  コマンド: タスク追加 / 予定追加 / 承認 / 却下 / [戦略評価]
```

---

## 8. GitHubへのアクセス方法

### RAWファイル取得（読み取り）
```
https://raw.githubusercontent.com/bestthink01109/northstar-os/main/{ファイルパス}
```

### GitHub API（読み書き）
```
GET  https://api.github.com/repos/bestthink01109/northstar-os/contents/{path}
PUT  https://api.github.com/repos/bestthink01109/northstar-os/contents/{path}
認証: Authorization: Bearer {GitHub PAT}
```

> **GitHub PATは社長が管理しています。Antigravityに渡す際は直接入力してください。**

---

## 9. セッション開始の標準手順

### Antigravityのみ（Claude Code枠節約）

```
① Antigravityに以下を貼り付け:
「以下のURLを読んでNorthStar OS COOとしてセッションを開始してください:
https://raw.githubusercontent.com/bestthink01109/northstar-os/main/ANTIGRAVITY_PROMPT.md」

② ローカルでセッション書き出し:
node /Users/fuminariaksse/.config/gdrive-mcp/session_export.js /tmp/session.txt

③ /tmp/session.txt の内容をAntigravityに貼り付け → セッション開始

④ セッション終了後、出力を /tmp/session_output.txt に保存

⑤ ローカルで反映:
node /Users/fuminariaksse/.config/gdrive-mcp/session_apply.js /tmp/session_output.txt
```

---

## 10. Antigravityへの一言要約（コピペ用）

```
私はBUN社長（赤瀬文成）、一人経営「ノーススター経営サポート」。
あなたはCOO AIです。

まず以下のURLを読んでください:
https://raw.githubusercontent.com/bestthink01109/northstar-os/main/ANTIGRAVITY_PROMPT.md

ストレージルール:
- データ(Dashboard・レポート) → Google Drive（フォルダIDはこのファイルのセクション4参照）
- マニュアル・スクリプト → GitHub（更新したらpush）
- APIキー・トークン → ローカルのみ（GitHubに絶対入れない）
- ファイル名は必ず _YYYYMMDD で終わる
- 部門別プレフィックス: DEV_/RSC_/BIZ_/FIN_/OPS_/COO_
- 省略・手抜き禁止
```

---

*このファイルはGitHubで管理されています。*  
*最新版: https://github.com/bestthink01109/northstar-os/blob/main/ANTIGRAVITY_GITHUB_SETUP.md*

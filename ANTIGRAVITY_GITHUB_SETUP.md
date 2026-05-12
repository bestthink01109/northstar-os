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

## 3. Antigravityの役割と範囲

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

Antigravityはセッション終了時に以下のフォーマットで変更を出力する。  
人間が `node session_apply.js` を実行して反映する。

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

## 4. システム全体像

```
Claude Code（日常セッション・枠に余裕がある時）
  ↓ 枠が少ない時の代替
Antigravity ← GitHubでルール・マニュアルを参照・更新

n8n（VPS: 162.43.78.67:5678）
  自動化ワークフロー（24/365稼働）:
  - 毎日 06:00: RSCリサーチ巡回（7サイト）
  - 毎日 07:00: 朝ブリーフィング + Dashboard作成
  - 毎日 18:45: 部門日次報告集約
  - 毎日 19:00: 夕リフレクション
  - 毎週月曜 08:00: BizDevスキャン
  - 毎週日曜 03:00: n8nバックアップ
  - 毎週日曜 04:00: Signal DB週次分析
  - 毎月1日 09:00: FIN月次レポート

Google Drive
  データ蓄積:
  - research/Daily_Report/Dashboard_YYYYMMDD.md（毎朝自動作成）
  - Reports/RSC/RSC_全ターゲット_YYYYMMDD.md（毎朝自動作成）
  - Reports/BizDev/Signal_DB.csv（蓄積）
  - Reports/BizDev/BIZ_市場スキャン_YYYYMMDD.md
  - Reports/FIN/FIN_月次レポート_YYYYMM.md

LINE（NorthStar @535qeekl）
  社長への通知:
  - 朝6:00: RSCリサーチ提言
  - 朝7:00: カレンダーブリーフィング
  - 夕18:45: 部門日次報告
  - 夕19:00: リフレクション
  社長からのコマンド:
  - タスク追加 / 予定追加 / 承認 / 却下 / [戦略評価]
```

---

## 5. GitHubへのアクセス方法

### RAWファイル取得（読み取り）
```
https://raw.githubusercontent.com/bestthink01109/northstar-os/main/{ファイルパス}
```

例：
```
https://raw.githubusercontent.com/bestthink01109/northstar-os/main/ANTIGRAVITY_PROMPT.md
https://raw.githubusercontent.com/bestthink01109/northstar-os/main/NORTHSTAR_MANUAL.md
```

### GitHub API（読み書き）
```
GET  https://api.github.com/repos/bestthink01109/northstar-os/contents/{path}
PUT  https://api.github.com/repos/bestthink01109/northstar-os/contents/{path}
認証: Authorization: Bearer {GitHub PAT}
```

> **GitHub PATは社長が管理しています。Antigravityに渡す際は直接入力してください。**

---

## 6. セッション開始の標準手順

### パターンA: Antigravityのみ（Claude Code枠節約）

```
① Antigravityに以下を貼り付け:
「以下のURLを読んでNorthStar OS COOとしてセッションを開始してください:
https://raw.githubusercontent.com/bestthink01109/northstar-os/main/ANTIGRAVITY_PROMPT.md」

② ローカルでセッション書き出し実行:
node /Users/fuminariaksse/.config/gdrive-mcp/session_export.js /tmp/session.txt

③ /tmp/session.txt の内容をAntigravityに貼り付け → セッション開始

④ セッション終了後、出力を /tmp/session_output.txt に保存

⑤ ローカルで反映:
node /Users/fuminariaksse/.config/gdrive-mcp/session_apply.js /tmp/session_output.txt
```

### パターンB: Claude Code（通常時）

```
/dashboard
```

---

## 7. Antigravityへの一言要約（コピペ用）

```
私はBUN社長（赤瀬文成）、一人経営の会社「ノーススター経営サポート」を経営しています。
あなたはCOO AIです。

まず以下のURLを読んでください:
https://raw.githubusercontent.com/bestthink01109/northstar-os/main/ANTIGRAVITY_PROMPT.md

ルール:
- データ(Dashboard・レポート・Signal DB) → Google Drive
- マニュアル・スクリプト → GitHub（更新したらpush）
- APIキー・トークン → ローカルのみ（GitHubに絶対入れない）
- 省略・手抜き禁止
```

---

*このファイルはGitHubで管理されています。*  
*最新版: https://github.com/bestthink01109/northstar-os/blob/main/ANTIGRAVITY_GITHUB_SETUP.md*

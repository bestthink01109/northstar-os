# 📘 NorthStar OS 使用マニュアル

最終更新: 2026-05-08

---

## ⚠️ ストレージポリシー（絶対ルール）

| 種別 | 保存先 | 具体例 |
|------|-------|-------|
| **データ**（生成・蓄積） | Google Drive | Dashboard、各種レポート、Signal_DB.csv、COO_Context |
| **マニュアル・設計書** | GitHub | NORTHSTAR_MANUAL.md、Architecture_Plan_v3.md |
| **アプリ・スクリプト** | GitHub | scripts/drive.js、Pythonアプリ |
| **機密情報**（キー・トークン） | ローカルのみ | n8n-api.sh、oauth_tokens.json（GitHub push禁止） |

> マニュアル・スクリプトを更新したら必ず GitHub に push すること。

---

## 🗂 目次
1. [自動で動くもの（n8n）](#自動)
2. [LINEから使えるコマンド](#LINE)
3. [Claude Codeで使えるコマンド](#Claude)
4. [drive.js コマンド一覧](#drive)
5. [Google Driveのフォルダ構成](#folder)
6. [Googleカレンダー ID](#calendar)
7. [n8n ワークフロー一覧](#workflows)
8. [トラブル対応](#trouble)

---

## 1. 自動で動くもの（n8n） {#自動}

### 毎日の自動フロー

| 時刻(JST) | ワークフロー | 出力先 | 内容 |
|-----------|------------|--------|------|
| **06:00** | RSCリサーチ巡回 | Reports/RSC/ + Dashboard #4 | 7サイト巡回・Gemini解析・シグナル検知 |
| **07:00** | 朝ブリーフィング + Dashboard作成 | LINE + Daily_Report/ | 予定・タスク・LINE通知・Dashboard_YYYYMMDD.md 生成 |
| **18:45** | 部門日次報告集約 | Reports/ + LINE | RSC/BizDev活動確認・Signal DBシグナル集計 |
| **19:00** | 夕リフレクション | LINE + Dashboard #7 | 今日の結果・タスク完了確認・明日向け |

### 週次・月次の自動フロー

| タイミング | ワークフロー | 出力先 | 内容 |
|-----------|------------|--------|------|
| **月曜 08:00** | BizDevスキャン | Reports/BizDev/ + LINE | 市場スキャン（Gemini+Claude Opus+QA） |
| **日曜 03:00** | n8nバックアップ | Reports/DEV/ | 全ワークフローJSONをバックアップ |
| **日曜 04:00** | Signal DB週次分析 | LINE | Story DB昇格候補を提案 |
| **毎月1日 09:00** | FIN月次レポート | Reports/FIN/ + LINE | コスト集計・利益率・最適化提案 |

---

## 2. LINEから使えるコマンド {#LINE}

LINEで **NorthStar** ボット（@535qeekl）に送るだけ。

### カレンダー操作

```
タスク 明日 投資家レポート確認
タスク 5/10 PR資料作成
タスク 今日 会議準備

予定 5/10 15時 A社MTG
予定 明後日 10:00 外部面談
予定 5/12 14:30 医師面談
```

| コマンド | 動作 |
|---------|------|
| `タスク [日付] タイトル` | BUN_CEOカレンダーにタスク追加 |
| `予定 日付 時間 タイトル` | メインカレンダーに予定追加 |

**日付の書き方**: `今日` `明日` `明後日` `5/10` `5月10日`

---

### 承認・却下フロー

```
承認 BizDev新規案件提案
承認 A社との契約更新
却下 コスト超過の追加開発
```

→ Signal DBにランクA記録・確認返信あり

---

### リアルタイム戦略評価

Claude Opusが即座に事業影響を評価してLINEに返信・Driveに保存。

```
[戦略評価] A社から失注、理由は価格
[戦略評価] B施設が新規依頼、月2万円想定
[戦略評価] 処遇改善加算IIIの改定通知が来た
[戦略評価] 社労士法人から業務委託の相談
```

**出力**: Claude Opus評価 → LINE返信 + `Reports/BizDev/BIZ_戦略更新_YYYYMMDD.md` 保存

---

## 3. Claude Codeで使えるコマンド {#Claude}

### /dashboard — 朝夕セッション開始

```
/dashboard
```

**セッション構成:**
- **#1 Core Vision**: ビジョンコーチング・タイムライン更新
- **#2 今日の予定・タスク**: 変更→カレンダー即反映
- **#3 今週展望**: 週間確認・修正
- **#4 Research Facts**: RSCリサーチをCOOと議論
- **#5 AI Task Workspace**: COO報告・方向性決定
- **#6 COO Strategy Report**: 今日の最終方針確定
- **#7 Reflection**: 今日の結果・明日の方向性

### /save-context — COOコンテキスト保存

```
/save-context
```

セッション内容を `COO_Context_YYYYMMDD.md` としてDriveに保存。

### /manual — このマニュアルを表示

```
/manual
```

---

## 4. drive.js コマンド一覧 {#drive}

**GitHub**: https://github.com/bestthink01109/northstar-os/blob/main/scripts/drive.js
**ローカル**: `/Users/fuminariaksse/.config/gdrive-mcp/drive.js`

### Driveファイル操作

| コマンド | 説明 |
|---------|------|
| `node drive.js list [フォルダID]` | フォルダ内一覧 |
| `node drive.js read <fileId>` | ファイル内容を読む |
| `node drive.js write <fileId> [filePath]` | ファイルを更新 |
| `node drive.js create <name> <parentId> [filePath]` | 新規ファイル作成 |
| `node drive.js search <keyword>` | キーワードで検索 |

### ダッシュボード操作

| コマンド | 説明 |
|---------|------|
| `node drive.js today-dashboard` | 今日のDashboardのID/URL |
| `node drive.js read-today` | 今日のDashboard内容を表示 |
| `node drive.js write-today [filePath]` | 今日のDashboardを更新 |
| `node drive.js create-dashboard` | 今日のDashboard新規作成 |

### カレンダー操作

| コマンド | 説明 |
|---------|------|
| `node drive.js events [calendarId]` | 今後1週間の予定 |
| `node drive.js add-event <calId> <title> <date> [time]` | 予定追加 |
| `node drive.js add-task <title> <date>` | タスク追加（BUN_CEO） |
| `node drive.js complete-task <eventId> [calId]` | タスクを[完了]にする |
| `node drive.js update-event <calId> <eventId> <field> <value>` | 予定更新（field: title/date/time） |

**よく使うカレンダーID:**
```
MAIN: bestthink01109@gmail.com
TASK: a0c7e0a0c3b9038b4a54b546d6119480d08d047ac3676811ea6fd1b00da46dc2@group.calendar.google.com
```

---

## 5. Google Driveのフォルダ構成 {#folder}

```
Google Drive/
├── 📊 Reports/                    ID: 1uM990vQViDJ5BTer9_XGJZUZsJEKD3y_
│   ├── DEV/                       ID: 1axzPX0xjgWxVLTHLQHZf-7kSLO2Q_9kZ
│   ├── RSC/                       ID: 1I_68Pimq8jKjq6xfPMAeD22oeAHc8mTf
│   │   ├── FUKUOKA/               ID: 1QxbuEYftnqZh4GnqdWAZ7PEWJGZor0GW
│   │   ├── KUMAMOTO/              ID: 1q5SwCxPyGJNA_aJlsKUaU48rLcYgM1-k
│   │   ├── MHLW/                  ID: 14lmvkwbJ3o4-xHxZ32R5edsYBhyNyuUt
│   │   └── AI/                    ID: 131j6YvcknIA2KPfIXW_uR7xCsPS7Eqc8
│   ├── BizDev/                    ID: 1ItQqd-_I3ARoUkclvJc4pVU2HMMlq_dS
│   │   └── Signal_DB.csv          ID: 1iCRjElopMprCT8l-yPvriGWVjWizRXuh
│   ├── FIN/                       ID: 1kXD9larver4TTgWAJAVeBLWujb2eaM70
│   └── OPS/                       ID: 1ahvEniXrxUiPH50yc1A1g6E4qcFdLccv
└── research/Daily_Report/         ID: 1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8
    ├── Dashboard_YYYYMMDD.md      ← 毎朝7:00自動作成（データ）
    └── COO_Context_YYYYMMDD.md    ← /save-context で保存（データ）
```

---

## 6. Googleカレンダー ID {#calendar}

| カレンダー | ID | 用途 |
|---------|-----|------|
| メインカレンダー | `bestthink01109@gmail.com` | 予定・ミーティング |
| BUN_CEOタスク | `a0c7e0a0c3b9038b4a54b546d6119480d08d047ac3676811ea6fd1b00da46dc2@group.calendar.google.com` | タスク（[完了]で永久保存） |

---

## 7. n8n ワークフロー一覧 {#workflows}

| ワークフロー名 | ID | スケジュール |
|-------------|-----|------------|
| 朝ブリーフィング+Dashboard | NjmKR3rlzaAdznoB | 毎日7:00 |
| RSCリサーチ巡回 | 796EUn4zvboKFQiP | 毎日6:00 |
| 夕リフレクション | VD4QeU4XVfhqmMbl | 毎日19:00 |
| 部門日次報告集約 | 4LTj5vfwCcDqVUKc | 毎日18:45 |
| LINEコマンド処理 | Ury2oteVKpcHBI8m | 常時（Webhook） |
| BizDevスキャン | 0zftWq8EAnbcJwrE | 毎週月曜8:00 |
| Signal DB週次分析 | wxJUU8dPwbWqFyGP | 毎週日曜4:00 |
| n8nバックアップ | PAlz3XfDYycQA48D | 毎週日曜3:00 |
| FIN月次レポート | uxIDllsGUiDilADI | 毎月1日9:00 |

**n8n管理画面:** `http://162.43.78.67:5678`

---

## 8. トラブル対応 {#trouble}

```bash
# ワークフロー実行状況確認
node /Users/fuminariaksse/.config/gdrive-mcp/check_all_workflows.js

# スケジュール設定確認
node /Users/fuminariaksse/.config/gdrive-mcp/check_schedules.js

# Dashboardを手動作成
node /Users/fuminariaksse/.config/gdrive-mcp/drive.js create-dashboard

# Signal DB確認
node /Users/fuminariaksse/.config/gdrive-mcp/drive.js read 1iCRjElopMprCT8l-yPvriGWVjWizRXuh
```

---

## ⚡ クイックリファレンス

```
LINE:
  タスク 明日 A社提案書作成
  予定 5/15 10:00 B社MTG
  承認 新規プロダクト開発
  [戦略評価] C社から失注

Claude Code:
  /dashboard    → 朝夕セッション
  /save-context → COOコンテキスト保存
  /manual       → このマニュアル

drive.js:
  node drive.js read-today
  node drive.js add-task "タスク名" "2026-05-10"
  node drive.js complete-task <eventId>
  node drive.js events bestthink01109@gmail.com
```

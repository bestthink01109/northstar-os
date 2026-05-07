# 📘 NorthStar OS 使用マニュアル

最終更新: 2026-05-08

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

**動作:**
1. 今日の `Dashboard_YYYYMMDD.md` をDriveから読み込み
2. Section 1〜7を順にセッション進行

**セッション構成:**
- **#1 Core Vision**: ビジョンコーチング・タイムライン更新
- **#2 今日の予定・タスク**: 変更→カレンダー即反映
- **#3 今週展望**: 週間確認・修正
- **#4 Research Facts**: RSCリサーチをCOOと議論
- **#5 AI Task Workspace**: COO報告・方向性決定
- **#6 COO Strategy Report**: 今日の最終方針確定
- **#7 Reflection**: 今日の結果・明日の方向性

---

### /save-context — COOコンテキスト保存

```
/save-context
```

**動作**: セッション内容を `COO_Context_YYYYMMDD.md` としてDriveに保存

**次回セッション開始時**: 自動的に最新のCOO_Contextを読み込む

---

### /manual — このマニュアルを表示

```
/manual
```

---

### drive.js — ローカルから直接操作

実行場所: `/Users/fuminariaksse/.config/gdrive-mcp/`

```bash
cd /Users/fuminariaksse/.config/gdrive-mcp

# 今日のダッシュボードを読む
node drive.js read-today

# 今日のダッシュボードを更新（内容を/tmp/new.mdに書いてから）
node drive.js write-today /tmp/new.md

# ファイル検索
node drive.js search "RSC_全ターゲット"
node drive.js search "Dashboard_202605"
```

---

## 4. drive.js コマンド一覧 {#drive}

### Driveファイル操作

| コマンド | 説明 |
|---------|------|
| `node drive.js list [フォルダID]` | フォルダ内一覧 |
| `node drive.js read <fileId>` | ファイル内容を読む |
| `node drive.js write <fileId> [filePath]` | ファイルを更新 |
| `node drive.js create <name> <parentId> [filePath]` | 新規ファイル作成 |
| `node drive.js search <keyword>` | キーワードで検索 |
| `node drive.js mkdir <name> [parentId]` | フォルダ作成 |

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
| `node drive.js calendars` | カレンダー一覧 |
| `node drive.js events [calendarId]` | 今後1週間の予定 |
| `node drive.js events-range <calId> <from> <to>` | 期間指定で予定一覧 |
| `node drive.js get-event <calId> <eventId>` | イベント詳細 |
| `node drive.js add-event <calId> <title> <date> [time]` | 予定追加 |
| `node drive.js add-task <title> <date>` | タスク追加（BUN_CEO） |
| `node drive.js complete-task <eventId> [calId]` | タスクを[完了]にする |
| `node drive.js update-event <calId> <eventId> <field> <value>` | 予定更新 |

**update-event の field 指定:**
- `title` : タイトル変更
- `date` : 日付変更（例: `2026-05-10`）
- `time` : 時刻変更（例: `15:00`）

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
│   │   └── n8n_backup_YYYYMMDD.json  ← 毎週日曜3:00自動
│   ├── RSC/                       ID: 1I_68Pimq8jKjq6xfPMAeD22oeAHc8mTf
│   │   ├── FUKUOKA/               ID: 1QxbuEYftnqZh4GnqdWAZ7PEWJGZor0GW
│   │   ├── KUMAMOTO/              ID: 1q5SwCxPyGJNA_aJlsKUaU48rLcYgM1-k
│   │   ├── MHLW/                  ID: 14lmvkwbJ3o4-xHxZ32R5edsYBhyNyuUt
│   │   └── AI/                    ID: 131j6YvcknIA2KPfIXW_uR7xCsPS7Eqc8
│   │   └── RSC_全ターゲット_YYYYMMDD.md  ← 毎朝6:00自動
│   ├── BizDev/                    ID: 1ItQqd-_I3ARoUkclvJc4pVU2HMMlq_dS
│   │   ├── Signal_DB.csv          ID: 1iCRjElopMprCT8l-yPvriGWVjWizRXuh
│   │   ├── BIZ_市場スキャン_YYYYMMDD.md  ← 毎週月曜8:00自動
│   │   └── BIZ_戦略更新_YYYYMMDD.md      ← [戦略評価]コマンド時
│   ├── FIN/                       ID: 1kXD9larver4TTgWAJAVeBLWujb2eaM70
│   │   └── FIN_月次レポート_YYYYMM.md    ← 毎月1日9:00自動
│   └── OPS/                       ID: 1ahvEniXrxUiPH50yc1A1g6E4qcFdLccv
└── research/Daily_Report/         ID: 1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8
    ├── Dashboard_YYYYMMDD.md      ← 毎朝7:00自動作成
    └── COO_Context_YYYYMMDD.md    ← /save-context で保存
```

---

## 6. Googleカレンダー ID {#calendar}

| カレンダー | ID | 用途 |
|---------|-----|------|
| メインカレンダー（赤瀬文成） | `bestthink01109@gmail.com` | 予定・ミーティング |
| BUN_CEOタスク | `a0c7e0a0c3b9038b4a54b546d6119480d08d047ac3676811ea6fd1b00da46dc2@group.calendar.google.com` | タスク管理（[完了]で永久保存） |

**ルール:** 予定はメインカレンダー、タスクはBUN_CEOカレンダーに厳格分離。タスク削除禁止（[完了]に書き換え）。

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
**n8nヘルパー:** `/Users/fuminariaksse/.config/gdrive-mcp/n8n-api.sh`

---

## 8. トラブル対応 {#trouble}

### LINEにブリーフィングが届かない
```bash
node /Users/fuminariaksse/.config/gdrive-mcp/check_all_workflows.js
node /Users/fuminariaksse/.config/gdrive-mcp/check_schedules.js
```

### Dashboardが作成されていない
```bash
node /Users/fuminariaksse/.config/gdrive-mcp/drive.js create-dashboard
```

### カレンダー操作コマンドが失敗する
```bash
node /Users/fuminariaksse/.config/gdrive-mcp/drive.js calendars
node /Users/fuminariaksse/.config/gdrive-mcp/drive.js events bestthink01109@gmail.com
```

### Signal DBを確認したい
```bash
node /Users/fuminariaksse/.config/gdrive-mcp/drive.js read 1iCRjElopMprCT8l-yPvriGWVjWizRXuh
```

### n8nにアクセスできない
```
VPS: 162.43.78.67
n8n: http://162.43.78.67:5678
SSH: ssh root@162.43.78.67
```

---

## ⚡ クイックリファレンス

```
LINE送信例:
  タスク 明日 A社提案書作成
  予定 5/15 10:00 B社ミーティング
  承認 新規プロダクト開発方針
  [戦略評価] C社から失注（競合に負けた）

Claude Code:
  /dashboard    → 朝夕セッション開始
  /save-context → COOコンテキスト保存
  /manual       → このマニュアルを表示

drive.js よく使うもの:
  node drive.js read-today                       → 今日のDashboard読む
  node drive.js add-task "タスク名" "2026-05-10"  → タスク追加
  node drive.js complete-task <eventId>          → タスク完了
  node drive.js events bestthink01109@gmail.com  → 予定一覧
```

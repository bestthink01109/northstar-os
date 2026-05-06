# North Star OS 引き継ぎ書
作成日: 2026/05/03
前セッション: VPS構築・n8n起動・GitHub構築・設計書完全版作成
次セッションのミッション: n8nワークフロー構築開始

---

## 1. このセッションで確定した全内容

### 1-1. 組織設計（確定）

```
BUN社長（取締役会）
判断するのは3つ:
1. お金と契約が絡むこと
2. 大きな方向性（右か左か）
3. OPSの現状判断（勤務体系変更・差異の原因特定・補正値確定・新規社員追加）
        ↓
COO（Claude Opus/Sonnet・執行責任者）
n8n（シンVPS・24/365稼働）で自律実行
        ↓
各部門（DEV/RSC/BizDev/FIN/OPS）
```

### 1-2. インフラ構成（確定）

| 保管場所 | 内容 |
|---------|------|
| VPS（162.43.78.67） | n8n・Pythonアプリ（KENZAI・shift_exporter・payroll_engine） |
| Google Drive | データ（入力Excel・出力CSV・ダッシュボード・リサーチレポート・Reports） |
| GitHub（northstar-os） | 設計書・マニュアル・コードのバックアップ（マスター） |

コード管理の流れ: GitHub（マスター）→ git pull → VPS（実行）→ Google Drive（データ入出力）

### 1-3. Google Driveフォルダ構成（確定）

```
Google Drive/
├── 📊 Reports/（フォルダID: 1uM990vQViDJ5BTer9_XGJZUZsJEKD3y_）
│   ├── OPS/（フォルダID: 1ahvEniXrxUiPH50yc1A1g6E4qcFdLccv）
│   ├── RSC/（フォルダID: 1I_68Pimq8jKjq6xfPMAeD22oeAHc8mTf）
│   │   ├── FUKUOKA/（フォルダID: 1QxbuEYftnqZh4GnqdWAZ7PEWJGZor0GW）
│   │   ├── KUMAMOTO/（フォルダID: 1q5SwCxPyGJNA_aJlsKUaU48rLcYgM1-k）
│   │   ├── MHLW/（フォルダID: 14lmvkwbJ3o4-xHxZ32R5edsYBhyNyuUt）
│   │   └── AI/（フォルダID: 131j6YvcknIA2KPfIXW_uR7xCsPS7Eqc8）
│   ├── BizDev/（フォルダID: 1ItQqd-_I3ARoUkclvJc4pVU2HMMlq_dS）
│   ├── FIN/（フォルダID: 1kXD9larver4TTgWAJAVeBLWujb2eaM70）
│   └── DEV/（フォルダID: 1axzPX0xjgWxVLTHLQHZf-7kSLO2Q_9kZ）
├── research/
│   └── Daily_Report/（フォルダID: 1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8）
├── 🏢【KENZAI】給与計算/
│   ├── 📥 01_ここに入力データをポン/
│   └── 📤 02_ここから完成品を取る/
└── 旧ファイル/（旧FUKUOKA・KUMAMOTO・MHLW・AI等を格納）
```

注意: 全フォルダはサービスアカウント（northstar-n8n@fifth-sprite-492523-i8.iam.gserviceaccount.com）と共有済み。

### 1-3-B. Googleカレンダー ID（確定）

| カレンダー | ID | 用途 |
|---------|-----|------|
| メインカレンダー（赤瀬文成） | bestthink01109@gmail.com | 予定の読み取り・作成 |
| BUN_CEOのタスク | a0c7e0a0c3b9038b4a54b546d6119480d08d047ac3676811ea6fd1b00da46dc2@group.calendar.google.com | タスク管理・[完了]への書き換え |

注意: 両カレンダーともサービスアカウントに「予定の変更」権限で共有済み。

### 1-4. n8n登録済みCredential（確定・6つ）

| Credential名 | 提供元 | 用途 |
|------------|-------|------|
| Anthropic account | Anthropic API | COO判断・OPS OCR・書類生成・BizDev事業判断 |
| Google Gemini(PaLM) Api account | Google AI API | RSC巡回・ブリーフィング・リフレクション・BizDevスキャン |
| DeepSeek account | DeepSeek API | 帳票・文書生成・FINレポート |
| OpenAI account | OpenAI API | QA（全パイプライン共通・GPT-4o mini） |
| GitHub account | GitHub API | コンテキストファイル参照 |
| Google Service Account account | Google Cloud | Google Drive・Calendar読み書き（サービスアカウント） |

### 1-5. 追加予定のCredential（未登録・次セッションで登録）

| API | 用途 | 登録優先度 |
|-----|------|---------|
| LINE Messaging API | 全通知・承認・社長からの指示受信 | 最優先 |
| Google Calendar API（OAuth） | 予定・タスク取得・更新 | 高 |

### 1-6. LINE Messaging API設定状況（確定）

- LINE Developersコンソール: ログイン済み
- プロバイダー名: NorthStar（作成済み）
- チャンネル: NorthStar（Messaging API・作成済み）
- ボットのベーシックID: @535qeekl
- チャンネルアクセストークン（長期）: 発行済み（社長が控えている）
- Channel Secret: 発行済み（社長が控えている）
- 次のステップ: n8nにHTTP RequestノードでLINE Messaging APIを登録・社長のLINEにボットを友達登録・ユーザーID取得

### 1-7. VPS状況（確定）

- IPアドレス: 162.43.78.67
- OS: Ubuntu 24.04 LTS
- Docker: 29.4.1
- n8n: 稼働中（http://162.43.78.67:5678）
- n8nオーナーアカウント: bestthink01109@gmail.com
- ポート開放済み: 22（SSH）・5678（n8n）
- スワップ領域: 未設定（次セッションで設定）

### 1-8. GitHubリポジトリ（確定）

- URL: https://github.com/bestthink01109/northstar-os（Private）
- 最新コミット: v3.2 API利用マップ完全版
- 主要ファイル:
  - Architecture_Plan_v3_完全版_20260501.md（マスター設計書・v3.2）
  - ProductArch_NorthStarOS_完全版_20260501.md
  - RSC_巡回ルール_20260501.md
  - Development/KENZAI/（最新版・引き継ぎ書・操作マニュアル含む）

---

## 2. 未完了・次セッションでやること（優先順）

### 最優先（Phase 1完了に必要）

| # | タスク | 詳細 |
|---|------|------|
| 1 | 設計書の最終版をGitHubにpush | Architecture_Plan_v3_完全版とProductArchの最新版をDownloadsからnorthstar_cleanにコピーしてpush |
| 2 | Google DriveにReportsフォルダを手動作成 | Reports/OPS・RSC・BizDev・FIN・DEVの5サブフォルダを作成 |
| 3 | n8nにLINE Messaging APIをHTTP Requestで登録 | チャンネルアクセストークンをn8nのCredentialsに登録 |
| 4 | 社長のLINEにNorthStarボット（@535qeekl）を友達登録 | QRコードまたはIDで追加 |
| 5 | 社長のLINEユーザーIDを取得 | n8nからLINEにテストメッセージを送るためのユーザーIDが必要 |
| 6 | VPSにスワップ領域追加 | メモリ対策。ターミナルで設定 |
| 7 | n8n Google Drive連携設定 | OAuth認証でGoogle DriveをCredentialsに登録 |
| 8 | n8n Google Calendar連携設定 | OAuth認証でGoogle CalendarをCredentialsに登録 |
| 9 | 朝7:00ブリーフィングワークフロー構築 | Googleカレンダー取得→Gemini整形→LINE通知 |
| 10 | 夕19:00リフレクションワークフロー構築 | 結果集計→Gemini整形→LINE通知 |
| 11 | 朝6:00 RSCリサーチ巡回ワークフロー構築 | 7ターゲット→Gemini解析→Google Drive保存 |

### 高優先（Phase 2）

| # | タスク |
|---|------|
| 12 | VPS上にPython環境構築（GitHubからclone） |
| 13 | KENZAIをVPSで動作確認 |
| 14 | n8nからKENZAIを呼び出すワークフロー構築 |
| 15 | OPS-Cシフト作成自動化 |
| 16 | BizDevパイプライン実装 |
| 17 | FINパイプライン実装 |
| 18 | Googleカレンダー双方向同期・The Task Protocol完全実装 |

---

## 3. COOの絶対ルール（最新・20項目）

1. お金・契約が絡む判断は必ず社長に上げる
2. OPSの現状判断（差異の原因特定・勤務体系変更・補正値確定・新規社員追加）は必ず社長に確認する
3. 上記以外はすべて自分で決めて動く
4. やったことは必ず記録してGoogle Drive/Reports/該当部門に保存する
5. ファイル名末尾には必ず_YYYYMMDD形式で当日の日付を付与する
6. 既存ファイルを読む際は必ず最新日付のファイルを読み込む
7. RSCリサーチ巡回はURL_EXTRACT_RULEとWEEKLY_FALLBACK_RULEを厳守する
8. GitHubのコンテキストファイルを必ず参照して出力する（同名ファイルは保存日が遅いものを参照）
9. 所定の書式やルールを逸脱しないこと（Masterフォーマットがあればコピーする）
10. 法定基準（人員配置基準・処遇改善加算・介護報酬等）を逸脱しないこと
11. 労務計算はAIに任せない。Pythonコードで厳密処理する
12. スケジュールとダッシュボードに差分を発見した場合は勝手に上書きせず必ず社長へ確認アラートを出す
13. OPS（既存業務の自動化）に関する仕様確定は、必ず社長にヒアリングしてから確定する。推測・捏造は禁止
14. Googleカレンダーのタスクの削除は厳禁。必ず[完了]に書き換えてグレーで永久保存する
15. Googleカレンダーの予定はメインカレンダー・タスクはGoogleカレンダーのBUN_CEOカレンダーに厳格分離する
16. ダッシュボードはGoogleカレンダーから毎朝読み込むまな板として機能させる
17. 省略・手抜き・「以下略」は職務放棄とみなす
18. 分からないことは自分で3回考えてから社長に質問する。ただし法令・お金・契約は迷わず即座に社長に上げる
19. やったことは必ず成果物としてGoogle DriveのReports/該当部門フォルダに保存してから報告する
20. 社長に甘えない。自分でできることは自分でやる。社長の時間を使うのはお金・契約・OPS判断・大きな方向性のみ

---

## 4. 設計書の最終状態（v3.2）

Architecture_Plan_v3_完全版_20260501.mdの構成:

| セクション | 内容 |
|---------|------|
| §1 | 経営理念・会社ポリシー |
| §2 | 基本プロファイル（売上30万円・6社・2事業） |
| §3 | ノーススター（2031年月200万円・2拠点生活） |
| §4 | ビジョンタイムライン |
| §5 | 品質・姿勢の掟（省略禁止・魂の定義） |
| §6 | 組織構造（社長3判断・COO中心） |
| §7 | COOシステムプロンプト完全版（責任範囲5領域・絶対ルール20項目） |
| §8 | The Task Protocol（Googleカレンダー一元管理・BUN_CEOカレンダー） |
| §9 | ダッシュボード仕様（7セクション・Google Drive・claude.ai連携） |
| §10 | マルチモデルAI配置表・API利用マップ（9-1〜9-4） |
| §11 | RSCリサーチ巡回ルール完全版（7ターゲット・シグナル検知2種別） |
| §12 | OPS代行業務自動化パイプライン（OPS-A/K/C/共通） |
| §13 | プロダクト開発アーキテクチャ概要（ProductArchへの参照リンク） |
| §14 | 収益・損益分岐戦略（1万円/月・2社黒字化・利益率97%） |
| §15 | QA必須ルール（GPT-4o mini・検証9項目） |
| §16 | 常駐自動フロー一覧（9フロー・Reports出力先対応） |
| §17 | フィードバックループ設計（各部門報告ルール・毎日/月次ループ） |
| §18 | インフラ構成・役割分担（VPS/Drive/GitHub・コード管理フロー） |
| §19 | コスト構造（固定3,650円+API従量1,701円=月5,351円） |
| §20 | 実行ロードマップ（Phase 1〜3） |
| §21 | 検証基準 |

---

## 5. 次セッション開始時の最初の指示

次のセッションで最初に以下を実行してください。

```
このセッションではNorth Star OS v3のn8nワークフロー構築を行います。

プロジェクトナレッジに以下がアップロード済みです:
- HANDOVER_NorthStarOS_20260503.md（本引き継ぎ書）
- Architecture_Plan_v3_完全版_20260501.md（マスター設計書・v3.2）
- ProductArch_NorthStarOS_完全版_20260501.md

本日の作業優先順:
1. 設計書最終版をGitHubにpush
2. Google DriveにReportsフォルダを手動作成
3. VPSにスワップ領域追加
4. n8nにLINE Messaging APIを登録
5. 社長のLINEにNorthStarボット（@535qeekl）を友達登録・ユーザーID取得
6. 朝7:00ブリーフィングワークフロー構築開始

絶対ルール: ALIGN FIRST。手抜きをしない。網羅する。魂を込める。
省略・手抜き・「以下略」は職務放棄とみなす。
```

---

**「ALIGN FIRST. Then Take Massive Action.」**
**「手抜きをしない。網羅する。魂を込める。」**

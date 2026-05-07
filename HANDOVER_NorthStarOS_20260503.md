# North Star OS 引き継ぎ書
作成日: 2026/05/03
更新日: 2026/05/07（v3.3 秋吉AI方式追加実装計画を追記）
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
| Google Drive | データ（入力Excel・出力CSV・ダッシュボード・リサーチレポート・Reports・Signal_DB.csv） |
| GitHub（northstar-os） | 設計書・マニュアル・コードのバックアップ（マスター）・Story_DB.md |

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
│   │   └── Signal_DB.csv（Phase 2-9で作成・Signal DBの蓄積先）
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
- 最新コミット: v3.3 秋吉AI方式追加実装計画
- 主要ファイル:
  - Architecture_Plan_v3_完全版_20260501.md（マスター設計書・v3.3）
  - ProductArch_NorthStarOS_完全版_20260501.md
  - RSC_巡回ルール_20260501.md
  - Story_DB.md（Phase 2-10で作成予定）
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
| 19 | Signal DB構築（Google Drive / Reports / BizDev / Signal_DB.csv への自動蓄積フロー） |
| 20 | Story DB初期インプット（BUN社長が手動入力・目標10〜20件・GitHub / Story_DB.md） |
| 21 | BUN社長クローン機能テスト（COOシステムプロンプトにデジタルクローン原則を統合・精度検証） |
| 22 | 会議前ブリーフィングワークフロー構築（Googleカレンダートリガー→Story DB参照→LINE送信 会議30分前） |
| 23 | LINE会話自動記録化ワークフロー構築（LINE Webhook受信→Gemini Flash判定→Signal DB書き込み） |
| 24 | リアルタイム戦略更新フロー構築（重要ビジネスイベント報告→Claude Opus評価→LINE即時通知） |

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

## 4. 設計書の最終状態（v3.3）

Architecture_Plan_v3_完全版_20260501.mdの構成:

| セクション | 内容 |
|---------|------|
| §1 | 経営理念・会社ポリシー |
| §2 | 基本プロファイル（売上30万円・6社・2事業） |
| §3 | ノーススター（2031年月200万円・2拠点生活） |
| §4 | ビジョンタイムライン |
| §5 | 品質・姿勢の掟（省略禁止・魂の定義） |
| §6 | 組織構造（社長3判断・COO中心） |
| §7 | COOシステムプロンプト完全版（責任範囲5領域・絶対ルール20項目）+ **BUN社長デジタルクローン原則（v3.3追加）** |
| §8 | The Task Protocol（Googleカレンダー一元管理・BUN_CEOカレンダー） |
| §9 | ダッシュボード仕様（7セクション・Google Drive・claude.ai連携） |
| §10 | マルチモデルAI配置表・API利用マップ（9-1〜9-4） |
| §11 | RSCリサーチ巡回ルール完全版（7ターゲット・シグナル検知2種別）+ **Signal DB設計・Story DB設計（v3.3追加）** |
| §12 | OPS代行業務自動化パイプライン（OPS-A/K/C/共通） |
| §13 | プロダクト開発アーキテクチャ概要（ProductArchへの参照リンク） |
| §14 | 収益・損益分岐戦略（1万円/月・2社黒字化・利益率97%） |
| §15 | QA必須ルール（GPT-4o mini・検証9項目） |
| §16 | 常駐自動フロー一覧（12フロー・Reports出力先対応）**（v3.3で3フロー追加）** |
| §17 | フィードバックループ設計（各部門報告ルール・毎日/月次ループ）+ **LINE会話自動記録化・会議前ブリーフィング・リアルタイム戦略更新（v3.3追加）** |
| §18 | インフラ構成・役割分担（VPS/Drive/GitHub・コード管理フロー） |
| §19 | コスト構造（固定3,650円+API従量1,701円=月5,351円） |
| §20 | 実行ロードマップ（Phase 1〜3）**（Phase 2に2-9〜2-14を追加・v3.3）** |
| §21 | 検証基準（**Phase 2完了条件に4項目追加・v3.3**） |

---

## 5. 次セッション開始時の最初の指示

次のセッションで最初に以下を実行してください。

```
このセッションではNorth Star OS v3のn8nワークフロー構築を行います。

プロジェクトナレッジに以下がアップロード済みです:
- HANDOVER_NorthStarOS_20260503.md（本引き継ぎ書）
- Architecture_Plan_v3_完全版_20260501.md（マスター設計書・v3.3）
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

## 6. 秋吉AI方式 追加実装計画（2026/05/07追加）

ランサーズ秋吉社長の「秋吉AI」システムから得られた知見をNorthStarOSに適用した追加実装計画。秋吉AIの本質は「CEOの意思決定パターンをAIに学習させ、会議コストを削減しながら経営の質を上げる」ことであり、BUN社長の一人経営においても同じ原理が有効。

### 追加する機能と設計思想

#### 高優先度 A: BUN社長デジタルクローン（§6に追加済み）

COOのシステムプロンプトにBUN社長の意思決定パターン（事業判断3基準・行動パターン・優先順位軸）を詳細に組み込む。各部門がBUN社長に確認を取る前にCOOが仮回答を生成し、エスカレーション件数を大幅に削減する。

**n8nへの実装:** COOを呼び出す全HTTPノードのシステムプロンプトに「BUN社長デジタルクローン原則」セクションを参照・埋め込む。Phase 2-11で精度検証を実施。

#### 高優先度 B: LINE会話自動記録化（§16・§15に追加済み）

BUN社長とCOOボットのLINEやり取りを自動でSignal DBに蓄積する。テキスト会話は音声より処理精度が高く、使うほど精度が上がるポジティブループが生まれる。

**n8nフロー設計:**
```
LINE Webhook受信
    ↓
Gemini 2.5 Flash（「経営・意思決定・事業に関係するか」判定）
    ↓ Yes
Google Drive / Reports / BizDev / Signal_DB.csv に追記
（日時・ソース=LINE・ランク・本文・アクション状態=未対応）
    ↓
（毎週日曜4:00）週次クラスタリング → Story DB昇格候補をLINEで社長に提案
```

**実装タスク:** Phase 2-13

#### 高優先度 C: 会議前ブリーフィング（§16・§15に追加済み）

Googleカレンダーに新規ミーティングが登録された際、COOが関連Story DBを検索して「過去の類似ケースと推奨アクション」を会議30分前にLINEで届ける。

**n8nフロー設計:**
```
Google Calendar 新規イベント作成 Webhook
    ↓
イベントタイトル・説明文を抽出
    ↓
Claude Sonnet 4.6（Story_DB.md + Signal_DB.csv を参照して会議ブリーフ生成）
    ↓
GPT-4o mini（QA）
    ↓
LINE Messaging API（会議30分前にスケジュール送信）
```

**実装タスク:** Phase 2-12

#### 中優先度 D: Signal DB構造化（§10に追加済み）

既存のシグナル検知フロー（毎朝7:00ブリーフィング内）の出力をLINE通知に加え、Google DriveのSignal_DB.csvにも同時書き込みするよう拡張する。1日50件・週400件規模で蓄積し、Story DBの材料とする。

**実装タスク:** Phase 2-9

#### 中優先度 E: リアルタイム戦略更新フロー（§16・§15に追加済み）

失注・受注・顧客からの重要連絡など、事業に影響するイベントをBUN社長がLINEでCOOに報告した際に、Claude Opusが即座に戦略的影響を評価して結果を返す。

**n8nフロー設計:**
```
BUN社長がLINEで「[戦略評価]○○社から失注」等を送信
    ↓
LINE Webhook → テキスト抽出
    ↓
Claude Opus 4.6（事業戦略への影響評価・Story DB参照・推奨アクション生成）
    ↓
GPT-4o mini（QA）
    ↓
LINE即時返信 + Google Drive / Reports / BizDev / StrategyUpdate_YYYYMMDD.md 保存
    ↓
Signal DBにも記録（ランクS/A）
```

**実装タスク:** Phase 2-14

### Story_DB.md 初期テンプレート（Phase 2-10用）

BUN社長がPhase 2-10で手動入力する際のフォーマット。GitHubの Story_DB.md として保存する。

```markdown
# BUN社長 Story DB

## S001: [ストーリータイトル]
- 期間: YYYY/MM〜YYYY/MM
- 登場人物: 
- 経緯: 
- 結果: 
- 成功/失敗: 
- 再現性: 
- 関連シグナルID: 
```

### 秋吉AI方式から得た設計思想（重要）

1. **経営者自身がAIにロジックを食わせる** → BUN社長がStory DBに自ら入力することで、外部エンジニアが作るより精度が高いシステムになる
2. **点（シグナル）を線（ストーリー）に変換する** → Signal DBだけでは足りない。時間軸でつないでパターン化することで予測力が生まれる
3. **使うほど賢くなるループを設計する** → LINE会話が増える → Signal DB充実 → Story DB充実 → COO精度向上 → BUN社長の確認コスト減 → さらにLINEを使う好循環

---

**「ALIGN FIRST. Then Take Massive Action.」**
**「手抜きをしない。網羅する。魂を込める。」**

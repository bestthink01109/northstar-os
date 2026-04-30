# n8n構築 実行計画書（ワンオペ完全版）修正版

# North Star OS v3 — Phase 2 実装ロードマップ

# 作成日: 2026/04/13（修正: 同日）

# 作成者: COO AI（Claude）

-----

## 0. 本計画の位置づけ

本計画は、Architecture Plan（North Star OS v3 最終確定版）のPhase 2「n8n + サブエージェント構築」を、BUN_CEO一人で実行するための具体的手順書である。

前提条件:

- Phase 1（手動運用）は並行継続。本計画の作業がPhase 1の代行業務を妨げないよう、作業時間を明確に区切る
- 作業可能時間: 平日の代行業務終了後（19:30以降）+ 週末の空き時間
- 技術サポート: Claude（claude.ai / Cursor）が全手順をリアルタイムで伴走する
- 投資上限: 月額2,000円以内（VPS代）。AI APIコストは別枠（既存予算$50〜120/月）

選定結果:

- オーケストレーションツール: n8n（セルフホスト版・Community Edition）
- 選定理由: AI APIマルチモデル接続のネイティブ対応、実行回数無制限、外販時のバックエンド転用可能、月$5〜10のVPS代のみ

-----

## 0-A. マルチモデルAI配置表（Architecture Planより転記・n8n実装対応）

本計画の全ワークフローで使用するAIモデルは以下の通り。n8n上では各モデルをHTTP Requestノードまたは専用ノードで接続する。

|ステップ             |担当AI                 |コスト(入/出 per 1M tokens)|n8n接続方式                    |選定理由                |
|:----------------|:--------------------|:---------------------|:--------------------------|:-------------------|
|PM（通常仕様策定・PRD生成） |Claude Sonnet 4.6    |$3 / $15              |HTTP Request（Anthropic API）|PRD生成・ロジック検証。十分な推論力 |
|PM（法規制・事業判断）     |Claude Opus 4.6      |$5 / $25              |HTTP Request（Anthropic API）|妥協不可の高度判断。自動ルーティング  |
|開発（スクリプト/文書/帳票）  |DeepSeek V3.2        |$0.14 / $0.28         |HTTP Request（DeepSeek API） |PRDがあれば品質十分。コスト1/20 |
|開発（プロダクトコード）     |Cursor + Claude      |Cursor Pro内           |n8n外（CEOがCursorで実行）        |精密なビジネスロジック実装。追加コスト0|
|開発（デモ用プロトタイプ）    |Lovable              |月$20〜50               |n8n外（必要時のみ手動起動）            |営業提案時の使い捨てデモ専用      |
|事業開発（市場スキャン）     |Gemini 2.5 Flash     |$0.30 / $2.50         |HTTP Request（Google AI API）|Web検索統合。大量情報の低コスト処理 |
|事業開発（事業判断）       |Claude Opus 4.6      |$5 / $25              |HTTP Request（Anthropic API）|「飯のたねになるか」の判断は最高品質  |
|リサーチ巡回（7ターゲット解析） |Gemini 2.5 Flash     |$0.30 / $2.50         |HTTP Request（Google AI API）|Web検索+要約。コスト効率最優先   |
|QA（全パイプライン共通）    |GPT-5.4 mini         |$0.75 / $4.50         |OpenAIノード（n8nネイティブ）        |別プロバイダで盲点補完。統一管理    |
|定型処理（朝ブリーフィング・通知）|Gemini 2.5 Flash-Lite|$0.10 / $0.40         |HTTP Request（Google AI API）|最安。大量定型処理           |

月間コスト推定（1日平均3PJ並列）: 約$50〜120/月（約7,500〜18,000円）

モデルルーティングの原則:

- 通常のPM判断 → Claude Sonnet 4.6
- 法規制（処遇改善加算・介護報酬等）または事業のGo/No-Go判断 → Claude Opus 4.6に自動昇格
- ルーチンのコード/文書/帳票生成 → DeepSeek V3.2（コスト1/20）
- 大量テキスト処理・Web検索 → Gemini 2.5 Flash
- 定型処理（巡回・通知・要約） → Gemini 2.5 Flash-Lite
- QAは必ずGPT-5.4 mini（全パイプライン共通。PMや実行とは別プロバイダにすることで盲点を補完）

-----

## 0-B. QA必須ルール（全パイプライン共通）

Architecture Planの共通構造「PM → 実行 → QA → CEO承認 → 出力」に基づき、n8n上の全パイプラインに以下のQAノードを必須で組み込む。

QA担当AI: GPT-5.4 mini（OpenAI API）— 全パイプライン統一

QAノードの標準プロンプト:

```
あなたはQA（品質保証）担当AIです。
以下の「PRD（要求仕様）」と「成果物」を照合し、品質を検証してください。

検証項目:
1. PRDの要求事項が全て満たされているか（漏れチェック）
2. 事実関係に誤りがないか（数値・日付・法令名等）
3. 日本語の正確性（誤字脱字・不自然な表現）
4. エビデンス・出典URLが明記されているか（リサーチ系の場合）
5. 当社ポリシー「手抜きをしない。網羅する。魂を込める。」に照らして不十分な点

出力形式:
- 合否判定: PASS / FAIL
- 指摘事項（FAILの場合）: 具体的な修正箇所と理由
- リスク指摘（PASSの場合でも）: 気づいた点があれば記載
```

QAの適用範囲（例外なし）:

|パイプライン        |QA対象              |QA後のフロー                         |
|:-------------|:-----------------|:-------------------------------|
|[DEV]         |PRD、生成コード、生成文書    |QA PASS → CEO承認 → GitHub/Drive保存|
|[BizDev]      |市場スキャン結果、事業機会レポート |QA PASS → CEO承認 → Drive保存       |
|[RSC]         |リサーチ巡回結果（7ターゲット全て）|QA PASS → ダッシュボードに自動反映          |
|[FIN]         |月次開発費レポート         |QA PASS → CEO承認 → Drive保存       |
|[MKT]（Phase 3）|マーケティング資料・配信原稿    |QA PASS → CEO承認 → 配信実行          |
|朝ブリーフィング      |ダッシュボード全体         |QA PASS → LINE通知 + Drive保存      |
|夕リフレクション      |リフレクション要約         |QA PASS → LINE通知 + Dashboard更新  |

重要: QAがFAILを返した場合、n8nは自動的に実行AIに差し戻し（1回リトライ）。2回目もFAILの場合はCEOにLINE通知「QA不合格: [パイプライン名] 手動確認が必要です」を送信し、処理を一時停止する。

-----

## 1. 全体スケジュール（4週間）

|週     |期間       |テーマ                                 |成果物                           |
|:-----|:--------|:-----------------------------------|:-----------------------------|
|Week 1|4/14〜4/20|VPS契約 + n8nセットアップ + 動作確認            |n8nがブラウザからアクセス可能になる           |
|Week 2|4/21〜4/27|[RSC]巡回自動化 + 朝7:00ダッシュボード統合ブリーフィング構築|リサーチ結果が組み込まれたダッシュボードが毎朝届く     |
|Week 3|4/28〜5/04|夕19:00リフレクション + CEO承認フロー構築          |夕方LINE通知 + LINEワンタップ承認が動作     |
|Week 4|5/05〜5/11|[DEV]/[FIN]/[BizDev]パイプライン基盤構築      |全パイプラインが「PM→実行→QA→CEO承認→出力」で稼働|

重要: 各週の作業量は「平日夜1時間 × 3日 + 週末2〜3時間」を想定。代行業務を圧迫しない設計。

-----

## 2. Week 1: VPS契約 + n8nセットアップ（4/14〜4/20）

### 2-1. VPS契約（所要時間: 30分）

推奨VPSプロバイダ（日本リージョン優先）:

|プロバイダ      |プラン          |スペック                       |月額          |備考                      |
|:----------|:------------|:--------------------------|:-----------|:-----------------------|
|ConoHa VPS |2GBプラン       |3vCPU / 2GB RAM / 100GB SSD|約1,848円     |日本リージョン。管理画面が日本語。初心者に最適 |
|Xserver VPS|2GBプラン       |3vCPU / 2GB RAM / 50GB SSD |約1,150円     |日本リージョン。コスト最安クラス        |
|Vultr      |Cloud Compute|1vCPU / 2GB RAM / 50GB SSD |$12（約1,800円）|東京リージョンあり。Docker公式イメージあり|

推奨: ConoHa VPS 2GBプラン（日本語サポート + 十分なスペック + 安定性）

契約時の設定:

- OS: Ubuntu 24.04 LTS
- リージョン: 東京
- SSH鍵認証を設定（パスワード認証は無効化する）
- ルートパスワードは1Passwordに保管

### 2-2. サーバー初期設定（所要時間: 1時間）

以下の手順はClaudeが一行ずつ指示する。社長はターミナル（Macの標準ターミナル）にコピペするだけ。

ステップ1: SSHでVPSに接続

```
ssh root@[VPSのIPアドレス]
```

ステップ2: セキュリティ基本設定

```
# システム更新
apt update && apt upgrade -y

# 作業用ユーザー作成（rootで直接作業しない）
adduser bunceo
usermod -aG sudo bunceo

# SSH鍵をコピー
mkdir -p /home/bunceo/.ssh
cp /root/.ssh/authorized_keys /home/bunceo/.ssh/
chown -R bunceo:bunceo /home/bunceo/.ssh

# ファイアウォール設定
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

ステップ3: Docker + Docker Composeインストール

```
# Docker公式インストール
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# bunceoユーザーにDocker権限付与
usermod -aG docker bunceo

# Docker Compose（V2は同梱済み。確認のみ）
docker compose version
```

### 2-3. n8nインストール（所要時間: 30分）

ステップ1: ディレクトリ作成

```
# bunceoユーザーに切替
su - bunceo

# n8n用ディレクトリ
mkdir -p ~/n8n-docker
cd ~/n8n-docker
```

ステップ2: docker-compose.yml作成

```yaml
# ~/n8n-docker/docker-compose.yml
version: '3.8'

services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    container_name: n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=n8n.[社長のドメイン or VPSのIPアドレス]
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - NODE_ENV=production
      - WEBHOOK_URL=https://n8n.[社長のドメイン]/
      - GENERIC_TIMEZONE=Asia/Tokyo
      - TZ=Asia/Tokyo
      # セキュリティ: 基本認証
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=bunceo
      - N8N_BASIC_AUTH_PASSWORD=[強力なパスワード]
    volumes:
      - n8n_data:/home/node/.n8n

  # リバースプロキシ（SSL自動取得）
  caddy:
    image: caddy:2
    container_name: caddy
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config

volumes:
  n8n_data:
  caddy_data:
  caddy_config:
```

ステップ3: Caddyfile作成（SSL自動化）

```
# ~/n8n-docker/Caddyfile
n8n.[社長のドメイン] {
    reverse_proxy n8n:5678
}
```

注: ドメインがない場合はIPアドレス直接アクセス（http://[IP]:5678）で仮運用開始可能。ドメイン+SSLは後日追加。

ステップ4: 起動

```
cd ~/n8n-docker
docker compose up -d
```

ステップ5: 動作確認

- ブラウザで https://n8n.[ドメイン] または http://[IP]:5678 にアクセス
- 基本認証でログイン
- n8nのセットアップウィザードが表示されれば成功

### 2-4. API認証情報の事前登録（所要時間: 45分）

n8n起動後、全パイプラインで使用するAPI認証情報を「Credentials」として一括登録する。

|# |サービス                              |n8n Credential種別 |取得先                           |用途                   |
|:-|:---------------------------------|:----------------|:-----------------------------|:--------------------|
|1 |Google（Calendar/Drive/Sheets）     |Google OAuth2    |Google Cloud Console          |予定・タスク取得、ファイル保存、台帳管理 |
|2 |Anthropic（Claude Sonnet/Opus）     |Header Auth      |https://console.anthropic.com/|PM層（PRD生成・事業判断）      |
|3 |Google AI（Gemini Flash/Flash-Lite）|Header Auth      |https://aistudio.google.com/  |リサーチ巡回・ブリーフィング・市場スキャン|
|4 |DeepSeek                          |Header Auth      |https://platform.deepseek.com/|スクリプト/文書/帳票生成        |
|5 |OpenAI（GPT-5.4 mini）              |OpenAI Credential|https://platform.openai.com/  |QA（全パイプライン共通）        |
|6 |LINE Notify                       |Header Auth      |https://notify-bot.line.me/   |全通知・承認依頼             |

### 2-5. Week 1 完了条件チェックリスト

- [ ] VPSが契約済みでSSH接続できる
- [ ] Dockerが動作している
- [ ] n8nにブラウザからアクセスできる
- [ ] 基本認証でログインできる
- [ ] 上記6つのAPI認証情報がn8nに登録済み
- [ ] テストワークフロー（手動トリガー → Gemini Flash-Lite API呼出 → 「Hello BUN_CEO」応答確認）が動作する

-----

## 3. Week 2: [RSC]巡回自動化 + 朝ダッシュボード統合ブリーフィング（4/21〜4/27）

### 3-0. 朝のフロー全体像（Architecture Plan準拠）

Architecture Planのダッシュボード構成（Layer 4）に忠実に再現する。朝の自動処理は以下の順序で実行される:

```
06:00 [RSC巡回ワークフロー起動]
  │
  ├→ 7ターゲット巡回（HTTP Request × 7）
  │     実行AI: n8nのHTTP Requestノード（ページ取得のみ。AIは不使用）
  │
  ├→ 巡回結果の解析・フォーマット整形（× 7並列）
  │     実行AI: Gemini 2.5 Flash（各ページの内容解析・URL抽出・要約）
  │
  ├→ QAチェック（巡回結果の事実確認・URL有効性・漏れチェック）
  │     QA AI: GPT-5.4 mini
  │     判定: PASS → 次へ / FAIL → Gemini Flashに差戻（1回リトライ）
  │
  ├→ 各リサーチファイルをGoogle Driveに保存
  │     - FUKUOKA/福岡県庁トレンドリポート_YYYYMMDD.md
  │     - KUMAMOTO/熊本県庁トレンドリポート_YYYYMMDD.md
  │     - MHLW/厚労省障害_YYYYMMDD.md
  │     - MHLW/厚労省介護_YYYYMMDD.md
  │     - MHLW/WAMNET障害_YYYYMMDD.md
  │     - MHLW/WAMNET介護_YYYYMMDD.md
  │     - AI/AIトレンド_YYYYMMDD.md
  │
  ▼
06:50 [RSC巡回完了 → 結果をダッシュボード統合ワークフローに引き渡し]
  │
  ▼
07:00 [朝ダッシュボード統合ブリーフィング ワークフロー起動]
  │
  ├→ Section 1: Core Vision（固定テンプレート。変更がある場合のみCEOが対話で修正）
  │
  ├→ Section 2: Today's Schedule & Tasks（全件）
  │     データ取得: Google Calendar API（予定 + タスク）
  │
  ├→ Section 3: 1-Week All（全予定・全タスク）
  │     データ取得: Google Calendar API（7日分）
  │
  ├→ Section 4: Research Facts（★ここにRSC巡回結果を統合）
  │     データ取得: 06:50に完了したRSC巡回結果を受け取り
  │     各ターゲットの要約 + 提言 + 詳細ファイルへのリンクを掲載
  │
  ├→ Section 5: AI Task Workspace（進行中プロジェクト一覧）
  │     データ取得: Google Drive内のプロジェクト管理ファイル
  │
  ├→ Section 6: PM Strategy Report（決断の書）— 空欄。朝の対話で確定
  │
  ├→ Section 7: Reflection — 空欄。夕方に記入
  │
  ▼
[ダッシュボード全体の統合・整形]
  実行AI: Gemini 2.5 Flash-Lite（Section 1〜7を統合してMarkdown整形）
  │
  ▼
[QAチェック（ダッシュボード全体）]
  QA AI: GPT-5.4 mini
  検証: 予定・タスクの抜け漏れ、リサーチ結果の整合性、日付の正確性
  │
  ▼
[QA PASS]
  │
  ├→ Google Drive: Dashboard_YYYYMMDD.md として保存
  ├→ LINE Notify: ダッシュボード要約を通知
  │     「おはようございます、BUN社長。本日のダッシュボードが完成しました。
  │      [優先タスク1] [優先タスク2] [優先タスク3]
  │      リサーチ新着: ○件（福岡○件、熊本○件、厚労省○件、AI○件）」
  │
  ▼
[CEOがDashboardを確認 → Cursor/claude.aiでAIコーチと対話]
  - Core Visionの復唱と確認
  - タスク優先順位の最終決定
  - Section 6「決断の書」の確定
  - 必要に応じてGoogleカレンダーの修正指示
```

### 3-1. [RSC]リサーチ巡回ワークフロー（毎朝6:00起動）

```
[Cronトリガー: 毎朝6:00 JST]
    │
    ▼ 並列実行（n8nのSplit In Batchesノード）
    │
    ├─[ターゲット1: 福岡県庁]──────────────────────────────┐
    │  HTTP Request: https://www.pref.fukuoka.lg.jp/       │
    │  soshiki/4600400/                                     │
    │  ↓                                                    │
    │  Gemini 2.5 Flash: 対象見出し14項目を完全一致で抽出  │
    │  適用ルール: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE  │
    │  ↓                                                    │
    │  QA: GPT-5.4 mini（URL有効性・見出し網羅性チェック）  │
    │  ↓                                                    │
    │  PASS → Google Drive保存                              │
    ├───────────────────────────────────────────────────────┘
    │
    ├─[ターゲット2: 熊本県庁]──────────────────────────────┐
    │  HTTP Request: https://www.pref.kumamoto.jp/          │
    │  soshiki/32/                                          │
    │  ↓                                                    │
    │  Gemini 2.5 Flash: 対象見出し11項目を完全一致で抽出  │
    │  適用ルール: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE  │
    │  ↓                                                    │
    │  QA: GPT-5.4 mini                                     │
    │  ↓                                                    │
    │  PASS → Google Drive保存                              │
    ├───────────────────────────────────────────────────────┘
    │
    ├─[ターゲット3: 厚労省【障害】]────────────────────────┐
    │  HTTP Request: https://www.mhlw.go.jp/stf/            │
    │  seisakunitsuite/bunya/hukushi_kaigo/                 │
    │  shougaishahukushi/index.html                         │
    │  ↓                                                    │
    │  Gemini 2.5 Flash: 過去30日分を全件抽出              │
    │  適用ルール: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE  │
    │  ↓                                                    │
    │  QA: GPT-5.4 mini                                     │
    │  ↓                                                    │
    │  PASS → Google Drive保存                              │
    ├───────────────────────────────────────────────────────┘
    │
    ├─[ターゲット4: 厚労省【介護】]────────────────────────┐
    │  HTTP Request: https://www.mhlw.go.jp/stf/            │
    │  seisakunitsuite/bunya/hukushi_kaigo/                 │
    │  kaigo_koureisha/index.html                           │
    │  ↓                                                    │
    │  Gemini 2.5 Flash: 過去30日分を全件抽出              │
    │  適用ルール: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE  │
    │  ↓                                                    │
    │  QA: GPT-5.4 mini                                     │
    │  ↓                                                    │
    │  PASS → Google Drive保存                              │
    ├───────────────────────────────────────────────────────┘
    │
    ├─[ターゲット5: WAMNET【障害】]────────────────────────┐
    │  HTTP Request: https://www.wam.go.jp/                 │
    │  gyoseiShiryou/rireki?tab=4                           │
    │  ↓                                                    │
    │  Gemini 2.5 Flash: 過去30日分を全件抽出              │
    │  適用ルール: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE  │
    │  ↓                                                    │
    │  QA: GPT-5.4 mini                                     │
    │  ↓                                                    │
    │  PASS → Google Drive保存                              │
    ├───────────────────────────────────────────────────────┘
    │
    ├─[ターゲット6: WAMNET【介護】]────────────────────────┐
    │  HTTP Request: https://www.wam.go.jp/                 │
    │  gyoseiShiryou/rireki?tab=2                           │
    │  ↓                                                    │
    │  Gemini 2.5 Flash: 過去30日分を全件抽出              │
    │  適用ルール: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE  │
    │  ↓                                                    │
    │  QA: GPT-5.4 mini                                     │
    │  ↓                                                    │
    │  PASS → Google Drive保存                              │
    ├───────────────────────────────────────────────────────┘
    │
    ├─[ターゲット7: AIトレンド]────────────────────────────┐
    │  HTTP Request: Google News RSS                        │
    │  (Generative AI Business Automation)                  │
    │  ↓                                                    │
    │  Gemini 2.5 Flash: 今月+先月分を全件抽出             │
    │  適用ルール: URL_EXTRACT_RULE                         │
    │  ↓                                                    │
    │  QA: GPT-5.4 mini                                     │
    │  ↓                                                    │
    │  PASS → Google Drive保存                              │
    ├───────────────────────────────────────────────────────┘
    │
    ▼ 全7ターゲット完了
[巡回結果サマリーを生成]
    実行AI: Gemini 2.5 Flash-Lite
    出力: 各ターゲットの新着件数 + 提言（ダッシュボードSection 4用）
    │
    ▼
[ダッシュボード統合ワークフローに引き渡し]
```

技術的注意点:

- 福岡県庁サイトはJavaScript動的生成の可能性あり。n8nのHTTP Requestでは取得できない場合、n8nのCodeノード内でPuppeteerを実行するか、Browserless.ioと連携する
- 各サイトへのアクセスは5秒以上の間隔を空ける（サーバー負荷軽減・ブロック回避）
- エラー時はリトライ3回 → それでも失敗ならLINE通知「○○の巡回に失敗しました」を送信し、ダッシュボードには「巡回失敗（手動確認要）」と表示

### 3-2. 朝ダッシュボード統合ブリーフィング ワークフロー（毎朝7:00起動）

```
[Cronトリガー: 毎朝7:00 JST]
    │
    ├→ [Google Calendar API] 今日の予定を全件取得
    ├→ [Google Calendar API] 今日のタスクを全件取得（BUN_CEOカレンダー）
    ├→ [Google Calendar API] 1週間の予定を全件取得
    ├→ [Google Calendar API] 1週間のタスクを全件取得
    ├→ [RSC巡回結果] 06:50に完了した巡回サマリーを取得
    ├→ [Google Drive API] AI Task Workspace情報を取得
    │
    ▼
[ダッシュボード統合・整形]
    実行AI: Gemini 2.5 Flash-Lite
    入力: Core Vision（固定テンプレート）+ 全予定・全タスク + RSC巡回結果 + AI Task情報
    出力: Dashboard_YYYYMMDD.md 形式のダッシュボード全文（Section 1〜5を埋め、6・7は空欄）
    │
    ▼
[QAチェック（ダッシュボード全体）]
    QA AI: GPT-5.4 mini
    検証項目:
    - Googleカレンダーの予定・タスクが全件反映されているか（抜け漏れチェック）
    - リサーチ結果のSection 4への統合が正しいか
    - 日付・曜日の正確性
    - タスクの緊急度判定が妥当か
    │
    ├→ PASS: 次へ
    ├→ FAIL: Gemini Flash-Liteに差戻（1回リトライ）→ 2回目FAIL → CEO LINE通知
    │
    ▼
[QA PASS後の出力]
    ├→ Google Drive: Dashboard_YYYYMMDD.md として保存
    ├→ LINE Notify: ダッシュボード要約を通知
```

### 3-3. LINE Notify設定手順

1. https://notify-bot.line.me/ にアクセス
1. LINEアカウントでログイン
1. 「トークンを発行する」をクリック
1. トークン名: 「North Star OS」
1. 通知先: 「1:1でLINE Notifyから通知を受け取る」を選択
1. 発行されたトークンをn8nのCredentialsに登録

n8nでのLINE通知ノード設定:

```
HTTP Request ノード
URL: https://notify-api.line.me/api/notify
Method: POST
Header: Authorization = Bearer [LINE_NOTIFY_TOKEN]
Body (Form): message = [通知本文]
```

### 3-4. Week 2 完了条件チェックリスト

- [ ] 7ターゲットのリサーチ巡回が毎朝6:00に自動実行される
- [ ] 各巡回結果がGPT-5.4 miniのQAを通過してGoogle Driveに保存される
- [ ] 巡回結果がダッシュボードのSection 4（Research Facts）に統合される
- [ ] ダッシュボード全体がGPT-5.4 miniのQAを通過する
- [ ] LINE Notifyでダッシュボード要約が毎朝7:00に届く
- [ ] Google DriveにDashboard_YYYYMMDD.mdが保存される
- [ ] 3営業日連続で全自動実行される（エラーなし）

-----

## 4. Week 3: 夕方リフレクション + CEO承認フロー構築（4/28〜5/04）

### 4-1. 夕方19:00リフレクション ワークフロー

```
[Cronトリガー: 毎日19:00 JST]
    │
    ├→ [Google Calendar API] 今日の予定（完了/未完了ステータス）
    ├→ [Google Calendar API] 今日のタスク（完了/未完了ステータス）
    ├→ [Google Drive API] 朝のDashboard_YYYYMMDD.md読み込み
    │
    ▼
[リフレクション分析・生成]
    実行AI: Gemini 2.5 Flash
    入力: 朝のダッシュボード（計画）+ Googleカレンダーの実績（完了/未完了）
    出力:
      - 今日の達成サマリー（完了タスク一覧）
      - 未完了タスクの持ち越し判断と理由
      - 明日の推奨アクション（最大3つ、理由付き）
      - 「今日の学び」（AIコーチとしてのフィードバック1つ）
    │
    ▼
[QAチェック]
    QA AI: GPT-5.4 mini
    検証: 完了/未完了の分類が正確か、推奨アクションの妥当性
    │
    ├→ PASS: 次へ
    ├→ FAIL: Gemini Flashに差戻（1回リトライ）→ 2回目FAIL → CEO LINE通知
    │
    ▼
[QA PASS後の出力]
    ├→ Google Drive: Dashboard_YYYYMMDD.md のSection 7（Reflection）を更新
    ├→ LINE Notify: リフレクション要約を通知
    │     「お疲れさまです、BUN社長。本日の結果です。
    │      完了: ○件 / 未完了: ○件
    │      明日の最優先: [タスク名]
    │      [詳細はDashboardを確認]」
    │
    ▼
[Googleカレンダー更新]
    完了タスク → カレンダー上で [完了] 表記に変更
    未完了タスク → 翌日以降に持ち越し（CEOの対話確認後に確定）
```

### 4-2. CEO承認フロー（LINE Webhookワンタップ）

全パイプライン共通の「PM → 実行 → QA → CEO承認 → 出力」フローの心臓部。

```
[任意のパイプラインのQA PASS後]
    │
    ▼
[LINE Notify]
    承認依頼メッセージ送信:
    「━━━━━━━━━━━━━━
     [DEV] PRD完成 — QA PASS
     件名: ○○○
     QA結果: PASS（指摘0件）
     
     承認 → [承認用URL]
     差戻 → [差戻用URL]
     ━━━━━━━━━━━━━━」
    │
    ▼
[CEO: LINEでURLをタップ]
    │
    ▼
[n8n Webhook受信]
    ├→ 承認（action=approve） → 次のステップへ自動進行（出力・保存）
    ├→ 差戻（action=reject） → PM層に差戻通知 + CEOにLINE「差戻理由を入力してください」
```

実装方法:

- n8nのWebhookノードで承認用・差戻用の2つのエンドポイントを作成
- 各パイプラインのQA PASS後に、LINE通知で両方のURLを送信
- Webhookは認証付き（トークン埋め込み）でセキュリティ確保

### 4-3. Week 3 完了条件チェックリスト

- [ ] 夕方19:00にリフレクション通知がLINEに届く
- [ ] リフレクションがGPT-5.4 miniのQAを通過している
- [ ] DashboardファイルのSection 7（Reflection）が自動更新される
- [ ] 完了タスクがGoogleカレンダー上で [完了] 表記に変更される
- [ ] LINE Webhook承認フローが動作する（承認タップ → n8n受信 → 次ステップ起動）
- [ ] 差戻フローが動作する（差戻タップ → PM層に通知）
- [ ] 3営業日連続で全自動実行される（エラーなし）

-----

## 5. Week 4: [DEV]/[FIN]/[BizDev]パイプライン基盤構築（5/05〜5/11）

### 5-1. 全パイプライン共通テンプレート

n8n上で全パイプラインが同一構造で動作するサブワークフローテンプレート:

```
[トリガー（Cron / Webhook / 手動）]
    │
    ▼
[PM層]
    通常判断 → Claude Sonnet 4.6（Anthropic API）
    法規制・事業判断 → Claude Opus 4.6（Anthropic API）
    出力: PRD or 要件定義
    │
    ▼
[QA #1: PRDの品質チェック]
    QA AI: GPT-5.4 mini（OpenAI API）
    PASS → CEO承認へ / FAIL → PM層に差戻（1回リトライ）
    │
    ▼
[CEO承認 #1（LINE ワンタップ）]
    │
    ▼
[実行層]
    スクリプト/文書/帳票 → DeepSeek V3.2（DeepSeek API）
    プロダクトコード → CEO LINE通知「Cursorで実装してください」
    市場スキャン → Gemini 2.5 Flash（Google AI API）
    │
    ▼
[QA #2: 成果物の品質チェック]
    QA AI: GPT-5.4 mini（OpenAI API）
    入力: PRD + 成果物
    PASS → CEO承認へ / FAIL → 実行層に差戻（1回リトライ）→ 2回目FAIL → CEO LINE通知
    │
    ▼
[CEO承認 #2（LINE ワンタップ）]
    │
    ▼
[出力・保存]
    Google Drive / GitHub / Supabase（Phase 3以降）
```

### 5-2. [DEV]パイプライン

```
[トリガー: CEO手動指示（LINE or Dashboard入力）]
    │
    ▼
[PM: Claude Sonnet 4.6]
    入力: CEOの指示テキスト
    出力: PRD（Product Requirements Document）
    │
    ▼
[QA #1: GPT-5.4 mini]
    PRDの完全性・実現可能性チェック
    │
    ▼
[CEO承認 #1（LINE ワンタップ）]
    │
    ▼
[実行]
    スクリプト/文書/帳票の場合 → DeepSeek V3.2
    プロダクトコードの場合 → CEO LINE通知「Cursorで実装してください。PRDを添付します」
    │
    ▼
[QA #2: GPT-5.4 mini]
    PRD vs 成果物の照合チェック
    │
    ▼
[CEO承認 #2（LINE ワンタップ）]
    │
    ▼
[出力]
    GitHub Push → Vercel自動デプロイ（プロダクトコードの場合）
    Google Drive保存（文書/帳票の場合）
```

### 5-3. [FIN]パイプライン

```
[Cronトリガー: 毎月1日 9:00 JST]
    │
    ▼
[データ取得]
    Google Sheets API: 開発費管理台帳から当月のデータ取得
    - AI API使用量（各プロバイダ別）
    - VPS費用
    - ドメイン費用
    - その他ツール費用
    │
    ▼
[PM: Claude Sonnet 4.6]
    レポート要件の定義（初回のみ。以降はテンプレート再利用）
    │
    ▼
[実行: DeepSeek V3.2]
    月次レポート生成:
    - 支出サマリー（項目別・前月比）
    - 予算対比（月額2万円以内の基準に対して）
    - コスト最適化提案
    │
    ▼
[QA: GPT-5.4 mini]
    数値の正確性・計算チェック
    │
    ▼
[CEO承認（LINE ワンタップ）]
    │
    ▼
[Google Drive保存]
    FIN/月次開発費レポート_YYYYMM.md
```

### 5-4. [BizDev]パイプライン（毎週月曜自動スキャン）

```
[Cronトリガー: 毎週月曜 8:00 JST]
    │
    ▼
[市場スキャン]
    実行AI: Gemini 2.5 Flash（Web検索統合）
    ├→ 介護・障害福祉の新制度・補助金・トレンドスキャン
    ├→ 同業他社（介護コンサル・SaaS）の新サービスリリース監視
    ├→ 海外の介護DX事例・スタートアップ動向
    ├→ BUN_CEOの経験・スキルセットで参入可能な市場機会（介護に限定しない）
    │
    ▼
[事業判断]
    実行AI: Claude Opus 4.6（Anthropic API）
    「飯のたねになるか」を3つの評価軸で採点:
    1. 市場性（TAMの大きさ・成長率）
    2. 適合性（既存ドメイン知識で参入可能か）
    3. 実現性（ワンオペ + AI + 低コストで構築可能か）
    スコア上位の案だけを「事業機会レポート」として出力
    │
    ▼
[QA: GPT-5.4 mini]
    数値根拠・エビデンスのクロスチェック
    TAM/SAM/SOM推計の妥当性検証
    │
    ├→ PASS: 次へ
    ├→ FAIL: Claude Opusに差戻（1回リトライ）→ 2回目FAIL → CEO LINE通知
    │
    ▼
[CEO承認（LINE ワンタップ）]
    │
    ▼
[出力]
    ├→ Google Drive: BizDev/事業機会レポート_YYYYMMDD.md
    ├→ LINE Notify: 「今週の事業機会レポートが出ました」
    ├→ ダッシュボード: 翌朝のDashboard Section 5（AI Task Workspace）に反映
```

### 5-5. Week 4 完了条件チェックリスト

- [ ] 共通サブワークフローテンプレートが動作する
- [ ] [DEV] PRD自動生成 → QA(GPT-5.4 mini) → CEO承認 → 実行 → QA → CEO承認 → 保存の全フローが動作
- [ ] [FIN] 月次レポートが自動生成され、QA(GPT-5.4 mini)を通過する
- [ ] [BizDev] 週次スキャン(Gemini Flash) → 事業判断(Claude Opus) → QA(GPT-5.4 mini) → CEO承認の全フローが動作
- [ ] 全パイプラインのQA FAIL時に自動差戻 → 2回目FAIL → CEO LINE通知が動作する
- [ ] 全パイプラインのエラー時にLINE通知が届く

-----

## 6. 常駐自動フロー一覧（Architecture Plan準拠）

Week 1〜4完了後に稼働する全自動フローの一覧:

|スケジュール   |ワークフロー名            |実行AI                      |QA AI       |出力先                              |
|:--------|:------------------|:-------------------------|:-----------|:--------------------------------|
|毎朝 6:00  |[RSC]リサーチ巡回（7ターゲット）|Gemini 2.5 Flash          |GPT-5.4 mini|Google Drive + ダッシュボードSection 4  |
|毎朝 7:00  |朝ダッシュボード統合ブリーフィング  |Gemini 2.5 Flash-Lite     |GPT-5.4 mini|Google Drive + LINE通知            |
|毎夕 19:00 |リフレクション            |Gemini 2.5 Flash          |GPT-5.4 mini|Google Drive（Dashboard更新）+ LINE通知|
|毎週月曜 8:00|[BizDev]市場スキャン     |Gemini Flash + Claude Opus|GPT-5.4 mini|Google Drive + LINE通知 + CEO承認    |
|毎月1日 9:00|[FIN]月次開発費集計       |DeepSeek V3.2             |GPT-5.4 mini|Google Drive + CEO承認             |
|毎週日曜 3:00|n8nワークフロー自動バックアップ  |n8n内部API（AIなし）            |なし          |Google Drive                     |
|異常発生時    |アラート通知             |n8nエラーハンドラー（AIなし）         |なし          |LINE通知（即時）                       |

随時起動（CEO指示による）:

|トリガー   |ワークフロー名      |PM AI             |実行AI                     |QA AI       |出力先                          |
|:------|:------------|:-----------------|:------------------------|:-----------|:----------------------------|
|CEO手動指示|[DEV]開発パイプライン|Claude Sonnet/Opus|DeepSeek V3.2 or Cursor通知|GPT-5.4 mini|GitHub/Google Drive + CEO承認×2|
|必要時のみ  |デモ用プロトタイプ    |なし                |Lovable（n8n外・手動起動）       |なし          |Lovable上                     |

-----

## 7. API接続一覧とコスト見積り

### 7-1. n8nに接続するAPI一覧

|# |サービス                        |担当AI/モデル                     |n8n接続方式                         |認証方式                           |取得先                           |
|:-|:---------------------------|:----------------------------|:-------------------------------|:------------------------------|:-----------------------------|
|1 |Google Calendar/Drive/Sheets|─（データ取得のみ）                   |Google Calendar/Drive/Sheets ノード|OAuth2                         |Google Cloud Console          |
|2 |Anthropic API               |Claude Sonnet 4.6 / Opus 4.6 |HTTP Request ノード                |API Key (Header: x-api-key)    |https://console.anthropic.com/|
|3 |Google AI API               |Gemini 2.5 Flash / Flash-Lite|HTTP Request ノード                |API Key (Header)               |https://aistudio.google.com/  |
|4 |DeepSeek API                |DeepSeek V3.2                |HTTP Request ノード                |API Key (Header: Authorization)|https://platform.deepseek.com/|
|5 |OpenAI API                  |GPT-5.4 mini（QA専用）           |OpenAI ノード（n8nネイティブ）            |API Key                        |https://platform.openai.com/  |
|6 |LINE Notify API             |─（通知のみ）                      |HTTP Request ノード                |Bearer Token                   |https://notify-bot.line.me/   |

### 7-2. 月間コスト見積り

|項目                         |月額（税込目安）        |
|:--------------------------|:---------------|
|VPS（ConoHa 2GB）            |約1,848円         |
|ドメイン（任意。年額を月割）             |約100円           |
|Claude Sonnet/Opus API     |約3,000〜8,000円   |
|Gemini Flash/Flash-Lite API|約500〜2,000円     |
|DeepSeek V3.2 API          |約200〜500円       |
|GPT-5.4 mini API（QA専用）     |約1,000〜3,000円   |
|LINE Notify                |0円              |
|Google Workspace（既存）       |既存費用内           |
|合計                         |約6,700〜15,500円/月|

-----

## 8. トラブル対応とバックアップ

### 8-1. n8nがダウンした場合

即時対応:

1. VPSにSSH接続: `ssh bunceo@[IP]`
1. Docker状態確認: `docker ps`
1. n8n再起動: `cd ~/n8n-docker && docker compose restart`
1. ログ確認: `docker logs n8n --tail 100`

復旧しない場合:

1. Docker Compose再構築: `docker compose down && docker compose up -d`
1. それでもダメならClaudeに状況を共有（エラーログをコピペ）

### 8-2. n8nデータの自動バックアップ

```
[Cronトリガー: 毎週日曜 3:00 JST]
    │
    ▼
[n8n API] 全ワークフローをJSON形式でエクスポート
    │
    ▼
[Google Drive] backup/n8n_workflows_YYYYMMDD.json として保存
```

### 8-3. Claude（claude.ai）によるバックアップ運用

n8nが長時間（1時間以上）復旧しない場合:

- 朝の儀式: Claude（claude.ai）でGoogleカレンダーから予定・タスクを取得し、コーチングを実施
- リサーチ巡回: Claude（claude.ai）のWeb検索で手動巡回
- パイプライン: Cursor上で手動PM→実行→QAを実施（Phase 1のフォールバック）

これにより「n8nが落ちても業務は止まらない」体制を維持する。

-----

## 9. Phase 3への橋渡し

Week 4完了後、以下の拡張に進む:

|順序|タスク                        |PM AI        |実行AI           |QA AI       |時期   |
|:-|:--------------------------|:------------|:--------------|:-----------|:----|
|1 |[MKT]パイプライン実装              |Claude Sonnet|DeepSeek V3.2  |GPT-5.4 mini|5月中旬 |
|2 |Supabase東京リージョンにプロダクトDB構築  |Claude Opus  |Cursor + Claude|GPT-5.4 mini|5月下旬 |
|3 |Dify導入検討（外販プロダクトのAIアプリ層として）|Claude Opus  |─              |─           |6月   |
|4 |Webアプリ版ダッシュボード開発           |Claude Sonnet|Cursor + Claude|GPT-5.4 mini|6月〜7月|
|5 |外販向けマルチテナント設計              |Claude Opus  |Cursor + Claude|GPT-5.4 mini|7月   |
|6 |MVP施設2〜3社デモ・フィードバック        |Claude Opus  |Lovable（デモ）    |GPT-5.4 mini|7月〜8月|

Difyについて: 外販プロダクト（音声ケース記録AI、ケアプランAI等）のユーザー向けインターフェース層として、Phase 3でn8n（バックエンド・オーケストレーション）+ Dify（フロントAI・ユーザー体験）の2層構成を検討する。現時点ではn8n単体で十分。

-----

## 10. 実行開始の手順

本日（4/13）以降の具体的なネクストアクション:

1. 本日: 本計画書を確認・承認する
1. 4/14（月）または代行業務の空き時間: VPSを契約する（ConoHa VPS 2GBプラン推奨）
1. VPS契約後: Claudeに「VPS契約完了。IPアドレスは○○○」と伝える
1. Claudeが手順を一つずつ指示 → 社長はターミナルにコピペ → 30分でn8n起動

以降、Week 1〜4の手順を各週の空き時間に実行する。全ステップでClaudeがリアルタイム伴走する。

-----

## 本計画の検証基準（Architecture Planから転記 + 補足）

Phase 2完了条件:

- n8nが朝7:00・夕19:00に5営業日連続エラーなし
- 全パイプラインで「PM → 実行 → QA(GPT-5.4 mini) → CEO承認 → 出力」が例外なく動作
- サブエージェント2つ以上が並列稼働しCEO承認ワンタップで完結
- CEOの実稼働時間3時間以下が週4日以上
- BizDevが毎週月曜に事業機会レポートを自動提出（Gemini Flash → Claude Opus → GPT QA → CEO承認）
- リサーチ巡回7ターゲットが全て自動化済み、かつ結果が朝のダッシュボードSection 4に自動統合
- n8nダウン時のバックアップ運用手順が確立済み
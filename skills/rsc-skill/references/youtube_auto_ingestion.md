# YouTube自動ナレッジ収集パイプライン 設計書
# 更新日: 2026-05-22
# 用途: 6カテゴリ・102キーワードでYouTube動画を自動収集・分析・蓄積する仕組み
# カテゴリ: MKT自動化 / SALES自動化 / AI技術-メーカー / AI技術-実装 / PKM / 新商材探索

---

## 全体アーキテクチャ

```
YouTube Data API v3（週次検索）
    ↓ キーワード×カテゴリで新着動画を取得
品質フィルター（YouTube版BIZ_SCORING）
    ↓ 閾値未満は除外・通知のみ
文字起こし取得（YouTube字幕→Whisper）
    ↓
Claude API で PART1自動分析
    ↓
individual/ フォルダに保存
    ↓
Obsidian + NotebookLM Sourceに追加
    ↓ LINE通知
BUN_CEO確認（任意）
```

---

## 1. 検索カテゴリ × キーワード設定

**合計102キーワード。週次実行で10,200ユニット消費（無料枠70,000/週の15%）。**

---

### カテゴリ1：MKT（マーケティング自動化・バズ手法）｜27キーワード

#### 国内（日本語）

| キーワード | 収集理由 |
|----------|---------|
| SNS自動化 Claude | NS-OS MKT部門の改善 |
| コンテンツマーケティング AI | SNS戦略のアップデート |
| X Twitter 自動投稿 | SNS自動化の最新手法 |
| インスタグラム AI マーケティング | Instagram展開準備 |
| note AI 集客 | note展開準備 |
| マーケティング自動化 n8n | WF設計改善 |
| YouTube マーケティング AI 2026 | 動画マーケ最新 |
| LINE公式 マーケティング 自動化 | LINE Harness改善 |
| ショート動画 AI生成 | リールTikTok対応 |
| SEO AI 記事生成 | コンテンツ量産手法 |
| メールマーケティング 自動化 | アウトリーチ改善 |
| ショート動画 バズ 手法 2026 | 国内バズコンテンツ設計（最新） |
| バズる コンテンツ 作り方 AI | バイラルコンテンツ国内最新 |
| TikTok マーケティング 戦略 | TikTok国内展開 |

#### 海外（英語）

| キーワード | 収集理由 |
|----------|---------|
| Claude Code marketing automation | 海外実装事例取り込み |
| AI content marketing 2026 | 海外バズ手法 |
| viral marketing strategy AI | バズコンテンツ設計 |
| AI video marketing automation | 動画×AI最新 |
| email automation AI 2026 | メール自動化海外 |
| social media AI agent | SNSエージェント最新 |
| content automation workflow | 自動化WF設計 |
| growth hacking AI 2026 | グロースハック最新 |
| AI influencer marketing | インフルエンサー×AI |
| best viral marketing strategy 2026 | 海外で実際にバズった事例（最重要） |
| most effective marketing funnel 2026 | 売れるファネル設計・海外実績 |
| trending marketing hack 2026 | 今バズってる施策の最前線 |
| what's working in marketing 2026 | 実際に効いてる施策（実証済み） |

---

### カテゴリ2：SALES（営業自動化）｜15キーワード

#### 国内（日本語）

| キーワード | 収集理由 |
|----------|---------|
| 営業 AI 自動化 | SALES部門の改善 |
| 介護 営業 顧客獲得 | ターゲット業界特化 |
| LINE 営業 自動化 | LINE Harness改善 |
| 営業リスト 自動生成 AI | リード獲得効率化 |
| 問い合わせ 自動化 AI | 問い合わせ対応改善 |
| CRM AI 活用 | 顧客管理AI化 |
| 商談 AI アシスト | 営業支援自動化 |
| 中小企業 営業 DX | ターゲット企業視点の取り込み |

#### 海外（英語）

| キーワード | 収集理由 |
|----------|---------|
| sales automation AI 2026 | 最新営業自動化 |
| CRM AI integration | 顧客管理AI最新 |
| Playwright scraping sales | SALES Playwright参考 |
| AI cold outreach 2026 | コールドアウトリーチ最新 |
| lead generation AI agent | リード生成エージェント |
| B2B sales AI 2026 | B2B営業最新手法 |
| sales pipeline automation | パイプライン自動化 |

---

### カテゴリ3：AI技術 - メーカー公式・カンファレンス｜13キーワード

#### 国内（日本語）

| キーワード | 収集理由 |
|----------|---------|
| Anthropic Claude 新機能発表 | 最新API追跡（最重要） |
| Google Gemini 新機能 | Antigravity・競合AI追跡 |
| OpenAI 新機能 発表 | 競合AI追跡 |
| AI カンファレンス 2026 日本 | 国内AI動向 |
| 生成AI 最新動向 2026 | トレンド把握 |

#### 海外（英語）

| キーワード | 収集理由 |
|----------|---------|
| Anthropic press conference 2026 | Anthropic公式発表（最重要） |
| Google I/O 2026 AI | Google開発者向け発表 |
| OpenAI DevDay 2026 | OpenAI公式 |
| Meta AI conference 2026 | Meta AI動向 |
| NeurIPS ICML 2026 | 学術カンファ・基礎研究 |
| AI keynote 2026 | 各社基調講演まとめ |
| Claude 4 release | Claude最新版（出たら即収集） |
| Gemini 3 announcement | Gemini最新（Antigravity連動） |

---

### カテゴリ4：AI技術 - 実装・エンジニア向け｜17キーワード

#### 国内（日本語）

| キーワード | 収集理由 |
|----------|---------|
| Claude Code 使い方 | 機能アップデート追跡 |
| AIエージェント 自動化 | NS-OS設計改善 |
| n8n AI workflow 2026 | n8n最新活用法 |
| Claude スキル 設計 | スキル設計改善 |
| MCP server 使い方 | MCP活用拡大 |
| マルチエージェント 設計 | 複数エージェント連携 |
| RAG 実装 日本語 | 検索拡張生成 |
| AIエージェント 設計原則 | 設計ベストプラクティス |

#### 海外（英語）

| キーワード | 収集理由 |
|----------|---------|
| AI agent design 2026 | 設計トレンド最前線 |
| LangGraph tutorial 2026 | グラフ型エージェント |
| multi-agent system Claude | マルチエージェント実装 |
| RAG implementation 2026 | 検索拡張最新 |
| MCP server tutorial | MCPサーバー構築 |
| prompt engineering 2026 | プロンプト最新技術 |
| Claude API best practices | API活用最適化 |
| computer use agent 2026 | PC操作エージェント |
| n8n advanced workflow | n8n高度化手法 |

---

### カテゴリ5：PKM（Obsidian / NotebookLM / 知識管理）｜12キーワード

#### 国内（日本語）

| キーワード | 収集理由 |
|----------|---------|
| Obsidian AI 活用 | Obsidian設計改善 |
| Obsidian Claude 連携 | Claudian設定改善 |
| NotebookLM 活用法 | NotebookLM改善 |
| 第二の脳 構築 | PKM概念の深化 |
| PARA 実践 Obsidian | PARAフォルダ運用改善 |
| ナレッジマネジメント AI | 知識管理改善全般 |

#### 海外（英語）

| キーワード | 収集理由 |
|----------|---------|
| Obsidian AI plugins 2026 | プラグイン最新動向 |
| NotebookLM tips 2026 | NotebookLM最新活用 |
| personal knowledge management AI | PKM全般の最新手法 |
| second brain system 2026 | 知識管理設計トレンド |
| Obsidian workflow automation | Obsidian×自動化連携 |
| AI notes management 2026 | AI×メモ管理最新 |

---

### カテゴリ6：新商材探索（ビジネストレンド・バズ商材・他業界横展開）｜18キーワード

#### 国内（日本語）

| キーワード | 収集理由 |
|----------|---------|
| AI副業 自動化 2026 | 新収益源の探索 |
| スモールビジネス AI 活用 | SME向け提案ネタ |
| 介護テック AI 最新 | 業界テック動向把握 |
| 中小企業 DX 事例 | 顧客企業視点の学び |
| AI SaaS 新サービス 日本 | 新商材候補の発見 |
| 士業 AI 業務効率化 | 横展開ターゲット探索 |
| フランチャイズ AI 活用 | 事業拡大モデル探索 |
| 売れているAIサービス 2026 | 国内で実際に売れてる商材の把握 |
| AIツール 人気 ランキング | 国内人気AIツール動向 |

#### 海外（英語）

| キーワード | 収集理由 |
|----------|---------|
| AI business model 2026 | ビジネスモデル最新 |
| SME automation ROI | 中小企業への費用対効果示唆 |
| healthcare AI automation | ヘルスケア×AI（介護横展開） |
| AI vertical SaaS 2026 | 業種特化SaaSの発見 |
| no-code AI business 2026 | ノーコードAI事業モデル |
| best selling AI product 2026 | 海外で実際に売れてるAI商材（最重要） |
| most profitable AI business 2026 | 高収益AIビジネスモデル・海外実績 |
| trending AI tools 2026 | 今トレンドのAIツール全般 |
| $10k month AI business | 月収1,000万規模のAIビジネス事例 |

---

## 2. 品質フィルター（YouTube版BIZ_SCORING）

各動画を以下の基準で0〜100点評価。**60点以上のみ収集**する。

| 軸 | 評価基準 | 満点 |
|----|---------|-----|
| **関連性** | 6カテゴリ（MKT/SALES/AI-メーカー/AI-実装/PKM/新商材）のいずれかに直接関係するか | 30 |
| **信頼性** | チャンネル登録者1000人以上・再生回数1000回以上 | 20 |
| **鮮度** | 公開から30日以内 | 20 |
| **実用性** | 実装・手順・事例が含まれているか（タイトル・説明から推定） | 20 |
| **時間** | 5〜60分（長すぎず短すぎず） | 10 |

**除外条件（即除外）：**
- 再生回数 500回未満
- 時間 3分未満 or 90分超
- タイトルに「宣伝」「PR」「広告」が含まれる
- 既に収集済みのvideoId

---

## 3. n8n WF設計（YouTube自動収集WF）

### WF基本仕様
- **スケジュール：** 毎週月曜 8:30 JST
- **WF名：** YouTube自動ナレッジ収集
- **出力先：** `/Users/fuminariaksse/youtube-insight/output/individual/`

### ノード構成
```
[週次スケジュール]
    ↓
[キーワードリスト取得（Sheets/Config）]
    ↓
[YouTube Data API v3 検索] ← 各キーワードで最新20件ずつ
    ↓
[重複チェック（既収集IDと照合）]
    ↓
[品質スコアリング（Code Node）]
    ↓ 60点以上
[字幕取得（youtube-transcript-api）]
    ↓
[Claude API：PART1自動分析（カテゴリ別プロンプト）]
    ↓
[ファイル保存（individual/フォルダ）]
    ↓
[収集ログをSheetsに追記]
    ↓
[LINE通知：「今週X本の新着ナレッジを追加しました」]
```

---

## 4. YouTube Data API v3 設定

### APIキー取得手順
1. Google Cloud Console（https://console.cloud.google.com）を開く
2. 「APIとサービス」→「ライブラリ」→「YouTube Data API v3」を有効化
3. 「認証情報」→「APIキーを作成」（OAuth同意画面は不要）
4. APIキーをn8n credentialsに登録

### n8n登録手順
1. n8n → Credentials → Add Credential → 「Header Auth」
2. Name: `YouTube-API-Key`、Value: 取得したAPIキー
3. HTTP Request NodeのQuery Parametersに `key` を設定

### 月間クォータ
- 無料枠：**10,000ユニット/日**（= 70,000ユニット/週）
- 検索1回：100ユニット
- **102キーワード × 100ユニット = 10,200ユニット/週 → 無料枠の15%で余裕あり**
- 将来キーワードを140本に増やしても14,000ユニット/週（1日分繰り越しで吸収可）

---

## 5. Claude API 分析プロンプト（カテゴリ別）

### MKT カテゴリ用プロンプト

```
あなたはノーススター経営サポートのCOO AIです。
以下のYouTube動画の文字起こしを分析し、MKT部門の改善に活かせるインサイトを抽出してください。

## 分析の視点
- NS-OSのMKT部門（SNSコンテンツ生成・PRタイムズスキャン・競合調査）への適用可能性
- 介護・福祉事業者向けマーケティングへの示唆
- ICEスコアで評価した場合の実装優先度

## 出力形式
[動画の主張・結論]（3文以内）
[NS-OS MKT部門への具体的な改善案]（ステップバイステップ）
[ICEスコア]: Impact: /10 Confidence: /10 Ease: /10 → 合計: /30
[優先度]: 今すぐ/次四半期/保留

文字起こし：
{transcript}
```

### SALES カテゴリ用プロンプト

```
あなたはノーススター経営サポートのCOO AIです。
以下のYouTube動画の文字起こしを分析し、SALES部門の改善に活かせるインサイトを抽出してください。

## 分析の視点
- NS-OSのSALES部門（PRタイムズリード管理・Playwright送信・SALES日次レビュー）への適用可能性
- KENZAIサービスの顧客獲得への示唆
- 介護・福祉事業者への営業効率化

## 出力形式
[動画の主張・結論]（3文以内）
[NS-OS SALES部門への具体的な改善案]（ステップバイステップ）
[KENZAIへの適用案]
[ICEスコア]: Impact: /10 Confidence: /10 Ease: /10 → 合計: /30
[優先度]: 今すぐ/次四半期/保留

文字起こし：
{transcript}
```

### AI技術（メーカー・カンファレンス）カテゴリ用プロンプト

```
あなたはノーススター経営サポートのCOO AIです。
以下のYouTube動画（AIメーカー・カンファレンス発信）を分析し、NS-OSへの影響を特定してください。

## 分析の視点
- Anthropic / Google / OpenAI / Meta の新機能・方向性がNS-OSに与える影響
- Claude API・Gemini API・MCP等の仕様変更への対応必要性
- Antigravityを含むCOO体制のアップデート要否

## 出力形式
[発表内容の要点]（3文以内）
[NS-OSへの影響：今すぐ対応必要 / 次四半期 / 監視継続]
[具体的な対応アクション]（あれば）
[ICEスコア]: Impact: /10 Confidence: /10 Ease: /10 → 合計: /30

文字起こし：
{transcript}
```

### AI技術（実装・エンジニア向け）カテゴリ用プロンプト

```
あなたはノーススター経営サポートのCOO AIです。
以下のYouTube動画の文字起こしを分析し、NS-OSの技術改善に活かせるインサイトを抽出してください。

## 分析の視点
- NS-OS（n8n + Claude + VPS）への直接適用可能性
- DEV/RSC/MKT/SALES/FIN/OPSの各部門AI改善への示唆
- コスト削減・速度向上・品質向上のバランス

## 出力形式
[動画の主張・結論]（3文以内）
[NS-OS技術スタックへの具体的な改善案]
[どの部門・WFに影響するか]
[ICEスコア]: Impact: /10 Confidence: /10 Ease: /10 → 合計: /30
[優先度]: 今すぐ/次四半期/保留

文字起こし：
{transcript}
```

### PKM（Obsidian / NotebookLM）カテゴリ用プロンプト

```
あなたはノーススター経営サポートのCOO AIです。
以下のYouTube動画の文字起こしを分析し、NS-OS × Obsidian × NotebookLM の3点連携改善に活かせるインサイトを抽出してください。

## 分析の視点
- Obsidian（Claudian設定・PARAフォルダ・プラグイン）の改善可能性
- NotebookLM活用の深化（質問テンプレート・ソース管理）
- NS-OS全部門のナレッジ蓄積・検索効率向上

## 出力形式
[動画の主張・結論]（3文以内）
[NS-OS×Obsidian×NotebookLM連携への具体的な改善案]
[BUN_CEOの日次ルーティンへの適用可能性]
[ICEスコア]: Impact: /10 Confidence: /10 Ease: /10 → 合計: /30
[優先度]: 今すぐ/次四半期/保留

文字起こし：
{transcript}
```

### 新商材探索（ビジネストレンド・他業界）カテゴリ用プロンプト

```
あなたはノーススター経営サポートのCOO AIです。
以下のYouTube動画の文字起こしを分析し、ノーススターの新商材・事業機会探索に活かせるインサイトを抽出してください。

## 分析の視点
- ノーススターが新たに展開できる商材・サービスの可能性
- 介護・福祉業界以外で横展開できる自動化・AI活用パターン
- 2026〜2027年にかけての市場トレンドと先行事例

## 出力形式
[動画が示す市場機会・トレンド]（3文以内）
[ノーススターが取り組める具体的な新商材・サービス案]
[必要なリソース・パートナー・期間の概算]
[ICEスコア]: Impact: /10 Confidence: /10 Ease: /10 → 合計: /30
[BizDev優先度]: 即探索 / 次四半期検討 / ウォッチリスト

文字起こし：
{transcript}
```

---

## 6. 収集ログ管理（Google Sheets）

全社ボードに「YouTubeナレッジ」シートを追加：

| 列 | 内容 |
|----|------|
| 収集日 | YYYY-MM-DD |
| videoId | YouTube動画ID |
| タイトル | 動画タイトル |
| カテゴリ | MKT / SALES / AI-メーカー / AI-実装 / PKM / 新商材 |
| 品質スコア | 0〜100 |
| 分析状態 | 完了 / 文字起こしのみ / 除外 |
| ファイルパス | individual/フォルダのパス |
| NotebookLM追加 | 済み / 未 |

---

## 7. NotebookLM 自動化（将来）

**現在：** APIが未公開のため手動アップロード
**将来：** NotebookLM APIが公開されたら自動Source追加

**今できる半自動化：**
1. n8nが週次でindividual/フォルダに新着ファイルを保存
2. LINE通知：「新着X本。NotebookLMへのアップロードをお忘れなく」
3. BUN_CEOが月1回まとめてNotebookLMにアップロード

---

## 8. 実装ロードマップ

| フェーズ | 内容 | 工数 | タイミング |
|---------|------|-----|----------|
| **Phase 1** | YouTube APIキー取得 ✅完了 | — | 2026-05-22 完了 |
| **Phase 2** | n8n WF作成（検索→品質フィルター→保存） | 3h | DEVチケット起票済み |
| **Phase 3** | Claude API自動分析ノード追加 | 2h | Phase 2完了後 |
| **Phase 4** | 全社ボードにナレッジシート追加 | 1h | Phase 3完了後 |
| **Phase 5** | NotebookLM API公開後に自動化 | — | API公開待ち |

---

## 更新ルール

- **キーワードは月1回見直しろ**（新ツール・トレンド・AIリリースに合わせて追加/削除）
- **APIクォータは102キーワードで余裕あり（無料枠の15%）**。140本まで増やせる。増やしすぎたら低優先キーワードを月次→隔週に変更して調整しろ
- 品質スコア閾値（60点）は実運用3ヶ月後に見直しろ（低すぎればノイズ増加・高すぎれば収集量不足）
- NotebookLM APIが公開されたら即Phase 5に着手しろ
- AIメーカー（Anthropic/Google/OpenAI）が大型リリースを行ったときはn8n WFを手動トリガーして即収集しろ

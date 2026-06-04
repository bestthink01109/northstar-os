# AI Handoff | NS-OSV2

更新日: 2026-06-05 Claude Code acting COO セッション

## 役割

通常時は `Codex（GPT-5.4）` が NS-OSV2 の COO として振る舞う。
`Claude Code` と `Antigravity` は通常時は担当 role / workstream を進める specialist runner とする。
`Codex` が limit に近い、または limit 到達時のみ、`Claude Code` か `Antigravity` が代行 COO として振る舞う。

**AUDIT Director v1（独立内部監査人）**: 毎週金曜21:03（週次）・毎月最終金曜21:03（月次）にcrontab自動実行。
現在のAUDITプロバイダー: OpenAI（gpt-5.4）。切り替えは `audit-use anthropic / openai / gemini` で可能。
Gemini対応済み（google.genai新API・gemini-2.5-proモデル）。

## セッション開始時の必須手順

1. `Vault/.claude/context/` の固定6ファイルを読む（グローバルではなくVault内が正本）
2. `03_Archives/COO_Context_履歴/` の最新 `COO_Context_*_MAIN_*.md` を読む
3. `01_Areas/COO/ClaudeCode_Handoff_Latest.md` を読む（次にやること・設定済み事項）
4. Board / `AI_Runner_Status_Latest.md` の latest を読む
5. 自分の runner status を `ACTIVE` に更新する
6. 前回の積み残しと今回の最優先を短く要約してから着手する

### CODEX が runner を担当する場合（追加手順）

CODEX がセッション開始時に `Vault/logs/runner_owner.json` を以下の形式で上書きすること:

```json
{
  "owner": "codex",
  "session_start": "YYYY-MM-DDTHH:MM:SS",
  "expires_at": "YYYY-MM-DDTHH:MM:SS",
  "note": "CODEX session active"
}
```

- `expires_at` はセッション想定終了時刻の **+2時間** を目安に設定する
- セッションが延長する場合は `expires_at` を延長更新する
- `expires_at` を過ぎると Claude Code runner が自動復帰する（手動操作不要）
- ファイルパス: `/Users/fuminariaksse/Desktop/NS-OSV2/NS-OSV2-Brain/logs/runner_owner.json`

**Claude Code runner がこのファイルを5分ごとに確認し、自動的に役割を切り替える。**

## セッション終了時の必須手順

1. 固定6ファイルを更新日含め最新化
2. `COO_Context_YYYYMMDD_MAIN_*.md` を新規作成して残す
3. `ClaudeCode_Handoff_Latest.md` を更新（Board実数・次セッション即実行事項）
4. `AI_Runner_Status_Latest.md` を `LIMITED` または `IDLE` に更新
5. remediation_log.md を更新（新規是正事項を追記）
6. 次セッションが最短で再開できる形で残す

## 次セッション即実行事項（優先順）【2026-06-05更新】

### 🔴 最優先1: 商材開発フロー継続（BizDev STEP3 → market_intelligence → BUN_CEO提示）
- BizDev STEP3チケット（20260605_BizDev_market_intelligence_step3_001）がqa/にある
- QAチケットがboard_runner_monitorで自動生成→QA Director実行待ち
- 完了後COO現物確認 → market_intelligence_v1によるTOP5候補の競合マッピング・参入余地評価
- 評価後BUN_CEOに商材候補を提示して方向性を確認

### 🔴 最優先2: MKT人格活用（market_intelligence完了後）
- 市場分析完了後にoffer_strategist_v1 + revenue_operator_v1で商材設計
- gary_vee / direct_response_writerはさらに商材確定後

### 🟡 継続: KENZAI② qa確認
- 0001チケット：業種修正済み（多業種対応）・qa/にある・QAチケット自動生成待ち
- LINE有料プラン（採算OK確認済み）→ QA PASS後にBUN_CEOへ実装フェーズ確認

### 🟡 継続
- 0003 SALES PKG: needs_rework（商材確定後にreusable_frameworks.mdを正しい商品でリライト）
- 0002 RSC見込み客リスト（商材確定後）
- 0004 LINE OAシナリオ（SALES PKG done後）
- YouTube signal: 6/4・6/5分が未生成・WebFetch権限問題継続
- 20260604_0001 OPS障害福祉フォローアップ

## BUN_CEO確認必須事項
- 商材候補のBizDev STEP3完了後に方向性確認（選択肢提示予定）

## 2026-06-05 確定ルール・変更事項

### QAフロー（案B正規）確定
実行完了 → qa/移動
→ board_runner_monitor がQAチケット（dept=QA）自動生成→todo/配置
→ QA Director（Claude Code + qa_director_v1）が実行
→ PASS: qa/に留置・COO承認待ち / FAIL: needs_rework/に移動
→ COO現物確認 → done/移動

- Antigravityはqa/の実行チケットを処理しない（qa/≠dispatch先）
- COOが切るチケットの必須項目: qa_required: true / qa_profile: [type] / output_path:

### 新規追加
- **market_intelligence_v1 PKG**: MKT部門に追加。April Dunford×Clayton Christensen型。競合マッピング・差別化・参入余地評価を担当
- MKT人格6構成: market_intelligence（市場分析）/ offer_strategist（価値提案）/ revenue_operator（ファネル）/ direct_response_writer（コピー）/ gary_vee（SNS）/ jay_abraham（JV）

### board_runner_monitor.sh v2（案B実装済み）
- qa/チケット: dept=QAならQA Director dispatch、それ以外はQAチケット自動生成
- 両方更新済み: ~/Library/Scripts/ + repo/scripts/monitors/

### 商材開発プロセス（確定）
RSC（市場バズ発見・TOB/TOC）→ BizDev（ニーズフィルター）→ market_intelligence（競合・参入余地）→ offer_strategist（商材設計）→ BUN_CEO確認
- 商材ありき禁止・市場→ニーズ→商材の順序厳守
- 三位一体必達: 売上アップ主軸×管理工数削減×コストダウン
- 評価軸: 手離れ×継続性×自動販売×短期販売可能×利益性×原価0or低

## 確立済みシステム（セッション5-7）

- **board_runner_monitor.sh v2**: launchd常駐・案B QA正規フロー実装済み
- **market_intelligence_v1 PKG**: /01_Areas/MKT/persona_packages/market_intelligence_v1/（10ファイル）
- **Runner 自動切り替え**: Vault/logs/runner_owner.json で制御
- **crontab**: AUDITのみ
- **AUDIT Director v1**: crontab独立稼働

## 確立済みルール（セッション3-7確定）

- COO done承認は現物確認必須（QA PASSのゴム印禁止・独立ビジネス判断必須）
- QAフロー: 案B正規（QAチケット自動生成方式）
- 商材開発: 市場→ニーズ→商材の正規順序（商材ありき禁止）
- 「0ベース」= 実績ゼロ・顧客ゼロ・商品ゼロ・看板ゼロの新規立ち上げ会社
- RSC→BizDev→market_intelligence→offer_strategist→BUN_CEO確認の順序厳守

# AI Handoff | NS-OSV2

更新日: 2026-06-05 Claude Code acting COO セッション（第2回・12:05終了）

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

## 次セッション即実行事項（優先順）【2026-06-05 第2回更新】

### 🔴 最優先1: DEVチケット3本の実装確認（Board自動化仕組み）
以下3本がtodo/に入っている。board_runner_monitorが自動dispatchするはず。
- `20260605_0936_DEV_coo_done_script_build_001` → coo_done.sh実装
- `20260605_0936_DEV_done_lane_validator_build_001` → done/バリデーション自動化
- `20260605_0936_DEV_qa_mechanical_check_build_001` → QA機械チェック
完了後COO現物確認 → **これらが稼働してから初めてBoard運用が正常化する**

### 🔴 最優先2: INFRAチケット（RSCパイプライン復旧）
- `20260605_1205_INFRA_rsc_pipeline_restore_001` → 6/3-6/5欠落対処・欠落検知自動化

### 🔴 最優先3: KENZAI② 正規QAフロー実行
- qa/にある（差し戻し済み・業種修正v1.0.1確認済み・QA_PASS記録あり）
- **正規手順**: QA Director再実行（業種修正後の再QA）→ COO現物確認（coo_done.sh使用）→ done/
- LINE有料プラン: BUN_CEO承認済み（月額5,000円〜）

### 🟡 継続: RSC情報源多様化
- `20260605_1205_RSC_multi_source_intelligence_build_001` → YouTube・ニュースレター・ProductHunt等8チャネル

### 🟡 継続
- PILLAR①直近キャッシュ商材: BUN_CEOへの提示未実施（STEP3はqa/差し戻し中）
- 0003 SALES PKG: needs_rework（商材確定後）
- 0002 RSC見込み客リスト（商材確定後）
- 0004 LINE OAシナリオ（SALES PKG done後）
- 20260604_0001 OPS障害福祉フォローアップ

## BUN_CEO確認済み事項（2026-06-05）
- KENZAI② LINE有料プラン: **OK**
- done管理仕組み3本の設計: **OK**
- RSC情報源多様化8チャネル: **OK**
- WebFetch権限: グローバルsettings.jsonに既存（変更不要・確認済み）

## BUN_CEO未確認事項（次セッションで提示必須）
- PILLAR①直近キャッシュ商材の候補選定（STEP3完了後）
- 商材開発の方向性確認（TOB/TOC・優先順位）

## 2026-06-05 確定ルール・変更事項

### QAフロー（案B正規）確定
```
実行完了 → qa/移動
→ board_runner_monitor がQAチケット（dept=QA）自動生成→todo/配置
→ QA Director（Claude Code + qa_director_v1）が実行
→ PASS: qa/に留置・COO承認待ち / FAIL: needs_rework/に移動
→ COO現物確認 → done/移動
```
- Antigravityはqa/の実行チケットを処理しない（qa/≠dispatch先）
- COOが切るチケットの必須項目: `qa_required: true` `qa_profile: [type]` `output_path:`

### 新規追加
- **market_intelligence_v1 PKG**: MKT部門に追加。April Dunford×Clayton Christensen型。競合マッピング・差別化・参入余地評価を担当
- MKT人格6構成: market_intelligence（市場分析）/ offer_strategist（価値提案）/ revenue_operator（ファネル）/ direct_response_writer（コピー）/ gary_vee（SNS）/ jay_abraham（JV）

### board_runner_monitor.sh v2（案B実装済み）
- qa/チケット: dept=QAならQA Director dispatch、それ以外はQAチケット自動生成
- Antigravityへの注記追加: qa/移動≠QA完了・done直接移動禁止
- 両方更新済み: `~/Library/Scripts/` + `repo/scripts/monitors/`

### 商材開発プロセス（確定）
```
RSC（市場バズ発見・TOB/TOC） → BizDev（ニーズフィルター: 売上UP×工数削減×コストダウン）
→ market_intelligence（競合マッピング・参入余地・SOM試算）
→ offer_strategist（Grand Slam Offer設計）→ BUN_CEO確認
```
- 商材ありき禁止・市場→ニーズ→商材の順序厳守
- 三位一体必達: 売上アップ主軸×管理工数削減×コストダウン
- 評価軸: 手離れ×継続性×自動販売×短期販売可能×利益性×原価0or低

## 2026-06-05 第2回セッション 確定事項

### ⚠️ COOの役割定義（2026-05-30確定・再徹底）
**COOは実動禁止。判断・dispatch・承認・報告のみ。**
- 市場調査・分析・レポート執筆は全てサブエージェントにdispatch
- COOが自分で書いた成果物はルール違反

### 会社の2本柱（PILLAR）
```
PILLAR①: キャッシュ生成エンジン（直近）
  評価軸: 手離れ × 継続性 × 自動販売 × 短期販売可能 × 多大な利益 × 原価0/低
  SCALE軸: S(手離れ/自動販売) C(質的担保) A(継続性/多大な利益) L(短期販売可能)

PILLAR②: NS-OS（半年〜1年でフルバージョン上市）
  評価軸: NS-OS開発加速・共通インフラ貢献・検証価値
  E軸のみ: NS-OS進化貢献度
```
- **①でキャッシュを稼ぎながら②を中長期開発する**
- 2つは独立した事業軸（①が②の部品になるわけではない）

### AUDIT RED対応（2026-06-05 週次AUDIT）
以下3本のDEVチケットを起票済み（再発防止仕組み）：

**仕組み①: coo_done.sh（done移動専用スクリプト）**
- `repo/scripts/coo/coo_done.sh`
- COOがdone/に移動する唯一の手段として強制化
- 自動チェック: qa_result=QA_PASSの記録があるか / coo_approved_at未記入確認
- 全PASS後のみ: status=done更新 + coo_approved_at追記 + done/移動
- 手動mvはboardバリデーション（仕組み②）で即検出

**仕組み②: done/バリデーション自動化（board_runner_monitor追加）**
- 5分ごとにdone/を自動スキャン
- status≠done のチケットを検出 → qa/に自動差し戻し + アラートログ
- `validate_done_lane()` 関数をboard_runner_monitor.shに追加

**仕組み③: QA機械チェック（qa_mechanical_check.sh）**
- QA Director実行前に成果物を自動スキャン
- CHECK A: 出典URL（https://）が3件未満 → FAIL（research/strategy/marketプロファイルのみ）
- CHECK B: 禁止ワード（「一般的に」「と思われます」「〜と考えられます」「とされています」）→ FAIL
- CHECK C: 「など」が4件超 → FAIL
- CHECK D: 数値あり・URL0件 → FAIL
- **いずれか1つでもFAIL → QA_FAIL確定・人間判断不可**
- qa_profile=implementationの場合はCHECK A・DをSKIP

### RSC情報源多様化（BUN_CEO承認済み）
チケット: `20260605_1205_RSC_multi_source_intelligence_build_001`（todo/）
- 🔴 CH-1: YouTube（RSS+WebFetch）
- 🔴 CH-2: 海外ニュースレター（ProductHunt/a16z/CBInsights）
- 🔴 CH-3: Product Hunt（新着プロダクト）
- 🟡 CH-4: X/Twitter トレンド
- 🟡 CH-5: VC/投資家レポート（公開資料）
- 🟡 CH-6: LinkedIn（採用情報→事業方向性）
- 🟢 CH-7: 特許データベース（J-PlatPat）
- 🟢 CH-8: 海外カンファレンス資料
理由: ネット検索偏重では他社と同じ情報しか取れない。先行シグナルを取るため。

### WebFetch権限
グローバルsettings.json（~/.claude/settings.json）のallowに既存。変更不要。

## 確立済みシステム（セッション5-8）

- **board_runner_monitor.sh v2**: launchd常駐・案B QA正規フロー実装済み
  - `/bin/bash` にフルディスクアクセス付与済み
  - スクリプト正本: `repo/scripts/monitors/board_runner_monitor.sh`
  - 実行コピー: `~/Library/Scripts/board_runner_monitor.sh`
- **market_intelligence_v1 PKG**: `/01_Areas/MKT/persona_packages/market_intelligence_v1/`（10ファイル）
- **Runner 自動切り替え**: `Vault/logs/runner_owner.json` で制御
- **crontab**: AUDITのみ
- **AUDIT Director v1**: crontab独立稼働

## 確立済みルール（セッション3-8確定）

- COO done承認は現物確認必須（QA PASSのゴム印禁止・独立ビジネス判断必須）
- **done移動は coo_done.sh 経由のみ**（仕組み①稼働後・手動mv禁止）
- QAフロー: 案B正規（QAチケット自動生成方式）
- 商材開発: 市場→ニーズ→商材の正規順序（商材ありき禁止）
- 「0ベース」= 実績ゼロ・顧客ゼロ・商品ゼロ・看板ゼロの新規立ち上げ会社
- RSC→BizDev→market_intelligence→offer_strategist→BUN_CEO確認の順序厳守
- launchd停止: `launchctl unload ~/Library/LaunchAgents/com.northstar.board-runner-monitor.plist`
- launchd再開: `launchctl load ~/Library/LaunchAgents/com.northstar.board-runner-monitor.plist`

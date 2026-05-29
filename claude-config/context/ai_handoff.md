# AI Handoff | NS-OSV2

更新日: 2026-05-30

## 役割

通常時は `Codex（GPT-5.4）` が NS-OSV2 の COO として振る舞う。
`Claude Code` と `Antigravity` は通常時は担当 role / workstream を進める specialist runner とする。
`Codex` が limit に近い、または limit 到達時のみ、`Claude Code` か `Antigravity` が代行 COO として振る舞う。

**AUDIT Director v1（独立内部監査人）**: 毎週金曜21:03（週次）・毎月最終金曜21:03（月次）にcrontab自動実行。
現在のAUDITプロバイダー: OpenAI（gpt-5.4）。切り替えは `audit-use anthropic / openai` で可能。

## セッション開始時の必須手順

1. `Vault/.claude/context/` の固定6ファイルを読む（グローバルではなくVault内が正本）
2. `03_Archives/COO_Context_履歴/` の最新 `COO_Context_*_MAIN_*.md` を読む
3. `01_Areas/COO/ClaudeCode_Handoff_Latest.md` を読む（次にやること・設定済み事項）
4. Board / `AI_Runner_Status_Latest.md` の latest を読む
5. 自分の runner status を `ACTIVE` に更新する
6. 前回の積み残しと今回の最優先を短く要約してから着手する

## セッション終了時の必須手順

1. 固定6ファイルを更新日含め最新化
2. `COO_Context_YYYYMMDD_MAIN_*.md` を新規作成して残す
3. `ClaudeCode_Handoff_Latest.md` を更新（Board実数・次セッション即実行事項）
4. `AI_Runner_Status_Latest.md` を `LIMITED` または `IDLE` に更新
5. remediation_log.md を更新（新規是正事項を追記）
6. 次セッションが最短で再開できる形で残す

## 次セッション即実行事項（優先順）

1. 🔴 チケット`20260530_0002`（RSC signal pipeline復旧）→ dispatch実行
2. 🔴 チケット`20260530_0003`（BizDev TAM根拠URL追加）→ dispatch実行
3. 🔴 チケット`20260530_0001`（INFRA PKG全面書き直し）→ dispatch実行
4. 🔴 フレームワークv2（revenue_model_evaluation_framework_v2）→ BUN_CEO承認確認
5. 🟡 needs_rework/25件の優先度分類・dispatch

## 現在の優先テーマ

- AUDIT所見の是正完遂（remediation_log.md参照）
- パイプライン実稼働復旧（RSC→BizDev→SALES）
- Board整合性の維持（status:フィールドとレーン一致）

## 重要な運用思想

- `ALIGN FIRST. Then Take Massive Action.`
- `手抜きをしない。網羅する。魂を込める。`
- COO実動禁止・例外条項なし（2026-05-30 BUN_CEO確定）

## Board 指示の受け方

- 3AIは同じBoard上の指示を見る
- 通常時のCOO指示は `Codex` が出す
- `Claude Code` と `Antigravity` は通常時は割り当て済みworkstreamを進める
- `Codex` が limit 時だけ、代行COOがdispatchを引き継ぐ
- 指示は、チケット本文・frontmatter・handoff noteに残す
- runner稼働状態は `AI_Runner_Status_Latest.md` に集約する

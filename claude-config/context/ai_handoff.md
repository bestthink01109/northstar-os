# AI Handoff | NS-OSV2

更新日: 2026-05-30 セッション4

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

## セッション終了時の必須手順

1. 固定6ファイルを更新日含め最新化
2. `COO_Context_YYYYMMDD_MAIN_*.md` を新規作成して残す
3. `ClaudeCode_Handoff_Latest.md` を更新（Board実数・次セッション即実行事項）
4. `AI_Runner_Status_Latest.md` を `LIMITED` または `IDLE` に更新
5. remediation_log.md を更新（新規是正事項を追記）
6. 次セッションが最短で再開できる形で残す

## 次セッション即実行事項（優先順）

1. 🔴 **shift_tool YAML全面書き直し**（BUN_CEOから受領した新仕様で）
   - 仕様確認表は ClaudeCode_Handoff_Latest.md に記載
   - シフト時間・スタッフ匿名化・配置ルール・新規スタッフ追加
   - 完了後に動作テスト実行
2. 🔴 **qa/30件のCOO現物確認 → done承認**（board_runner_monitor.shがQA実行中）
3. 🟡 shift_tool 汎用化設計（YAML全面書き直し後に着手）

## 確立済みシステム（セッション4で追加・変更）

- **board_runner_monitor.sh**: launchd常駐稼働中（PID確認済み）。5分ごと全レーン監視。
  - スクリプト正本: `repo/scripts/monitors/board_runner_monitor.sh`
  - 実行コピー: `~/Library/Scripts/board_runner_monitor.sh`（TCC制限回避）
  - **変更時は両方更新が必要**
- **crontab**: AUDITのみ（週次・月次）。ランナー系はboard_runner_monitorに集約済み
- **QA Director v1.1 PKG**: `01_Areas/QA/context_packages/qa_director_v1/`
- **COO Dispatch Agent PKG**: `01_Areas/COO/context_packages/coo_dispatch_agent_v1/`
- **評価フレームワーク v3.0**: SCALE-M（60点+30点=90点満点）
- **shift_tool**: `northstar-os/Development/shift_tool/` にシフト自動作成ツール発見
  - バグ修正済み（weekday_fixed実装・月末チェックバグ・診断改善）
  - セキュリティ修正済み（スタッフ名ハードコード除去・YAML動的読み込み化）
  - **新仕様でYAML全面書き直しが必要（次セッション最優先）**

## 確立済みルール（セッション3-4確定）

- COO done承認は現物確認必須（QA PASSのみでdone移動禁止）
- board_runner_monitor.sh = ランナー本体（crontabに個別登録しない）
- QA Director = QA実行・PASS/FAIL判定のみ。done移動はCOO専権
- shift_tool: 本番利用前にYAML新仕様適用・動作テスト必須

## 現在の優先テーマ

- shift_tool YAML全面書き直し → 動作確認 → BUN_CEO手動作業を解消
- qa/30件のCOO現物確認フロー
- shift_tool 汎用化（他施設展開・商品化の基盤）

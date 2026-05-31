# AI Handoff | NS-OSV2

更新日: 2026-05-31 セッション5

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

1. 🔴 **qa/COO現物確認の完了・done/needs_rework移動**（詳細はClaudeCode_Handoff_Latest.md）
   - PASS確定19件 → done/に移動
   - needs_rework確定6件 → needs_rework/に移動
   - 未確認3件（0004/0005/0007）→ 現物確認してから判定
2. 🔴 **shift_tool: 6月実データYAML作成 → 動作テスト**
   - 3月YAMLは希望休データが実際と異なる可能性あり → 6月の実データで再実施
   - v2 YAMLはconfigs/shift_config_202603_v2.yaml に作成済み（構造は正しい）
   - ソルバー更新済み（backup_only / skip_consecutive_limit 実装済み）
3. 🟡 shift_tool 汎用化設計（6月テスト成功後に着手）

## 確立済みシステム（セッション5で追加・変更）

- **board_runner_monitor.sh**: launchd常駐稼働・TCC問題解決済み
  - `/bin/bash` にフルディスクアクセス付与済み（BUN_CEO操作）
  - qa/30件の検知・QA実行を開始確認済み
  - スクリプト正本: `repo/scripts/monitors/board_runner_monitor.sh`
  - 実行コピー: `~/Library/Scripts/board_runner_monitor.sh`
  - **変更時は両方更新が必要**
- **crontab**: AUDITのみ。ランナー系はboard_runner_monitorに集約済み
- **shift_tool v2**: `configs/shift_config_202603_v2.yaml` 作成済み
  - シフト時間修正済み（A:9-17, B:7-15）
  - スタッフ全匿名化済み
  - backup_only / skip_consecutive_limit をソルバーに実装済み
  - 6月実データで再テスト予定
- **QA Director v1.1 PKG / COO Dispatch Agent PKG**: 稼働中
- **評価フレームワーク v3.0**: SCALE-M（事業構造60点+市場性30点=90点満点）

## 確立済みルール（セッション3-5確定）

- COO done承認は現物確認必須（QA PASSのみでdone移動禁止）
- board_runner_monitor.sh = ランナー本体（crontabに個別登録しない）
- QA Director = QA実行・PASS/FAIL判定のみ。done移動はCOO専権
- shift_tool: 6月実データYAMLで動作確認してから本番利用
- launchd停止: `launchctl unload ~/Library/LaunchAgents/com.northstar.board-runner-monitor.plist`
- launchd再開: `launchctl load ~/Library/LaunchAgents/com.northstar.board-runner-monitor.plist`

## 現在の優先テーマ

- qa/現物確認完了 → board整理（done/needs_rework振り分け）
- shift_tool 6月実データテスト → BUN_CEO手動作業を解消
- shift_tool 汎用化（他施設展開・商品化の基盤）

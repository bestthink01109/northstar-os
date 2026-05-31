# AI Handoff | NS-OSV2

更新日: 2026-06-01 セッション6

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

## 次セッション即実行事項（優先順）

1. 🔴 **needs_rework/6件の再実行依頼** — runner が検知・agents に dispatch
2. 🔴 **shift_tool: 6月実データYAML作成 → 動作テスト**（BUN_CEO から6月データ受領待ち）
3. 🟡 shift_tool 汎用化設計（6月テスト成功後に着手）

## 確立済みシステム（セッション5-6で追加・変更）

- **board_runner_monitor.sh**: launchd常駐稼働・TCC問題解決済み
  - `/bin/bash` にフルディスクアクセス付与済み（BUN_CEO操作）
  - スクリプト正本: `repo/scripts/monitors/board_runner_monitor.sh`
  - 実行コピー: `~/Library/Scripts/board_runner_monitor.sh`
  - **変更時は両方更新が必要**
- **Runner 自動切り替え（Heartbeat ファイル方式）**:
  - ファイル: `Vault/logs/runner_owner.json`
  - CODEX 起動時: `owner: codex` + `expires_at` を設定するだけで自動切り替え
  - expires_at 経過後: Claude Code runner が自動復帰
- **crontab**: AUDITのみ。ランナー系はboard_runner_monitorに集約済み
- **AUDIT Director v1**: crontab独立稼働。Claude Code / CODEX の状態に無関係
- **shift_tool v2**: `configs/shift_config_202603_v2.yaml` 作成済み（6月実データで再テスト予定）
- **QA Director v1.1 PKG / COO Dispatch Agent PKG**: 稼働中
- **評価フレームワーク v3.0**: SCALE-M（事業構造60点+市場性30点=90点満点）

## 確立済みルール（セッション3-6確定）

- COO done承認は現物確認必須（QA PASSのみでdone移動禁止）
- board_runner_monitor.sh = ランナー本体（crontabに個別登録しない）
- QA Director = QA実行・PASS/FAIL判定のみ。done移動はCOO専権
- shift_tool: 6月実データYAMLで動作確認してから本番利用
- launchd停止: `launchctl unload ~/Library/LaunchAgents/com.northstar.board-runner-monitor.plist`
- launchd再開: `launchctl load ~/Library/LaunchAgents/com.northstar.board-runner-monitor.plist`
- **runner 自動切り替え**: `Vault/logs/runner_owner.json` の `owner` と `expires_at` で制御
  - CODEX が runner を持つ → `owner: codex` + `expires_at` を設定
  - expires_at 経過後 → Claude Code runner が自動復帰（手動操作不要）

## 現在の優先テーマ

- needs_rework/6件の再実行 → Board クリーン化
- shift_tool 6月実データテスト → BUN_CEO手動作業を解消
- shift_tool 汎用化（他施設展開・商品化の基盤）
- CODEX 復帰対応: runner_owner.json で自動切り替え済み

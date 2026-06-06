---
# AI Handoff | NorthStar OS
# 更新日: 2026-06-06（done/管理崩壊対処・board_runner修正・CODEX引き継ぎ）
# ※このファイルはセッション終了時にCOOが必ず更新する
---

## 役割

通常時は `Codex（GPT-5.4）` が NS-OSV2 の COO として振る舞う。
`Claude Code` と `Antigravity` は通常時は担当 role / workstream を進める specialist runner とする。
`Codex` が limit に近い、または limit 到達時のみ、`Claude Code` か `Antigravity` が代行 COO として振る舞う。

**AUDIT Director v1（独立内部監査人）**: 毎週金曜21:03（週次）・毎月最終金曜21:03（月次）にcrontab自動実行。

## セッション開始時の必須手順

1. `Vault/.claude/context/` の固定6ファイルを読む（グローバルではなくVault内が正本）
2. `03_Archives/COO_Context_履歴/` の最新 `COO_Context_*_MAIN_*.md` を読む
3. `01_Areas/COO/ClaudeCode_Handoff_Latest.md` を読む（次にやること・設定済み事項）
4. Board / `AI_Runner_Status_Latest.md` の latest を読む
5. 自分の runner status を `ACTIVE` に更新する
6. 前回の積み残しと今回の最優先を短く要約してから着手する

### CODEX が runner を担当する場合（追加手順）

CODEXがセッション開始時に `Vault/logs/runner_owner.json` を以下の形式で上書きすること:

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
- ファイルパス: `/Users/fuminariaksse/Desktop/NS-OSV2/NS-OSV2-Brain/logs/runner_owner.json`

**現在値: owner=codex, expires_at=2099-12-31（2026-06-06設定）**

## セッション終了時の必須手順

1. 固定6ファイルを更新日含め最新化
2. `COO_Context_YYYYMMDD_MAIN_*.md` を新規作成して残す
3. `ClaudeCode_Handoff_Latest.md` を更新（Board実数・次セッション即実行事項）
4. `AI_Runner_Status_Latest.md` を `LIMITED` または `IDLE` に更新
5. remediation_log.md を更新（新規是正事項を追記）
6. 次セッションが最短で再開できる形で残す

## 次セッション即実行事項（優先順）【2026-06-06 更新】

### 🔴 最優先（CODEX引き継ぎ後）
| 優先 | タスク | 状態 | 担当 |
|------|--------|------|------|
| 🔴 | board_runner再起動 `launchctl load ~/Library/LaunchAgents/com.northstar.board-runner-monitor.plist` | 即時 | CODEX |
| 🔴 | coo_done.sh 実装・テスト | todo/待機 | board_runner経由DEV |
| 🔴 | qa_mechanical_check.sh テスト | todo/待機 | board_runner経由DEV |
| 🔴 | done_lane_validator（仕組み②）完了確認 | doing/滞留 | CODEX |
| 🔴 | qa/45件のQA Director処理 | qa/積み | board_runner自動 |
| 🔴 | Barry（Barry-FIN/OPS）理解 | 未着手 | 次COOセッション |

## Board現状（2026-06-06 12:17時点）
- todo: 2件（coo_done.sh, qa_mechanical_check.sh）
- doing: 1件（done_lane_validator）
- qa: 45件（差し戻し36件+既存9件）
- done: 0件（クリーンアップ完了）
- blocked: 2件（0002, 0004）
- archived: 105件
- needs_rework: 1件

## 2026-06-06 確定事項・ナレッジ

### done/管理崩壊と根本原因（2026-06-06 教訓）
- 旧QAバッチが `qa/→done/` 直接移動し、status更新失敗（Bash権限なし）
- coo_done.sh不在のため誰でもdone/に移動できる状態だった
- 122件中36件がstatus=qa/needs_rework/todoのままdone/に混入
- **根本対処**: coo_done.sh（仕組み①）+ done_lane_validator（仕組み②）+ qa_mechanical_check.sh（仕組み③）

### COO実動禁止ルール（2026-06-06 再徹底）
- **COOは実動禁止。判断・dispatch・承認・報告のみ。**
- qa_mechanical_check.shをCOO自身がデバッグ → BUN_CEOに指摘 → 再dispatch
- 違反時は即キャンセルして再dispatch。ルール例外なし。

### board_runner権限問題の解決策（確定）
- **問題**: Agent toolはFleetViewが `--allowedTools mcp__*` のみ設定 → Bash不可
- **解決**: board_runner（claude --print --permission-mode acceptEdits）経由 → Bash可
- **設定済み**: 正本・実行コピー両方に適用済み
- **settings.json**: mv /NS-OSV2/* と rm /tmp/* を追加済み

### done/管理の3本柱（仕組み）
- 仕組み①（coo_done.sh）: QA_PASSを確認してからdone/移動 → `repo/scripts/coo/coo_done.sh`
- 仕組み②（done_lane_validator）: 定期的にdone/内のstatus不整合を検知 → doing/に滞留中
- 仕組み③（qa_mechanical_check.sh）: QA Director実行前の機械チェック → todo/に待機

## runner_owner.json 現状
```json
{
  "owner": "codex",
  "session_start": "2026-06-06T19:10:00",
  "expires_at": "2099-12-31T23:59:59",
  "note": "Codex が COO席を継続保持。Claude Code は COO席ではなく、現時点で specialist 運用にも含めない。"
}
```

## launchd 操作
```bash
# 停止
launchctl unload ~/Library/LaunchAgents/com.northstar.board-runner-monitor.plist
# 再起動
launchctl load ~/Library/LaunchAgents/com.northstar.board-runner-monitor.plist
```

## BUN_CEO確認済み事項（2026-06-06）
- done/全件クリーンアップ: **OK**
- settings.json allowlist拡張（mv NS-OSV2/* / rm /tmp/*）: **OK**
- board_runner --permission-mode acceptEdits 適用: **OK**

## 確立済みシステム

- **board_runner_monitor.sh**: launchd常駐・全レーン監視・`--permission-mode acceptEdits` 適用済み
  - スクリプト正本: `repo/scripts/monitors/board_runner_monitor.sh`
  - 実行コピー: `~/Library/Scripts/board_runner_monitor.sh`
  - **現在停止中（CODEX引き継ぎのため）**

## インフラ・技術メモ
- VPS SSH: ssh root@162.43.78.67 | n8n: http://162.43.78.67:5678 | WF総数: 25本
- バックアップ: GitHub日次（3:00 JST）+ VPS SQLite日次（3:30 JST cron）
- launchd: board_runner停止中（2026-06-06 12:17 launchctl unload済み）
- drive.js認証エラー時: 別セッションでdrive.jsを一度実行→oauth_tokens.json自動更新

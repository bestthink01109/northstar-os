#!/bin/bash
# Codex CLI チケット監視スクリプト（リアルタイムボード同期対応）

set -euo pipefail

TICKETS_WAITING="/root/northstar-os/tickets/waiting"
TICKETS_DONE="/root/northstar-os/tickets/done"
LOG_FILE="/root/northstar/logs/codex_watcher.log"
BOARD_WEBHOOK="http://localhost:5678/webhook/board-sync"
POLL_INTERVAL=30

source /root/.config/northstar/keys.sh

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

process_ticket() {
  local ticket_file="$1"
  local ticket_name=$(basename "$ticket_file")

  log "処理開始: $ticket_name"

  local prompt="以下のチケットに従ってコードをデバッグ・修正してください。
修正後、チケットの「Codex処理ログ」セクションに実施内容を追記してください。

$(cat "$ticket_file")"

  cd /root/northstar-os
  local output
  local exec_status=0
  if output=$(echo "$prompt" | codex exec \
    -c 'approval_policy="never"' \
    -c 'sandbox_permissions=["disk-full-read-access","disk-write-access"]' \
    2>&1); then
    log "✅ 成功: $ticket_name"
    echo -e "\n## Codex処理ログ\n完了: $(date '+%Y-%m-%d %H:%M:%S')\n$output" >> "$ticket_file"

    # Type Bレポート形式で追記（成功時）
    cat >> "$ticket_file" << REPORT

## DEV_レポート（Type B）
- 完了日時: $(date '+%Y-%m-%d %H:%M:%S') JST
- Layer: L3（Codex CLI経由）
- 担当AI: Codex CLI

### 実装概要
$output

### スキル化候補
（次のCOOセッションで評価）

### 完了確認
- [x] 実装完了
- [ ] 本番環境テスト（要手動確認）
REPORT

  else
    exec_status=$?
    log "❌ エラー: $ticket_name -> $output"
    echo -e "\n## Codex処理ログ\nエラー: $(date '+%Y-%m-%d %H:%M:%S')\n$output" >> "$ticket_file"

    # Type Cレポート形式で追記（失敗・デバッグ時）
    cat >> "$ticket_file" << REPORT

## DEBUG_レポート（Type C）
- 対応日時: $(date '+%Y-%m-%d %H:%M:%S') JST
- 担当: Codex CLI

### 実施した対応
$output

### 結果
❌ 失敗（exit code: $exec_status）
REPORT

  fi

  mv "$ticket_file" "$TICKETS_DONE/$ticket_name"
  log "完了移動: $ticket_name -> done/"

  cd /root/northstar-os
  git add -A
  git commit -m "Codex: デバッグ完了 $ticket_name" 2>/dev/null || true
  git push origin main 2>&1 | tee -a "$LOG_FILE" || true

  curl -s -X POST "$BOARD_WEBHOOK" \
    -H "Content-Type: application/json" \
    -d "{\"trigger\":\"codex_done\",\"ticket\":\"$ticket_name\"}" > /dev/null 2>&1 &
}

log "=== Codex Watcher 起動 (interval: ${POLL_INTERVAL}s, リアルタイムボード同期) ==="

while true; do
  for ticket in "$TICKETS_WAITING"/*.md; do
    [ -f "$ticket" ] || continue
    process_ticket "$ticket"
  done
  sleep "$POLL_INTERVAL"
done

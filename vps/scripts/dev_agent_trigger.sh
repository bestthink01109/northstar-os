#!/bin/bash
# L3専用: Python + Claude API で実装コードを生成する（リアルタイムボード同期対応）

TICKET_FILE=$1
REPO=/root/northstar-os
WAITING=$REPO/tickets/waiting
LOG=/root/northstar/logs/dev_agent.log
BOARD_WEBHOOK="http://localhost:5678/webhook/board-sync"

source /root/.config/northstar/keys.sh

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"; }

if [ ! -f "$TICKET_FILE" ]; then
  log "エラー: チケットが見つかりません: $TICKET_FILE"
  exit 1
fi

name=$(basename "$TICKET_FILE")
log "[L3] DEV Agent開始 (Python): $name"

ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  python3 /root/northstar/l3_agent.py "$TICKET_FILE" 2>&1 | tee -a "$LOG"

exit_code=${PIPESTATUS[0]}
log "[L3] DEV Agent終了 (exit: $exit_code): $name"

mv "$TICKET_FILE" "$WAITING/$name"
log "[L3] waiting/ に移動: $name"

curl -s -X POST "$BOARD_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d "{\"trigger\":\"l3_waiting\",\"ticket\":\"$name\"}" > /dev/null 2>&1 &

cd $REPO && git add -A && git commit -m "L3成果物生成: $name" && git push origin main 2>&1 | tee -a "$LOG"

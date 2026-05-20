#!/bin/bash
# GitHub ticketsフォルダを60秒ごとにpullして3層ルーティングするチケットパーサー
# リアルタイム全社ボード同期対応版

REPO=/root/northstar-os
TODO=$REPO/tickets/todo
DOING=$REPO/tickets/doing
WAITING=$REPO/tickets/waiting
DONE=$REPO/tickets/done
LOG=/root/northstar/logs/ticket_puller.log
BOARD_WEBHOOK="http://localhost:5678/webhook/board-sync"

source /root/.config/northstar/keys.sh

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"; }

# チケット状態変化時に全社ボードを即時同期
sync_board() {
  curl -s -X POST "$BOARD_WEBHOOK" \
    -H "Content-Type: application/json" \
    -d "{\"trigger\":\"ticket_$1\",\"ticket\":\"$2\"}" > /dev/null 2>&1 &
}

detect_layer() {
  local file=$1
  local layer=$(grep -m1 'layer:' "$file" | awk '{print $NF}')
  local type=$(grep -m1 'type:' "$file" | awk '{print $NF}')
  local complexity=$(grep -m1 'complexity:' "$file" | awk '{print $NF}')

  if [ "$layer" = 'auto' ] || [ -z "$layer" ]; then
    if [[ "$type" =~ ^(client-bot|new-product)$ ]]; then
      echo 3
    elif [ "$complexity" = 'high' ]; then
      echo 3
    elif [[ "$type" =~ ^(n8n-wf)$ ]] && [ "$complexity" = 'low' ]; then
      echo 1
    else
      echo 2
    fi
  else
    echo "$layer"
  fi
}

handle_layer1() {
  local ticket=$1 name=$(basename "$1")
  log "[L1] テンプレートマッチング: $name"
  if /root/northstar/apply_template.sh "$ticket"; then
    mv "$ticket" "$DONE/$name"
    log "[L1] 完了 → done/: $name"
    cd $REPO && git add -A && git commit -m "L1完了: $name" && git push origin main 2>&1 | tee -a "$LOG"
    sync_board "done" "$name"
  else
    log "[L1→L2] テンプレート不一致 → L2へ: $name"
    handle_layer2 "$ticket"
  fi
}

handle_layer2() {
  local ticket=$1 name=$(basename "$1")
  log "[L2] Claude API差分生成: $name"

  local prompt="$(cat $ticket)

以下の指示に従ってコード・設定を生成してください。
既存構造を壊さず変更・追加が必要な部分のみ出力してください。

出力形式: コードブロックのみ（説明不要）"

  local result=$(echo "$prompt" | claude --print 2>&1)
  local exit_code=$?

  if [ $exit_code -eq 0 ] && [ -n "$result" ]; then
    echo -e "\n## Layer 2 生成結果\n$result" >> "$ticket"
    mv "$ticket" "$DONE/$name"
    log "[L2] 完了 → done/: $name"
    cd $REPO && git add -A && git commit -m "L2完了: $name" && git push origin main 2>&1 | tee -a "$LOG"
    sync_board "done" "$name"
  else
    log "[L2→L3] 生成失敗 → L3へ: $name"
    handle_layer3 "$ticket"
  fi
}

handle_layer3() {
  local ticket=$1 name=$(basename "$1")
  log "[L3] Claude Code DEV Agent起動: $name"
  /root/northstar/dev_agent_trigger.sh "$ticket" >> "$LOG" 2>&1 &
}

log '=== Ticket Puller 起動（3層対応・リアルタイムボード同期）==='

while true; do
  cd $REPO && git pull --quiet origin main 2>&1 | grep -v 'Already up to date' | tee -a "$LOG"

  for ticket in "$TODO"/*.md; do
    [ -f "$ticket" ] || continue
    [ "$(basename $ticket)" = 'README.md' ] && continue

    name=$(basename "$ticket")
    layer=$(detect_layer "$ticket")
    log "チケット検出: $name (Layer $layer)"

    mv "$ticket" "$DOING/$name"
    cd $REPO && git add -A && git commit -m "処理開始(L${layer}): $name" && git push origin main 2>&1 | tee -a "$LOG"
    sync_board "doing" "$name"

    case "$layer" in
      1) handle_layer1 "$DOING/$name" ;;
      2) handle_layer2 "$DOING/$name" ;;
      3) handle_layer3 "$DOING/$name" ;;
      *) log "不明なlayer: $layer → L3にフォールバック"; handle_layer3 "$DOING/$name" ;;
    esac
  done

  sleep 60
done

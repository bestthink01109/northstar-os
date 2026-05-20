#!/bin/bash
# L1テンプレートマッチング・変数置換スクリプト

TICKET_FILE=$1
REPO=/root/northstar-os
TEMPLATE_DIR=$REPO/dev/templates/n8n
LOG=/root/northstar/logs/ticket_puller.log

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"; }

TEMPLATE_NAME=$(grep -m1 'template:' "$TICKET_FILE" | sed 's/.*template:[[:space:]]*//')
TEMPLATE_FILE=$TEMPLATE_DIR/$TEMPLATE_NAME.json

if [ -z "$TEMPLATE_NAME" ] || [ ! -f "$TEMPLATE_FILE" ]; then
  log "[L1] テンプレート不一致: '$TEMPLATE_NAME'"
  exit 1
fi

log "[L1] テンプレートマッチ: $TEMPLATE_NAME"

OUTPUT=$(cat "$TEMPLATE_FILE")

in_vars=0
while IFS= read -r line; do
  if echo "$line" | grep -q '^## vars:'; then
    in_vars=1
    continue
  fi
  if [ $in_vars -eq 1 ]; then
    if echo "$line" | grep -qE '^[[:space:]]+-[[:space:]][A-Za-z_]+:'; then
      KEY=$(echo "$line" | sed 's/.*- //; s/:.*//')
      VAL=$(echo "$line" | sed 's/[^:]*:[[:space:]]*//')
      OUTPUT=$(python3 -c "
import sys
content = '''$OUTPUT'''
print(content.replace('{{$KEY}}', '$VAL'))
" 2>/dev/null || echo "$OUTPUT")
      log "[L1] 変数置換: {{$KEY}} → $VAL"
    elif echo "$line" | grep -qE '^[^[:space:]-]' && [ -n "$line" ]; then
      in_vars=0
    fi
  fi
done < "$TICKET_FILE"

name=$(basename "$TICKET_FILE" .md)
OUTPUT_FILE=$REPO/workspace/${name}_output.json
mkdir -p "$REPO/workspace"
echo "$OUTPUT" > "$OUTPUT_FILE"

echo -e "\n## Layer 1 適用結果\nテンプレート: $TEMPLATE_NAME\n出力: workspace/${name}_output.json" >> "$TICKET_FILE"

log "[L1] 完了: $OUTPUT_FILE"
exit 0

#!/bin/bash
# NS-OS 日次バックアップスクリプト
# 実行タイミング: 毎日 18:30 UTC (3:30 JST) - n8nバックアップWFの30分後
# 対象: n8n SQLite DB（credentials含む）+ ローカルJSONバックアップ

LOG=/root/northstar/logs/backup.log
BACKUP_DIR=/root/backups
DATE=$(date +%Y%m%d)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"; }

mkdir -p "$BACKUP_DIR/n8n" "$BACKUP_DIR/sqlite"
log '=== NS-OS 日次バックアップ開始 ==='

# ① n8n SQLite DB バックアップ（WF定義 + credentials が入っている）
DB_VOL=$(docker inspect $(docker ps -q --filter name=n8n 2>/dev/null) \
  --format '{{range .Mounts}}{{if eq .Destination "/home/node/.n8n"}}{{.Source}}{{end}}{{end}}' 2>/dev/null)

if [ -n "$DB_VOL" ] && [ -f "${DB_VOL}/database.sqlite" ]; then
    cp "${DB_VOL}/database.sqlite" "$BACKUP_DIR/sqlite/n8n_db_${DATE}.sqlite"
    log "✅ SQLite backup: n8n_db_${DATE}.sqlite ($(du -sh "$BACKUP_DIR/sqlite/n8n_db_${DATE}.sqlite" | cut -f1))"
else
    log "⚠️  SQLite DB が見つかりません"
fi

# ② 7日以上前のバックアップを削除（ローテーション）
DELETED_JSON=$(find "$BACKUP_DIR/n8n/" -name 'n8n_backup_*.json' -mtime +7 -delete -print 2>/dev/null | wc -l)
DELETED_DB=$(find "$BACKUP_DIR/sqlite/" -name 'n8n_db_*.sqlite' -mtime +7 -delete -print 2>/dev/null | wc -l)
log "ローテーション: JSON ${DELETED_JSON}件 / SQLite ${DELETED_DB}件 削除"

# ③ 現在のバックアップ数を確認
COUNT_JSON=$(ls "$BACKUP_DIR/n8n/"*.json 2>/dev/null | wc -l)
COUNT_DB=$(ls "$BACKUP_DIR/sqlite/"*.sqlite 2>/dev/null | wc -l)
log "=== 完了: JSONバックアップ ${COUNT_JSON}件 / SQLite ${COUNT_DB}件 ==="

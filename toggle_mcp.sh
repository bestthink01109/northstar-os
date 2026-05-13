#!/bin/bash

# このスクリプトはGoogle CalendarとGoogle DriveのMCPサーバーを切り替えるためのものです。
# システムのツール数制限（最大100個）を回避するために使用します。

CONFIG_PATH="$HOME/.gemini/antigravity/mcp_config.json"
BACKUP_PATH="$HOME/.gemini/antigravity/mcp_config_backup.json"

# バックアップの作成
cp "$CONFIG_PATH" "$BACKUP_PATH"

echo "BUN_CEO、どちらのMCPサーバーを有効にしますか？"
echo "1: Google Calendar (スケジュール管理用)"
echo "2: Google Drive (ファイル操作用 - ツール数が多いため単独で使用)"
read -p "番号を入力してください (1 または 2): " choice

case $choice in
    1)
        cat << 'EOF' > "$CONFIG_PATH"
{
  "mcpServers": {
    "google-calendar": {
      "command": "/Users/fuminariaksse/google-calendar-mcp/bin/npx",
      "args": [
        "-y",
        "@cocal/google-calendar-mcp"
      ],
      "env": {
        "GOOGLE_OAUTH_CREDENTIALS": "/Users/fuminariaksse/.gemini/antigravity/gcp-oauth.keys.json",
        "PATH": "/Users/fuminariaksse/google-calendar-mcp/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
      }
    }
  }
}
EOF
        echo "Google Calendar用の設定を適用しました。"
        ;;
    2)
        cat << 'EOF' > "$CONFIG_PATH"
{
  "mcpServers": {
    "google-drive": {
      "command": "/Users/fuminariaksse/google-calendar-mcp/bin/npx",
      "args": [
        "-y",
        "@piotr-agier/google-drive-mcp",
        "start"
      ],
      "env": {
        "GOOGLE_DRIVE_OAUTH_CREDENTIALS": "/Users/fuminariaksse/.gemini/antigravity/gcp-oauth.keys.json",
        "GOOGLE_OAUTH_CREDENTIALS": "/Users/fuminariaksse/.gemini/antigravity/gcp-oauth.keys.json",
        "GOOGLE_DRIVE_MCP_TOKEN_PATH": "/Users/fuminariaksse/.config/google-drive-mcp/tokens.json",
        "PATH": "/Users/fuminariaksse/google-calendar-mcp/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
      }
    }
  }
}
EOF
        echo "Google Drive用の設定を適用しました。"
        ;;
    *)
        echo "無効な入力です。処理を中止します。"
        exit 1
        ;;
esac

echo "設定が完了しました。Antigravity(AIシステム)を再起動、またはリロードして反映させてください。"

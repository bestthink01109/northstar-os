---
pattern_name: "line_messaging_api"
created: "2026-05-20"
updated: "2026-05-20"
author: "COO"
tags:
  - LINE
  - API
  - n8n
source_reports:
  - "COO_Context_20260520_MAIN.md"
applicable_scene: "n8n WFからLINE Messaging APIでプッシュ通知を送信する場合"
confidence: high
---

# LINE Messaging API 通知パターン

## 概要

n8n WFからBUN_CEOのLINEにプッシュ通知を送信するパターン。
アラート・日次レポート・承認リクエスト等で使用。

## LINE Harness経由の送信

NorthStar OSではCloudflare WorkerベースのLINE Harnessを経由:

```
n8n WF → HTTP Request → LINE Harness → LINE Messaging API → BUN_CEO LINE
```

### HTTP Requestノード設定

```json
{
  "method": "POST",
  "url": "https://northstar-line.bestthink01109.workers.dev/api/push",
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      { "name": "Content-Type", "value": "application/json" },
      { "name": "X-API-Key", "value": "53079982a5df23b73aa5da91c2891eb90b20186b578dc2ed22684bff7f664a7a" }
    ]
  },
  "sendBody": true,
  "specifyBody": "json",
  "jsonBody": {
    "to": "TARGET_USER_ID",
    "messages": [
      {
        "type": "text",
        "text": "{{ $json.messageContent }}"
      }
    ]
  }
}
```

## 直接LINE API送信（Harness不要の場合）

```
URL: https://api.line.me/v2/bot/message/push
Header: Authorization: Bearer {channel_access_token}
```

## メッセージ形式のベストプラクティス

```
🔴 [WF名] エラー発生
─────────────
発生時刻: 2026-05-20 19:00 JST
エラー: [概要]
─────────────
対応: [自動修復済み / COO確認必要]
```

## 注意事項

- LINE Messaging APIの無料枠: 月200通（2026年5月時点）
- メッセージの二重送信に注意（board-sync WFのWebhook実行時はLINE送信をスキップする設計）
- 二重エンコード問題: URLエンコードされた文字列をさらにエンコードしないこと（修正済み）

## 関連パターン

- oauth_unified_pattern: Google OAuth（LINE APIは不要だが参考）
- error_workflow_setup: エラーアラートでLINE送信を使用

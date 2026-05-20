---
pattern_name: "oauth_unified_pattern"
created: "2026-05-20"
updated: "2026-05-20"
author: "COO"
tags:
  - n8n
  - OAuth
  - Drive
  - Sheets
source_reports:
  - "COO_Context_20260520_MAIN.md"
applicable_scene: "n8n WFからGoogle API（Drive/Sheets/Calendar）を使う場合のOAuth token取得"
confidence: high
---

# n8n OAuth統一パターン

## 問題

n8n WFごとに個別のOAuth credential設定を持つと、トークン切れ時に「もぐらたたき」が発生する。
15本以上のWFが個別にOAuthを管理していた時期には、1本直しても別の1本が切れるという事態が頻発した。

## 解決策: 共通OAuth WF方式

全WFが1つの共通WF（Eu3kQaH8vQpJmyqd）からOAuth access_tokenを取得する。

### アーキテクチャ

```
各WF → HTTP Request POST http://localhost:5678/webhook/google-oauth-token
     → レスポンス: { "access_token": "ya29...." }
     → 以降のGoogle API呼び出しで Authorization: Bearer ya29.... を使用
```

### 共通WF側の構成

```
Webhook受信（/webhook/google-oauth-token）
    ↓
Google OAuth2 Credential（refresh_token保持）
    ↓
token取得 → access_token をレスポンスとして返却
```

### 各WF側の実装

```json
{
  "method": "POST",
  "url": "http://localhost:5678/webhook/google-oauth-token",
  "options": {}
}
```

取得したaccess_tokenを後続ノードで使用:
```
Authorization: Bearer {{ $json.access_token }}
```

## 変更が必要な場合

OAuth client_id/client_secretの変更、refresh_tokenの再取得は共通WF（Eu3kQaH8vQpJmyqd）のみ修正すれば全WFに反映される。

## 注意事項

- localhost:5678 はVPS内からの呼び出し限定。外部からはアクセス不可
- access_tokenの有効期限は約1時間。各WF実行のたびに新しいtokenを取得するため問題なし
- 共通WF自体がダウンすると全WFのGoogle API呼び出しが失敗する（SPOFだが、n8n自体のダウンと同義なので許容）

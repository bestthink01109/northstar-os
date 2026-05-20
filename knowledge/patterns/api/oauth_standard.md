# NorthStar OS Google OAuth 共通仕様

## 認証方式の統一ルール（必須）

### 標準: 共通OAuthトークン取得WF経由
すべてのWFでGoogle APIを呼ぶ場合は以下を使用する。

```
POST http://localhost:5678/webhook/google-oauth-token
Body: {"trigger": "shared_oauth"}
Response: {"access_token": "ya29.xxx"}
```

WFへの組み込み方（標準パターン）：
1. "OAuthトークン取得" ノードを追加（HTTP Request）
   - Method: POST
   - URL: http://localhost:5678/webhook/google-oauth-token
   - specifyBody: json
   - jsonBody: {"trigger":"shared_oauth"}
   - options.neverError: true
   - timeout: 5000
2. 以降のGoogle APIノードのAuthorizationヘッダー:
   Authorization: Bearer {{ $('OAuthトークン取得').item.json.access_token }}

### 禁止: ノード参照でIDを使う
❌ 誤: $('sq-token').item.json.access_token
✅ 正: $('OAuthトークン取得').item.json.access_token
※ n8n expressionではノードの「名前」で参照する（IDではない）

### Google Service Account（SA）の使用場面
Google SA credential（ID: Z72mc0LCzm6a777h）は以下の場合のみ使用：
- Drive保存（非OAuth必要なファイル）
- 特定のSheets（SA権限で書き込み可能なシート）

原則として、ユーザーのカレンダー・メインDrive・SheetsへのアクセスはユーザーOAuth経由を使う。

## 共通OAuth WF情報
- WF ID: Eu3kQaH8vQpJmyqd
- スコープ: calendar + drive
- トークン有効期限: 約1時間（自動リフレッシュ）
- OAuthキー変更時: このWF1本のみ修正すればOK

## 既知の問題パターン
- $('NodeID') → 「Referenced node doesn't exist」エラー
- 対策: 必ずノード「名前」で参照、IDで参照しない

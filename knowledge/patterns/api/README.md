# API連携パターン集

NorthStar OSで使用するAPI連携の標準パターン。

---

## パターン1: Google OAuth共通WF経由でのtokenトークン取得

### 概要
各WFが直接OAuthトークンを管理するのではなく、
共通の `Google OAuth Token` WFにHTTPリクエストしてトークンを取得する。

### フロー
1. 各WFの最初に `ユーザーOAuth取得` HTTPノードを配置
2. `POST /webhook/google-oauth-token` にリクエスト
3. レスポンスの `access_token` を後続ノードで使用

### 実装
```javascript
// OAuth取得ノード設定
{
  "method": "POST",
  "url": "http://localhost:5678/webhook/google-oauth-token",
  "sendBody": true,
  "contentType": "json",
  "specifyBody": "json",
  "jsonBody": "{\"trigger\":\"shared_oauth\"}",
  "options": {
    "response": {
      "response": {
        "neverError": true
      }
    },
    "timeout": 5000
  }
}

// 後続ノードでのtoken使用
// Authorization: =Bearer {{ $('ユーザーOAuth取得').item.json.access_token }}
```

### 注意点
- `neverError: true` を設定してOAuth失敗時もWFを継続させる
- timeout は 5000ms（5秒）に設定
- トークンは共通WFで自動リフレッシュされる

### 確認日
2026-05-20

---

## パターン2: GitHub API経由でのファイルコミットパターン

### 概要
n8nからGitHub APIを使ってファイルを直接コミットする方法。
`mcp__github__create_or_update_file` と同等の機能をn8n HTTPノードで実現。

### フロー
1. 既存ファイルのSHAを取得（更新の場合）
2. ファイルコンテンツをBase64エンコード
3. PUT `/repos/{owner}/{repo}/contents/{path}` でコミット

### 実装
```javascript
// コードノードでBase64エンコード
const content = Buffer.from(fileContent).toString('base64');
const body = JSON.stringify({
  message: `update: ${filename} ${date}`,
  content: content,
  sha: existingSha || undefined,  // 新規作成の場合はundefined
  branch: 'main'
});
return [{ json: { body } }];

// HTTP Requestノード
// Method: PUT
// URL: https://api.github.com/repos/bestthink01109/northstar-os/contents/{path}
// Headers:
//   Authorization: token {GITHUB_TOKEN}
//   Content-Type: application/json
//   Accept: application/vnd.github.v3+json
// Body: {{ $json.body }}
```

### 注意点
- ファイル更新時はSHAが必須（GETで先に取得すること）
- コンテンツは必ずBase64エンコードする
- コミットメッセージに日付を含める（ルール準拠）

### 確認日
2026-05-20

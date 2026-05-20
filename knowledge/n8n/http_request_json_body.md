---
pattern_name: "http_request_json_body"
created: "2026-05-20"
updated: "2026-05-20"
author: "COO"
tags:
  - n8n
  - API
  - debug
source_reports:
  - "COO_Context_20260520_MAIN.md"
  - "MKT_PRTIMES_HANDOVER_CONTEXT.md"
applicable_scene: "n8n HTTP Requestノード v4でJSON Bodyを送信する場合"
confidence: high
---

# n8n HTTP Request JSON Body パターン

## 問題

n8n HTTP Requestノード v4でJSON Bodyの指定方法を誤ると「JSON Body not valid JSON」エラーが発生する。
MKT_PRタイムズ WFで長期間このエラーが継続した。

## 根本原因

n8n HTTP Requestノード v4の仕様:
- `specifyBody: "json"` + `jsonBody` が正しい組み合わせ
- `jsonBody` に渡す値の型によって挙動が変わる

## 正しい使い方

### パターン1: jsonBodyにJSON文字列を渡す場合

```javascript
// Code nodeで作成
const body = JSON.stringify({
  model: "claude-sonnet-4-20250514",
  max_tokens: 4096,
  messages: [{ role: "user", content: prompt }]
});
return { json: { requestBody: body } };
```

HTTP Requestノード設定:
```json
{
  "method": "POST",
  "url": "https://api.anthropic.com/v1/messages",
  "sendBody": true,
  "specifyBody": "json",
  "jsonBody": "={{ $json.requestBody }}"
}
```

n8nの挙動: jsonBodyが文字列 → `JSON.parse()` してからHTTP送信

### パターン2: jsonBodyにオブジェクトを渡す場合

```json
{
  "jsonBody": {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 4096
  }
}
```

n8nの挙動: jsonBodyがオブジェクト → そのままHTTP送信

## やってはいけないこと

### NG: 二重JSON.stringify

```javascript
// Code node
const body = JSON.stringify({ model: "claude-sonnet-4-20250514" });
return { json: { requestBody: body } };

// HTTP Request node
// jsonBody: JSON.stringify($json.requestBody)  ← これはNG
// n8nが更にJSON.parseするので破壊される
```

### NG: specifyBody未指定

```json
{
  "sendBody": true,
  // specifyBody が欠落 → Bodyが送信されない
}
```

## Code nodeの制約

- Code nodeはsandbox環境: `fetch()` / `require()` は使用不可
- 外部APIを叩くにはHTTP Requestノードを使う
- Code nodeはデータ加工・整形のみに使用

## チェックリスト（デバッグ時）

- [ ] specifyBody が "json" になっているか
- [ ] jsonBody の値が有効なJSON文字列またはオブジェクトか
- [ ] JSON.stringify が二重になっていないか
- [ ] Code nodeでfetch()を使おうとしていないか
- [ ] HTTPヘッダーのContent-Typeが application/json になっているか

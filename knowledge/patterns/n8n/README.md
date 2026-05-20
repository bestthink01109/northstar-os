# n8n パターン集

n8n ワークフロー開発で発見された問題と解決策のパターン。

---

## パターン1: HTTP Request v4 JSON Body 二重エンコード問題

### 問題
`specifyBody: json` + `jsonBody: "={{ $json.someField }}"` の構成で、
`someField` がすでに `JSON.stringify()` された文字列の場合、二重エンコードが発生する。

### 症状
- 受信側でJSONパースエラー
- リクエストボディが `"\"{}\"` のような二重エスケープになる

### 解決策
**方法A**: コードノードで文字列をそのまま返し、`specifyBody: raw` + `Content-Type: application/json` で送信。

**方法B**: `jsonBody` に直接オブジェクトリテラルを書く（`JSON.stringify` せずに n8n の式で組み立てる）。

```javascript
// NG: 二重エンコードになる
const body = JSON.stringify({ key: "value" });
return [{ json: { body } }];
// → jsonBody: "={{ $json.body }}"

// OK: n8n式で直接組み立て
// jsonBody: '={"key": "{{ $json.key }}"}'
```

### 確認日
2026-05-20

---

## パターン2: AggregateノードのallItemData出力構造

### 問題
`Aggregate` ノードで `allItemData` を使うと、出力が `data[]` フィールドにネストされる。

### 症状
次のコードノードで `$json.items` を参照しても `undefined` になる。

### 解決策
Aggregateノードの後は `$json.data` でアクセスする。

```javascript
// Aggregateノードの出力
// { data: [ {json: {...}}, {json: {...}}, ... ] }

// 正しいアクセス方法
const items = $json.data;
items.forEach(item => {
  const d = item.json;
  // ...
});
```

### 確認日
2026-05-20

---

## パターン3: Google Drive multipart アップロードの `=` 記号分割問題

### 問題
`uploadType=media` のURLを n8n の HTTP Request ノードで使うと、
`=` 記号でURLが分割されてしまいアップロードが失敗する。

### 症状
- HTTP 400 エラー
- `Bad Request: Invalid upload type`

### 解決策（2ステップ方式）
1. **ファイルメタデータ作成**: `POST /drive/v3/files` でファイルIDを取得
2. **コンテンツアップロード**: `PATCH /upload/drive/v3/files/{fileId}?uploadType=media` でコンテンツを送信

```javascript
// Step 1: メタデータノード
// URL: https://www.googleapis.com/drive/v3/files
// Body: { name: "filename.md", parents: ["folderID"], mimeType: "text/plain" }

// Step 2: アップロードノード
// URL: =https://www.googleapis.com/upload/drive/v3/files/{{ $json.id }}?uploadType=media
// Body: [ファイルコンテンツ]
// Content-Type: text/plain
```

### 確認日
2026-05-20

---

## パターン4: LINE monthly limit 対応

### 問題
LINE Messaging API の無料プランは月200通の上限があり、超過するとエラーになる。
WFでエラーが発生するとその後のノードが全てスキップされる。

### 解決策
LINE送信ノードに `onError: continueRegularOutput` を設定する。

```json
{
  "name": "LINE送信",
  "type": "n8n-nodes-base.httpRequest",
  "onError": "continueRegularOutput",
  ...
}
```

### 運用方針（2026-05-20 確定）
- 無料200通/月で運用
- 個別WF通知は廃止
- 朝ブリーフィング（7:00）と夕方まとめのみ
- エラー通知のみLINEに送信

### 確認日
2026-05-20

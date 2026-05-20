# patterns/n8n/ — n8n問題解決パターン集

> n8n固有のエラー・設定問題の解決パターンを蓄積する。
> 同じ問題を2度調べることのないよう、発見次第ここへ登録すること。

---

## P-001: HTTP Request v4 JSON Body設定エラー

- **カテゴリ**: n8n / HTTP Request
- **症状**: "JSON Body not valid JSON" エラーが発生してWFが停止する
- **原因**: `specifyBody: json` モードで `JSON.stringify()` を適用すると、既にJSONとして評価された値が再度文字列化されてエスケープが二重になる
- **解決策**:
  - `jsonBody` に文字列（既存JSON）を渡す場合は `JSON.stringify()` を使わない
  - オブジェクトをそのまま渡すか、`specifyBody: keypair` に変更して各キーを個別指定する
  - コード例:
    ```javascript
    // NG: 二重stringify
    body: JSON.stringify({ key: "value" })

    // OK: オブジェクトをそのまま渡す（n8nが自動でシリアライズ）
    body: { key: "value" }

    // OK: すでにJSON文字列なら specifyBody: string を使う
    specifyBody: "string"
    body: '{"key": "value"}'
    ```
- **確認日**: 2026-05-20
- **参照**: WF整備セッション（2026-05-20）
- **登場回数**: 1

---

## P-002: Aggregateノードの出力構造

- **カテゴリ**: n8n / Aggregateノード
- **症状**: `aggregateAllItemData` の出力を後続ノードで `input.items` で参照すると `undefined` になる
- **原因**: `aggregateAllItemData` モードはすべてのアイテムを `data[]` フィールドに格納して出力する。`input.items` という名前では出力されない
- **解決策**:
  - 後続のCode/Function ノードでフォールバック付き参照を使う:
    ```javascript
    const items = input.items
      || (input.data && input.data[0] && input.data[0].items)
      || [];
    ```
  - または `aggregateAllItemData` の代わりに `aggregateIndividualFields` を使い、明示的なフィールド名を指定する
- **確認日**: 2026-05-20
- **参照**: WF整備セッション（2026-05-20）
- **登場回数**: 1

---

## P-003: Drive multipartアップロード

- **カテゴリ**: n8n / Google Drive / HTTP Request
- **症状**: Google Drive APIへのファイルアップロード時に `"Invalid multipart request with 0 mime parts"` エラー
- **原因**: `specifyBody: string` でmultipartボディを組み立てる際、`charset=UTF-8` の `=` がkey=value分割の区切り文字として解釈され、MIMEパートが正しく認識されない
- **解決策**: 2ステップアップロードに分割する
  1. **Step 1 — メタデータ作成 (POST)**:
     ```
     POST https://www.googleapis.com/drive/v3/files
     Content-Type: application/json
     Body: { "name": "ファイル名", "parents": ["フォルダID"] }
     ```
     → レスポンスの `id` を変数に保存
  2. **Step 2 — コンテンツアップロード (PATCH)**:
     ```
     PATCH https://www.googleapis.com/upload/drive/v3/files/{fileId}?uploadType=media
     Content-Type: text/plain; charset=UTF-8
     Body: （ファイル内容）
     ```
- **確認日**: 2026-05-20
- **参照**: Drive保存WF整備（2026-05-20）、drive.js の実装も参照
- **登場回数**: 1

---

## P-004: LINE monthly limit対応

- **カテゴリ**: n8n / LINE Messaging API
- **症状**: `"You have reached your monthly limit"` エラーでWFが停止し、後続処理がすべてスキップされる
- **原因**: LINEの無料プラン（200通/月）の上限に達すると429/400エラーが返り、n8nのデフォルトエラーハンドリングではWF全体が停止する
- **解決策**: LINE送信ノードの設定で `onError: continueRegularOutput` を有効にする
  ```json
  {
    "onError": "continueRegularOutput"
  }
  ```
  これによりLINE送信失敗時でも後続ノードが実行される。
  加えてエラー通知用の分岐を追加し、月次通知でLIMIT到達をアラートする:
  ```javascript
  // errorOutputsの有無でLIMIT判定
  if ($('LINE送信').errorOutput.length > 0) {
    // フォールバック通知（メール等）へ分岐
  }
  ```
- **確認日**: 2026-05-20
- **参照**: LINEプラン確認（2026-05-20）、月200通上限で運用継続決定
- **登場回数**: 1

---

## 追加テンプレート

新しいパターンを発見したら以下をコピーして末尾に追加する:

```markdown
## P-[次の連番]: パターン名

- **カテゴリ**: n8n / [サブカテゴリ]
- **症状**: 
- **原因**: 
- **解決策**: 
- **確認日**: YYYY-MM-DD
- **参照**: 
- **登場回数**: 1
```

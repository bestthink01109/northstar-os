---
layer: L3
dept: DEV
priority: high
created: 2026-05-20
---

# MKT_PRタイムズ Drive成果物保存 multipart修正

## 概要
n8n WF「MKT_PRタイムズ4専門人格エージェント」(ID: ht60IBCItF9vt1vO) の
`Drive成果物保存` ノードが `Invalid multipart request with 0 mime parts` で失敗し続けている。

## 現状・調査済み

### 失敗ノード
- ノード名: `Drive成果物保存`
- エラー: `Invalid multipart request with 0 mime parts.`
- API: `POST https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart`

### 根本原因
n8n HTTP Request v4 の `specifyBody: "string"` が、bodyに含まれる `charset=UTF-8` の
`=` 記号でbodyをkey=value形式として分割してしまい、正しいmultipartバイナリではなく
JSON objectとしてGoogle Driveに送信している。

実際にGoogleに届いたbody（確認済み）:
```json
{
  "--boundary123\r\nContent-Type: application/json; charset": "UTF-8\r\n..."
}
```

期待する正しいmultipartボディ:
```
--boundary123\r\n
Content-Type: application/json; charset=UTF-8\r\n
\r\n
{"name": "filename.md", "parents": ["フォルダID"]}\r\n
--boundary123\r\n
Content-Type: text/plain; charset=UTF-8\r\n
\r\n
<file content>\r\n
--boundary123--
```

### 試したこと（効果なし）
- bodyフィールドの先頭`=`を削除
- n8n API経由でWF定義を修正・PUT更新（6回）

## 求める修正内容

以下のいずれかの方法でDrive成果物保存を動作させること。

### 方法A（推奨）: 2ステップアップロードに変更
1. `POST /drive/v3/files` でメタデータのみ作成（mimeType, name, parents）
2. `PATCH /upload/drive/v3/files/{fileId}?uploadType=media` でコンテンツをアップロード

### 方法B: Code nodeでmultipartボディを構築してから渡す
Drive成果物保存の前にCode nodeを追加し、正しいCRLFを持つmultipartボディをBufferで構築する。

### 方法C: n8n Google DriveビルトインノードAに置き換え
`n8n-nodes-base.googleDrive` ノードを使用してファイルをアップロードする。
OAuthトークンは共通WF（http://localhost:5678/webhook/google-oauth-token）から取得。

## 関連情報

- WF ID: `ht60IBCItF9vt1vO`
- Drive保存先フォルダID: `1I_68Pimq8jKjq6xfPMAeD22oeAHc8mTf` (Reports/RSC/)
- OAuth取得WF: `http://localhost:5678/webhook/google-oauth-token`
- n8n管理URL: `http://162.43.78.67:5678`
- VPS SSH: `ssh root@162.43.78.67`
- n8n APIキーは `/root/n8n-api.sh` に記載

## 修正後のテスト方法

```bash
# バックアップWebhookでWFを手動テスト実行
curl -X POST http://162.43.78.67:5678/webhook/mkt-scan-backup \
  -H "Content-Type: application/json" -d '{}'

# 実行結果確認（statusがsuccessになること）
curl "http://162.43.78.67:5678/api/v1/executions?workflowId=ht60IBCItF9vt1vO&limit=1" \
  -H "X-N8N-API-KEY: <key from /root/n8n-api.sh>"
```

## 成功条件
- WF実行がsuccessで完了すること
- Google Drive Reports/RSC/ フォルダに MKT_PRタイムズ_YYYYMMDD.md が保存されること

## L3 Agent 実装ログ
完了: 2026-05-20 14:30:49
生成ファイル数: 1
保存先: /root/northstar-os/workspace/20260520_1400_DEV_MKT_Drive成果物保存multipart修正/
- fix_mkt_pr_drive_upload.py

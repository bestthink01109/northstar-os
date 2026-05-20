---
pattern_name: "drive_multipart_upload"
created: "2026-05-20"
updated: "2026-05-20"
author: "COO"
tags:
  - Drive
  - API
  - n8n
source_reports:
  - "MKT_PRTIMES_HANDOVER_CONTEXT.md"
  - "DEV_MKT_Drive成果物保存multipart修正_20260520"
applicable_scene: "n8n WFからGoogle DriveにMarkdownファイル等を保存する場合"
confidence: high
---

# Google Drive マルチパートアップロードパターン

## 概要

n8n WFからGoogle Driveにファイルをアップロードする際、Google Drive API v3のmultipart upload方式を使用する。

## 正しい実装

### HTTP Requestノードの設定

```
Method: POST
URL: https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart
Headers:
  Authorization: Bearer {{ $json.access_token }}
  Content-Type: multipart/related; boundary=boundary_string
```

### Body構築（Code nodeで作成）

```javascript
const metadata = JSON.stringify({
  name: fileName,
  parents: [folderId],
  mimeType: 'text/markdown'
});

const content = reportContent;

const multipartBody = 
  '--boundary_string\r\n' +
  'Content-Type: application/json; charset=UTF-8\r\n\r\n' +
  metadata + '\r\n' +
  '--boundary_string\r\n' +
  'Content-Type: text/markdown; charset=UTF-8\r\n\r\n' +
  content + '\r\n' +
  '--boundary_string--';

return { json: { uploadBody: multipartBody } };
```

### HTTP Requestノードの設定詳細

```json
{
  "method": "POST",
  "url": "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      { "name": "Authorization", "value": "Bearer {{ $('OAuth').item.json.access_token }}" },
      { "name": "Content-Type", "value": "multipart/related; boundary=boundary_string" }
    ]
  },
  "sendBody": true,
  "specifyBody": "string",
  "body": "={{ $json.uploadBody }}"
}
```

## よくある間違い

### NG: specifyBodyをjsonにする

マルチパートボディはJSONではないため、`specifyBody: "string"` を使用する。
`specifyBody: "json"` にするとn8nがJSON.parseしようとして失敗する。

### NG: boundaryの不一致

Content-Typeヘッダーのboundaryとbody内のboundaryが一致しないとアップロードが失敗する。

### NG: OAuth tokenの取得漏れ

事前に共通OAuth WF（oauth_unified_pattern参照）からtokenを取得しておく必要がある。

## フォルダID一覧

| 部門 | フォルダID |
|------|-----------|
| Reports/DEV/ | 1axzPX0xjgWxVLTHLQHZf-7kSLO2Q_9kZ |
| Reports/RSC/ | 1I_68Pimq8jKjq6xfPMAeD22oeAHc8mTf |
| Reports/BizDev/ | 1ItQqd-_I3ARoUkclvJc4pVU2HMMlq_dS |
| Reports/FIN/ | 1kXD9larver4TTgWAJAVeBLWujb2eaM70 |
| Reports/OPS/ | 1ahvEniXrxUiPH50yc1A1g6E4qcFdLccv |
| research/Daily_Report/ | 1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8 |

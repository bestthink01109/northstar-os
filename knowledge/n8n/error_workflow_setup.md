---
pattern_name: "error_workflow_setup"
created: "2026-05-20"
updated: "2026-05-20"
author: "COO"
tags:
  - n8n
  - debug
  - LINE
source_reports:
  - "COO_Context_20260520_MAIN.md"
applicable_scene: "n8n WFにエラー検知・自動アラートを設定する場合"
confidence: high
---

# n8n エラーワークフロー設定パターン

## 概要

全WFにerrorWorkflow設定を入れ、エラー発生時に自動で:
1. LINEアラート送信
2. 全社ボード（n8n稼働ログ）に記録

## 設定方法

### 各WFのSettings

```json
{
  "settings": {
    "errorWorkflow": "VOR8Hbpt8FYEtmIp"
  }
}
```

### エラーアラートWF（VOR8Hbpt8FYEtmIp）の構成

```
Error Trigger
    ↓
エラー情報抽出（WF名・エラーメッセージ・発生時刻）
    ↓
├── LINE通知（アラートメッセージ送信）
└── 全社ボード書き込み（n8n稼働ログシートにエラー行追記）
```

## n8n APIでの一括設定

```bash
# 全WFのerrorWorkflowを一括設定するスクリプト
for wf_id in $(curl -s http://localhost:5678/api/v1/workflows \
  -H "X-N8N-API-KEY: ${N8N_API_KEY}" | jq -r '.data[].id'); do
  curl -s -X PATCH "http://localhost:5678/api/v1/workflows/${wf_id}" \
    -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"settings":{"errorWorkflow":"VOR8Hbpt8FYEtmIp"}}'
done
```

## 注意事項

- errorWorkflow自体がエラーを出すと無限ループになるため、エラーアラートWF自身にはerrorWorkflowを設定しない
- エラーアラートWF内のノードは極力シンプルに保つ（複雑なロジックを入れない）
- LINE通知のメッセージにはWF名・エラー概要・発生時刻を含める

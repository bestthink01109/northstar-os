---
pattern_name: "credential_rotation"
created: "2026-05-20"
updated: "2026-05-20"
author: "COO"
tags:
  - security
  - n8n
  - debug
source_reports:
  - "COO_Context_20260520_MAIN.md"
applicable_scene: "APIキー流出・credential期限切れ・セキュリティインシデント発生時"
confidence: high
---

# Credential ローテーションパターン

## 概要

APIキーの流出やcredential期限切れが発生した場合の対応手順。
2026-05-20にGemini APIキー流出インシデントで実証済み。

## 対応手順

### 1. 影響範囲の特定

```bash
# 流出したcredentialを使用しているWFを特定
bash n8n-api.sh wf-nodes <wfId> | grep -i "credential"

# 全WFのcredential使用状況を確認
for wf_id in $(curl -s http://localhost:5678/api/v1/workflows \
  -H "X-N8N-API-KEY: ${N8N_API_KEY}" | jq -r '.data[].id'); do
  echo "=== WF: $wf_id ==="
  curl -s "http://localhost:5678/api/v1/workflows/${wf_id}" \
    -H "X-N8N-API-KEY: ${N8N_API_KEY}" | jq '.nodes[].credentials'
done
```

### 2. 新しいcredential作成

```bash
# n8n UIで新しいcredentialを作成（APIでは不可）
# → http://162.43.78.67:5678/credentials/new
```

### 3. 旧credential削除

```bash
# n8n APIで旧credentialを削除
bash n8n-api.sh delete-cred <old_credential_id>
```

### 4. 各WFのcredential参照を更新

```bash
# WF内のノードが旧credential IDを参照している場合
# n8n UIで各ノードのcredential設定を新IDに変更
# または n8n API PATCH で一括更新
```

### 5. 動作確認

```bash
# credential有効性テスト
bash n8n-api.sh test-cred <new_credential_id> <type>
```

## 共通OAuth方式の場合

共通OAuth WF（Eu3kQaH8vQpJmyqd）を使用している場合、変更は1箇所のみ:
1. 共通OAuth WF内のGoogle OAuth2 credentialを新しいものに差し替え
2. 全WFは自動的に新しいtokenを取得

## チェックリスト

- [ ] 流出元の特定（どこから漏れたか）
- [ ] 旧キー/tokenの無効化（プロバイダー管理画面で）
- [ ] 新credential作成・テスト
- [ ] 影響を受ける全WFの更新
- [ ] 動作確認（テスト実行）
- [ ] インシデントレポート作成（Type C: デバッグレポート）
- [ ] 再発防止策の実施

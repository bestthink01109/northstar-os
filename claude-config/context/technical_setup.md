---
# Technical Setup | NorthStar OS
# 更新日: 2026-05-20（セッション終了版・最終）
---

※最新版は /Users/fuminariaksse/.claude/context/technical_setup.md を参照
このファイルはGitHubバックアップ用コピーです。セッション終了時に自動更新されます。

## 稼働中ツール

| ツール | 用途 | エンドポイント |
|--------|------|--------------|
| Claude Code（COO） | 戦略・監督・例外処理 | ローカルMac |
| n8n | オーケストレーター（24/7） | http://162.43.78.67:5678 |
| LINE Harness | LINE自動化 | northstar-line.bestthink01109.workers.dev |
| Google Drive | 全成果物・データ保存 | drive.js経由 |
| GitHub（Public） | コード・マニュアル・DEVチケット | bestthink01109/northstar-os |

## VPS情報

- IP: 162.43.78.67（シンVPS）
- OS: Ubuntu 24.04.4 LTS
- n8n: Docker稼働（:5678）
- SSH: ~/.ssh/vps_key

## 共通GoogleOAuth WF

- ID: Eu3kQaH8vQpJmyqd
- Webhook: http://localhost:5678/webhook/google-oauth-token

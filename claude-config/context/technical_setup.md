---
# Technical Setup | NorthStar OS
# 更新日: 2026-05-22（L3正常稼働確認・Drive認証手順追加）
---

## 稼働中ツール

| ツール | 用途 | エンドポイント |
|--------|------|--------------|
| Claude Code（COO） | 戦略・監督・例外処理 | ローカルMac（PC起動時） |
| Antigravity | COOバックアップ（制限あり） | /Desktop/antigravity Folder/ |
| n8n | オーケストレーター（24/7） | http://162.43.78.67:5678 |
| LINE Harness | LINE自動化・HTTPS固定URL | northstar-line.bestthink01109.workers.dev |
| Google Drive | 全成果物・データ保存 | drive.js経由 |
| GitHub（Public） | コード・マニュアル・DEVチケット | bestthink01109/northstar-os |
| Cloudflare | Workers（LINE Harness）・R2 | bestthink01109@gmail.com |

## 稼働インフラ方式（確定）

```
VPS + Ticket自動処理方式
  常時：n8n（24/7）・ticket-puller（60秒）・codex-watcher（30秒）
  DEV：COOがGitHubにチケットをcommit → VPSが自動処理（L1/L2/L3）
  目的：コスト最小化・24/7対応・Mac不在でも稼働
```

## VPS DEVパイプライン（L3修正完了 2026-05-19）

| スクリプト | パス | 役割 | 状態 |
|-----------|------|------|------|
| ticket_puller.sh | /root/northstar/ | Layer判定・ルーティング | ✅ |
| apply_template.sh | /root/northstar/ | L1テンプレート適用 | ✅ |
| dev_agent_trigger.sh | /root/northstar/ | L3 DEV Agent起動 | ✅（Python+Claude API方式） |
| l3_agent.py | /root/northstar/ | L3本体・Claude API直接呼び出し | ✅ |
| codex_watcher.sh | /root/northstar/ | Codexデバッグ監視 | ✅ |

SSH接続: `ssh root@162.43.78.67`（vps_keyをssh-agentに登録済み）

## drive.js認証トラブルシューティング（2026-05-22追加）

```
症状：invalid_grant エラー
原因：oauth_tokens.json のrefresh_tokenが古い（revoked）
対処：別セッションでdrive.jsを一度実行 → oauth_tokens.jsonが自動更新される
確認：node drive.js search "test" で認証テスト
```

## n8n 稼働中ワークフロー

| ワークフロー | ID | スケジュール | 状態 |
|------------|-----|------------|------|
| 朝ブリーフィング+Dashboard | NjmKR3rlzaAdznoB | 毎日7:00 | ✅ |
| RSCリサーチ巡回 | 796EUn4zvboKFQiP | 毎日6:00 | ✅ |
| 夕リフレクション | VD4QeU4XVfhqmMbl | 毎日19:00 | ✅ |
| 部門日次報告集約 | 4LTj5vfwCcDqVUKc | 毎日18:45 | ✅ |
| LINEコマンド処理 | Ury2oteVKpcHBI8m | 常時Webhook | ✅ |
| BizDevスキャン | 0zftWq8EAnbcJwrE | 毎週月曜8:00 | ✅ |
| Signal DB週次分析 | wxJUU8dPwbWqFyGP | 毎週日曜4:00 | ✅ |
| n8nバックアップ | PAlz3XfDYycQA48D | 毎週日曜3:00 | ✅ |
| FIN月次レポート | uxIDllsGUiDilADI | 毎月1日9:00 | ✅（ベリファイ追加が今週タスク） |
| DEV QAレビュー(DeepSeek) | RAtN2vX8tMOfHJ5G | 常時Webhook | ✅ |
| n8nエラーアラート | VOR8Hbpt8FYEtmIp | WF失敗時 | ✅ |
| プリフライト3回パス | pbGRNA9dKLzHqqxQ | 常時Webhook | ✅ |
| System QA夜間 | dSItw958pDfl3fMs | 毎日21:00 JST | ✅ |
| MKT_PRタイムズ4エージェント | ht60IBCItF9vt1vO | 毎日9:00 | ❌ JSON Bodyエラー（今週修正） |
| MKT_SNSコンテンツ自動生成 | YGacVsIyaf43mfG2 | 月水金10:00 | ✅ |
| SALES_PRタイムズ | Ru1FfTgXk6YWczjk | 毎日5:45 | ⚠️ エラー（今週修正） |
| 共通GoogleOAuth | Eu3kQaH8vQpJmyqd | 常時Webhook | ✅ |

## 全社ボード（Google Sheets）
- URL: https://docs.google.com/spreadsheets/d/1MMneMJ_jLHpK_a79vJ7n2QfWhj2QtE_6zJDPkjd2I1Q
- シート: 📋チケットボード / ⚙️n8n稼働ログ / 💰APIコスト / 📦成果物管理 / SALES_リード管理

## API認証情報（n8n credentials）

| プロバイダー | ID | 用途 |
|------------|-----|------|
| Anthropic | 6RjA3eGBjtQkbNiy | 全部門実行AI |
| OpenAI | x2D3cGEreDX5TCzW | MKT/SALES/FIN/OPS QA・System QA |
| Google Gemini | zU4hmCHGMNhqZzZN | RSC実行AI |
| DeepSeek | PqJXpBvAh3IFuE3i | DEV QA（データ主権要注意） |
| LINE | K0c4UrAem1gYGaxD | 通知・受信 |
| Google SA | Z72mc0LCzm6a777w | Drive保存 |
| GitHub | GpJ0FZiIMEBV1JZg | コード管理 |

## Google Drive フォルダID

| 用途 | フォルダID |
|------|-----------|
| Reports/DEV/ | 1axzPX0xjgWxVLTHLQHZf-7kSLO2Q_9kZ |
| Reports/RSC/ | 1I_68Pimq8jKjq6xfPMAeD22oeAHc8mTf |
| Reports/BizDev/ | 1ItQqd-_I3ARoUkclvJc4pVU2HMMlq_dS |
| Reports/FIN/ | 1kXD9larver4TTgWAJAVeBLWujb2eaM70 |
| Reports/OPS/ | 1ahvEniXrxUiPH50yc1A1g6E4qcFdLccv |
| Dashboard/ | 1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8 |

## スケジュール確定表（JST）

| WF | JST時刻 |
|----|---------|
| APIコスト | 0:30 |
| n8nバックアップ | 3:00 |
| MKT_PRタイムズ | 5:30 |
| SALES_PRタイムズ | 5:45 |
| RSCリサーチ | 6:00 |
| SALES日次 | 6:30 |
| 全社ボード同期（朝） | 6:50 |
| 朝ブリーフィング | 7:00 |
| 部門日次報告 | 18:45 |
| 夕リフレクション | 19:00 |
| 全社ボード同期（夜） | 19:00 |
| System QA | 21:00 |
| BizDev | 月曜8:00 |
| Signal DB | 日曜4:00 |
| FIN月次 | 1日9:00 |

## 手動WF実行Webhook一覧
```bash
curl -X POST http://162.43.78.67:5678/webhook/board-sync                  # 全社ボード同期
curl -X POST http://162.43.78.67:5678/webhook/rsc-manual-run              # RSCリサーチ巡回
curl -X POST http://162.43.78.67:5678/webhook/briefing-manual-run -H "Content-Type: application/json" -d '{"trigger":"manual"}'
curl -X POST http://162.43.78.67:5678/webhook/sales-pr-manual-run -H "Content-Type: application/json" -d '{"trigger":"manual"}'
curl -X POST http://162.43.78.67:5678/webhook/sysqa-manual-run -H "Content-Type: application/json" -d '{"trigger":"manual"}'
```

## 重要コマンド
```bash
node /Users/fuminariaksse/.config/gdrive-mcp/drive.js [command]
bash /Users/fuminariaksse/.config/gdrive-mcp/n8n-api.sh [command]
```

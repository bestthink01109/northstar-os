# Technical Setup | NorthStar OS
# 更新日: 2026-05-21

最新版は /Users/fuminariaksse/.claude/context/technical_setup.md を参照。

## 主要インフラ
- VPS: 162.43.78.67 (シンVPS Ubuntu 24.04)
- n8n: Docker稼働 TZ=Asia/Tokyo (JST)
- n8n API: http://162.43.78.67:5678

## n8n TZ=Asia/Tokyo（重要）
cronは全てJST値で設定。UTC計算不要。
例: 5:30 JST = `30 5 * * *`

## スケジュール確定表（JST）
| WF | cron | JST |
|----|------|-----|
| APIコスト | 30 0 * * * | 0:30 |
| n8nバックアップ | 0 3 * * * | 3:00 |
| MKT_PR | 30 5 * * * | 5:30 |
| SALES_PR | 45 5 * * * | 5:45 |
| RSCリサーチ | 0 6 * * * | 6:00 |
| SALES日次 | 30 6 * * * | 6:30 |
| 全社ボード朝 | 50 6 * * * | 6:50 |
| 朝ブリーフィング | 0 7 * * * | 7:00 |
| 部門日次 | 45 18 * * * | 18:45 |
| 夕リフレクション | 0 19 * * * | 19:00 |
| 全社ボード夜 | 0 19 * * * | 19:00 |
| System QA | 0 12 * * * | 12:00 |

## 共通OAuth WF
- ID: Eu3kQaH8vQpJmyqd
- URL: http://localhost:5678/webhook/google-oauth-token
- 参照: $('OAuthトークン取得').item.json.access_token

## バックアップ体制
- n8n WF定義: GitHub backups/n8n/ 毎日3:00 JST
- SQLite DB: /root/backups/sqlite/ 毎日3:30 JST (cron)

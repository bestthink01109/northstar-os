# NS_OS_ARCHITECTURE | NorthStar OS
# 更新日: 2026-05-21（セッション終了版）

## 2026-05-21 主な変更点
- MKT/SALES WF全修正完了
- n8n TZ=Asia/Tokyo確定（cronはJST値）
- LINE全WFにcontinueRegularOutput設定
- 冗長化体制確立（GitHub日次+VPS SQLite日次）
- knowledge/ディレクトリ構築
- レポートフォームType A〜D統一

## スケジュール確定（JST）
| WF | JST | cron |
|----|-----|------|
| APIコスト | 0:30 | 30 0 * * * |
| n8nバックアップ | 3:00 | 0 3 * * * |
| MKT_PRタイムズ | 5:30 | 30 5 * * * |
| SALES_PRタイムズ | 5:45 | 45 5 * * * |
| RSCリサーチ | 6:00 | 0 6 * * * |
| SALES日次 | 6:30 | 30 6 * * * |
| 全社ボード朝 | 6:50 | 50 6 * * * |
| 朝ブリーフィング | 7:00 | 0 7 * * * |
| 部門日次報告 | 18:45 | 45 18 * * * |
| 夕リフレクション | 19:00 | 0 19 * * * |
| 全社ボード夜 | 19:00 | 0 19 * * * |
| System QA | 12:00 | 0 12 * * * |
| BizDev | 月曜8:00 | 0 8 * * 1 |
| Signal DB | 日曜4:00 | 0 4 * * 0 |
| FIN月次 | 1日9:00 | 0 9 1 * * |

## バックアップ体制
- n8n WF定義（サニタイズ）→ GitHub backups/n8n/ 毎日3:00 JST
- SQLite DB → VPS /root/backups/sqlite/ 毎日3:30 JST

## VPS情報
- IP: 162.43.78.67（シンVPS）
- n8n TZ=Asia/Tokyo（JST）
- SSH: ssh root@162.43.78.67

## 共通OAuth
- WF ID: Eu3kQaH8vQpJmyqd
- URL: http://localhost:5678/webhook/google-oauth-token
- 参照: $('OAuthトークン取得').item.json.access_token

## GitHub構造
- northstar-os/
  - backups/n8n/ : WF定義日次バックアップ
  - claude-config/context/ : contextファイル
  - claude-config/coo-context/ : COO_Context
  - vps/scripts/ : VPSスクリプト
  - knowledge/ : パターン・決定事項・スキル
  - dev/templates/reports/ : レポートフォーム
  - tickets/ : DEVチケット

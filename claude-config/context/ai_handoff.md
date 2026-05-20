# AI Handoff | NorthStar OS
# 更新日: 2026-05-21（セッション終了版・最終）

## 重要引き継ぎ事項（2026-05-21版）

### n8n タイムゾーン確定
- TZ=Asia/Tokyo → cronは全てJST値で設定
- 5:30 JST = `30 5 * * *`（UTC計算不要）

### スケジュール確定（JST cron）
- MKT_PR: `30 5 * * *` / SALES_PR: `45 5 * * *`
- RSC: `0 6 * * *` / SALES日次: `30 6 * * *`
- 全社ボード朝: `50 6 * * *` / 朝ブリーフィング: `0 7 * * *`
- 部門日次: `45 18 * * *` / 夕リフレクション: `0 19 * * *`
- System QA: `0 12 * * *`（12:00 JST正午）

### LINE設計完成
- 全12WF onError:continueRegularOutput設定済み
- エラーアラート5分重複チェック追加
- 月次200通：朝夕+エラーアラートのみ稼働
- 6月1日自動回復

### OAuth参照ルール（重要）
- 正: `$('OAuthトークン取得').item.json.access_token`
- 誤: `$('sq-token')` → ノードIDで参照するとエラー
- 仕様: knowledge/patterns/api/oauth_standard.md 参照

### バックアップ体制（確立済み）
- GitHub: WF定義 `backups/n8n/` 毎日3:00 JST
- VPS: SQLite `/root/backups/sqlite/` 毎日3:30 JST

### WF修正完了（2026-05-21）
- MKT_PRタイムズ: 全修正完了（data[0].items/Drive2ステップ/jsonBody）
- SALES_PRタイムズ: 同様修正・稼働確認済み
- System QA: `$('sq-token')` → `$('OAuthトークン取得')` 修正
- DEV QA: specifyBody:json 追加

### 全社ボード強化
- 稼働ログ: グループ順統一・LINE停止表現改善
- システム状態: バックアップ体制セクション追加
- 朝ブリーフィング: 部門サマリー追加

### ナレッジ体系構築
- dev/templates/reports/ : Type A〜D テンプレート
- knowledge/patterns/n8n/ : バグパターン4件
- knowledge/patterns/api/ : OAuth共通仕様
- knowledge/decisions/ : 重要決定事項記録

## 積み残しタスク（優先順）
| 優先 | タスク | 状態 |
|------|--------|------|
| 🔴 | 全社ボード確認（毎セッション必須）| — |
| 🔴 | OPS純青 Python実装 | DEVチケット起票 |
| 🔴 | LINE月次上限（6/1リセット待ち）| 自動回復 |
| 🔴 | MKT/SALES_PR明朝定時実行確認 | 自動 |
| 🟡 | LINE自動化デモ認証エラー | l5snFeHnKr435xiL |
| 🟡 | KENZAI Mac自動適用 | workspace/生成済み |
| 🟡 | SALES Playwright実送信 | 骨格のみ |
| 🟡 | GitHubのtest_ticket削除 | done/に残存 |
| 🟢 | OPS仕様ヒアリング（信和・共生）| BUN_CEO指示待ち |
| 🟡 | Instagram/note SNS展開 | アカウント作成後 |
| 🟡 | X自動投稿 | Developer Account申請後 |

## 次セッションへの引き継ぎ
1. **全社ボード最初に読む**（稼働状況確認）
2. **LINE停止は正常**（⚠️後続稼働・6/1自動回復）
3. **OPS純青Python実装**をDEVチケット化
4. 明朝5:30/5:45の定時実行を確認

## 技術情報
- VPS SSH: ssh root@162.43.78.67
- n8n: http://162.43.78.67:5678
- n8n-api.sh: /Users/fuminariaksse/.config/gdrive-mcp/n8n-api.sh
- WF総数: 25本（共通OAuthWF含む）

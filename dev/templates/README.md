# L1 テンプレートライブラリ

コスト0でチケットを処理するためのテンプレート集。
チケットの `template:` フィールドでテンプレート名を指定する。

## マッチングルール

| template名 | 用途 | キーワード |
|-----------|------|-----------|
| `line-notify` | LINE通知送信 | LINE、通知、メッセージ送信 |
| `drive-read` | Driveファイル読み込み | Drive読み込み、ファイル取得 |
| `drive-write` | Driveファイル書き込み | Drive保存、ファイル作成 |
| `schedule-claude` | スケジュール+Claude API | 定期実行、毎日、Claude |
| `http-get` | HTTP GETリクエスト | API取得、HTTP GET、外部API |
| `error-alert` | エラーアラート | エラー検知、アラート、失敗通知 |
| `webhook-trigger` | Webhook受信+処理 | Webhook、受信トリガー |
| `drive-to-line` | Drive読んでLINE通知 | レポート通知、Drive→LINE |

## チケット記述例

```markdown
- layer: 1
- type: n8n-wf
- template: line-notify
- vars:
  - MESSAGE: 今日のレポートが完成しました
  - CHANNEL: bestthink01109@gmail.com
```

## 変数置換ルール
テンプレート内の `{{VAR_NAME}}` をチケットの `vars:` セクションの値で置換する。

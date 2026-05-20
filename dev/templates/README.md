# NorthStar OS — テンプレートライブラリ

---

## ディレクトリ構造

```
dev/templates/
├── README.md              ← このファイル
├── n8n/                   ← L1 n8nテンプレート（コスト¥0）
├── sales/                 ← SALESフォーミュラ集
│   └── DIRECT_RESPONSE_FORMULAS.md
├── reports/               ← レポートフォームテンプレート（Type A〜C, E）
│   ├── TYPE_A_OPS_REPORT.md       ← 運用レポート（RSC/FIN/MKT等）
│   ├── TYPE_B_DEV_REPORT.md       ← 開発・実装レポート
│   ├── TYPE_C_DEBUG_REPORT.md     ← デバッグレポート
│   └── TYPE_E_RESEARCH_REPORT.md  ← 調査・分析レポート
└── tickets/               ← チケットフォームテンプレート（Type D）
    └── TYPE_D_COO_TICKET.md       ← COO指示書
```

---

## レポートフォーム（Type A〜E）

詳細は `dev/REPORT_FORM_GUIDE.md` を参照。

| Type | 名称 | テンプレート | 主な使用場面 |
|------|------|------------|-------------|
| A | 運用レポート | reports/TYPE_A_OPS_REPORT.md | n8n WF自動生成（RSC/FIN/MKT/SALES/BizDev） |
| B | 開発・実装レポート | reports/TYPE_B_DEV_REPORT.md | DEVチケット完了時 |
| C | デバッグレポート | reports/TYPE_C_DEBUG_REPORT.md | 障害・エラー修復時 |
| D | COO指示書 | tickets/TYPE_D_COO_TICKET.md | チケット起票時 |
| E | 調査・分析レポート | reports/TYPE_E_RESEARCH_REPORT.md | 競合調査・法改正分析時 |

### 使い分けルール

- 新しく作る → Type B
- 壊れたものを直す → Type C
- 定常報告 → Type A
- 調査・分析 → Type E
- 誰かに指示する → Type D

---

## L1 n8nテンプレート（コスト¥0）

チケットの `template:` フィールドでテンプレート名を指定する。

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

### チケット記述例

```markdown
- layer: 1
- type: n8n-wf
- template: line-notify
- vars:
  - MESSAGE: 今日のレポートが完成しました
  - CHANNEL: bestthink01109@gmail.com
```

### 変数置換ルール

テンプレート内の `{{VAR_NAME}}` をチケットの `vars:` セクションの値で置換する。

# NorthStar OS — レポートテンプレート一覧

各部門AIが出力するレポートのフォームを4種類に統一したテンプレート集。
各WFのプロンプト内で参照し、一貫したフォーマットで成果物を出力すること。

---

## テンプレート一覧

| ファイル名 | 種別 | 用途 |
|---|---|---|
| [type_a_operations.md](./type_a_operations.md) | Type A: 運用レポート | RSC・FIN・BizDev・System QA等の自動生成レポート |
| [type_b_development.md](./type_b_development.md) | Type B: 開発レポート | DEVチケット完了時の実装報告 |
| [type_c_debug.md](./type_c_debug.md) | Type C: デバッグレポート | WF/スクリプトの障害対応記録 |
| [type_d_ticket.md](./type_d_ticket.md) | Type D: COO指示書（チケット） | COOからDEV/OPS/各部門AIへの作業指示 |

---

## 使い分けガイド

### Type A: 運用レポート
- **使う場面**: RSCリサーチ結果、FIN月次レポート、BizDev分析、System QA報告、n8n WF自動生成レポート全般
- **ファイル名規則**: `[部門プレフィックス]_[内容]_YYYYMMDD.md`
  - 例: `RSC_福岡介護動向_20260520.md`
  - 例: `FIN_月次損益レポート_20260520.md`
- **保存先**: Google Drive `Reports/[部門]/`

### Type B: 開発レポート
- **使う場面**: DEVチケット完了時、新規スクリプト・WF実装後
- **ファイル名規則**: `DEV_[機能名]_YYYYMMDD.md`
  - 例: `DEV_KENZAIリリースノート_20260520.md`
- **保存先**: Google Drive `Reports/DEV/`

### Type C: デバッグレポート
- **使う場面**: WF障害・スクリプトエラー・API接続失敗等の障害対応後
- **ファイル名規則**: `DEBUG_[対象WF/機能]_YYYYMMDD.md`
  - 例: `DEBUG_n8n_RSC_WF_20260520.md`
- **保存先**: Google Drive `Reports/DEV/`

### Type D: COO指示書（チケット）
- **使う場面**: COOが各部門AIへ作業を依頼するとき。Googleカレンダーのタスクや全社ボードのチケットに対応
- **ファイル名規則**: `TICKET_[タスク名]_YYYYMMDD.md`
  - 例: `TICKET_n8n_WF修正_20260520.md`
- **保存先**: GitHub `dev/tickets/` または全社ボード

---

## 命名規則まとめ

| 部門 | プレフィックス | 例 |
|---|---|---|
| DEV | `DEV_` | `DEV_KENZAIリリースノート_20260520.md` |
| RSC | `RSC_` | `RSC_福岡介護動向_20260520.md` |
| BizDev | `BIZ_` | `BIZ_新規案件評価_20260520.md` |
| FIN | `FIN_` | `FIN_月次損益レポート_20260520.md` |
| OPS | `OPS_` | `OPS_シフト修正報告_20260520.md` |
| COO横断 | `COO_` | `COO_Context_20260520.md` |
| デバッグ | `DEBUG_` | `DEBUG_n8n_RSC_WF_20260520.md` |
| チケット | `TICKET_` | `TICKET_n8n_WF修正_20260520.md` |

---

## WFプロンプトへの組み込み方

各WFのシステムプロンプトに以下を追加することで、出力フォーマットを統一できる:

```
# 出力フォーマット
レポートはGitHub northstar-os リポジトリの以下テンプレートに従うこと:
- 運用レポート: dev/templates/reports/type_a_operations.md
- 開発レポート: dev/templates/reports/type_b_development.md
- デバッグ報告: dev/templates/reports/type_c_debug.md
- 作業指示書: dev/templates/reports/type_d_ticket.md
```

---

更新日: 2026-05-20

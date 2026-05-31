# Technical Setup | NS-OSV2

更新日: 2026-06-01

## 正本パス

- Vault root: `/Users/fuminariaksse/Desktop/NS-OSV2/NS-OSV2-Brain`
- Repo root: `/Users/fuminariaksse/Desktop/NS-OSV2/repo`

## 重要ディレクトリ

### Vault (NS-OSV2-Brain) — ドキュメント・チケット・コンテキスト
- Board tickets: `00_Projects/NS-OSV2_Board/tickets/`
- COO area: `01_Areas/COO/`
- QA area: `01_Areas/QA/`
- RSC knowledge: `02_Resources/KnowledgeBase/rsc_daily_patrol/`
- Archive contexts: `03_Archives/COO_Context_履歴/`
- Runner status: `01_Areas/COO/AI_Runner_Status_Latest.md`

### Repo (repo/) — スクリプト・コード・テンプレート・仕様書
- スクリプト全般: `repo/scripts/`
  - 監視スクリプト: `repo/scripts/monitors/`（board_qa_monitor.sh 等）
  - 実行スクリプト: `repo/scripts/runners/`
  - バックアップ: `repo/scripts/backup/`
  - 取り込み: `repo/scripts/ingestion/`
- QA仕様: `repo/docs/qa/`
- 運用設計: `repo/docs/operations/`
- Boardテンプレート: `repo/board/templates/`
- 保存先全体マップ: `repo/docs/operations/NS-OSV2_保存先作成マップ.md`

### 保存先の原則（必ず守る）
- シェルスクリプト・Pythonスクリプト → `repo/scripts/` 配下
- Markdownドキュメント・チケット → `NS-OSV2-Brain/` 配下
- 機密情報（キー・トークン）→ ローカルのみ（repo に push 禁止）

## automation の考え方

- daily と 15分 health monitor が稼働している前提
- latest 面は自動更新されるが、ズレがあれば実チケット正本を優先する

## Claude Code の責務

- ドキュメント・チケット・コンテキストの更新
- 最新文脈の引き継ぎ
- ルール違反の drift を remediation work に落とす

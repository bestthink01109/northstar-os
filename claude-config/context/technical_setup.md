# Technical Setup | NS-OSV2

更新日: 2026-05-30 セッション2

## 正本パス

- Vault root: `/Users/fuminariaksse/Desktop/NS-OSV2/NS-OSV2-Brain`
- Repo root: `/Users/fuminariaksse/Desktop/NS-OSV2/repo`
- AUDIT scripts: `Vault/01_Areas/AUDIT/`
- context正本: `Vault/.claude/context/`（グローバル~/.claude/context/ではない）

## 重要ディレクトリ

### Vault (NS-OSV2-Brain) — ドキュメント・チケット・コンテキスト
- Board tickets: `00_Projects/NS-OSV2_Board/tickets/`
- COO area: `01_Areas/COO/`
- AUDIT area: `01_Areas/AUDIT/`（audit_runner.py / audit_config.json / remediation_log.md）
- RSC knowledge: `02_Resources/KnowledgeBase/rsc_daily_patrol/`
- Archive contexts: `03_Archives/COO_Context_履歴/`

### AUDIT System
- 実行: `python3 Vault/01_Areas/AUDIT/audit_runner.py weekly [openai|anthropic|gemini]`
- Provider切替: `audit-use openai` / `audit-use anthropic` / `audit-use gemini`（~/.zshrc・~/.bash_profileにalias設定済み）
- 現在のdefault: openai（gpt-5.4）
- Anthropic: レートリミット対応済み（PKGファイル収集除外）
- Gemini: google.genai新API対応済み（gemini-2.5-pro）

### 保存先の原則（必ず守る）
- シェルスクリプト・Pythonスクリプト → `repo/scripts/` 配下
- Markdownドキュメント・チケット → `NS-OSV2-Brain/` 配下
- 機密情報（キー・トークン）→ ローカルのみ（repo に push 禁止）

## Claude Code の責務

- ドキュメント・チケット・コンテキストの更新
- 最新文脈の引き継ぎ
- AUDIT所見の是正実施・remediation_log.md更新

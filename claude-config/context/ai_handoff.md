---
# AI Handoff | NorthStar OS
# 更新日: 2026-05-23（YouTube API v3登録完了・ナレッジ結晶化インフラ整備・Layer B設計確定）
# ※このファイルはセッション終了時にCOOが必ず更新する
---

## ⚠️ COOセッション開始時の必須手順（スキップ禁止）

1. このファイルを読む
2. technical_setup.md を読む
3. philosophy_values.md / professional_identity.md / design_language.md / NS_OS_ARCHITECTURE.md を読む
4. `node drive.js search "COO_Context"` で最新ファイルを読む
5. 「コンテキスト読み込み完了。前回の続きから着手します」と宣言
6. 作業開始

## ⚠️ COOセッション終了時の必須手順（スキップ禁止）

以下の6ファイルを必ず更新してからセッションを終了すること：
1. `ai_handoff.md` — 積み残し・完了・引き継ぎを更新
2. `technical_setup.md` — インフラ変更があれば更新
3. `philosophy_values.md` — 方針変更があれば更新
4. `professional_identity.md` — 組織変更があれば更新
5. `design_language.md` — 規則変更があれば更新
6. `NS_OS_ARCHITECTURE.md` — アーキテクチャ変更があれば更新

---

## COO体制（2026-05-22確定）

```
主：Claude Code（このインターフェース）
    - フル機能：ファイル操作・コード実行・n8n操作・全部門統括

副：Antigravity 2.0（Google I/O 2026・5/19発表）
    - エンジン：Gemini 3.5 Flash（289トークン/秒・Opus比4倍速）
    - 用途：戦略議論・文書作成・分析・デバッグ全般
    - 作業フォルダ: /Users/fuminariaksse/northstar-os/（統合済み）
```

## n8nワークフロー（2026-05-23版）

| WF | ID | 状態 |
|----|----|----|
| 朝ブリーフィング | NjmKR3rlzaAdznoB | ✅稼働中 |
| 夕リフレクション | VD4QeU4XVfhqmMbl | ✅稼働中 |
| 全社ボード同期 | oX27R5nH3AYa6KlW | ✅稼働中 |
| RSCリサーチ | 796EUn4zvboKFQiP | ✅稼働中 |
| 部門日次報告 | 4LTj5vfwCcDqVUKc | ✅稼働中 |
| BizDevスキャン | 0zftWq8EAnbcJwrE | ✅稼働中 |
| Signal DB分析 | wxJUU8dPwbWqFyGP | ✅稼働中 |
| FIN月次レポート | uxIDllsGUiDilADI | ✅稼働中 |
| System QA夜間 | dSItw958pDfl3fMs | ✅稼働中 |
| MKT_PRタイムズ | ht60IBCItF9vt1vO | ✅稼働中（2026-05-22 20:30 success確認） |
| MKT_SNSコンテンツ | YGacVsIyaf43mfG2 | ✅稼働中 |
| SALES日次レビュー | lIPXpgBTg478uHW0 | ✅稼働中 |
| SALES承認Webhook | zFS7khgDCmK5GR0L | ⚠️骨格のみ・Playwright未実装 |
| APIコスト日次更新 | 0XHdY5FAsuAkwtVW | ✅稼働中 |
| LINEコマンド | Ury2oteVKpcHBI8m | ✅稼働中 |
| n8nバックアップ | PAlz3XfDYycQA48D | ✅稼働中 |
| n8nエラーアラート | VOR8Hbpt8FYEtmIp | ✅稼働中 |
| プリフライト3回パス | pbGRNA9dKLzHqqxQ | ✅稼働中 |
| DEV QA(DeepSeek) | RAtN2vX8tMOfHJ5G | ✅稼働中 |
| SALES_PRタイムズ | Ru1FfTgXk6YWczjk | ✅稼働中（2026-05-22 20:45 success確認） |
| LINE自動化デモ | l5snFeHnKr435xiL | ✅稼働中 |
| 共通GoogleOAuth | Eu3kQaH8vQpJmyqd | ✅全WFが参照 |
| YouTube APIテスト | 9AjBftcINoGx7CNH | ✅動作確認用（削除可） |

---

## 積み残しタスク（2026-05-23更新）

### 🔴 次セッション最優先
| 優先 | タスク | 工数 |
|------|--------|------|
| 🔴 | 全社ボード確認（セッション開始必須） | — |
| 🔴 | **TYPE A〜Dテンプレートリファクタリング** | 2h |
| 🔴 | **Phase 2：YouTube自動収集 n8n WF本体構築** | 3h |
| 🔴 | **YAMLフロントマター+マルチコピー方式実装** | 2h |

### 🟡 今週中
| 優先 | タスク | 工数 |
|------|--------|------|
| 🟡 | Phase 3：Claude API自動分析ノード追加 | 2h |
| 🟡 | 月次3タスクのコントラクト設計 | 1.5h |
| 🟡 | LINE月次上限（6月1日リセット待ち） | — |

### 🟡 BUN_CEO手動作業
| タスク | 工数 |
|--------|------|
| Obsidianインストール（Step 0〜6） | 30min |
| 126本を3 NotebookLMにアップロード | 30min |
| NotebookLMで質問→distilled_*.md初回蒸留 | 1h |

### 🟡 以上が終わったらやる
| タスク | 工数 |
|--------|------|
| mkt/sales/dev-skill/references/ 中身作成 | 2h |
| Phase 4：全社ボードYouTubeナレッジシート追加 | 1h |
| KENZAI向けCLAUDE.mdと競合調査スキル設計 | 3h |

---

## 完了済みタスク（2026-05-23追加）

| タスク | 完了日 |
|--------|--------|
| YouTube Data API v3 n8n登録・動作確認 | 2026-05-23 |
| YouTube検索キーワード拡充（102本・6カテゴリ） | 2026-05-23 |
| distilled_ai_agent/mkt_sales/pkm 新設 | 2026-05-23 |
| knowledge/mkt・sales・pkm・kaigo GitHub作成 | 2026-05-23 |
| REPORT_FORM_GUIDE Layer B結晶化サイクル明文化 | 2026-05-23 |
| 126本 3フォルダ自動仕分け | 2026-05-23 |
| MKT_PR・SALES_PR✅・FIN月次✅・GitHub監査✅ 確認 | 2026-05-23 |
| FINスキルP&L4ステップ追加（v2.0） | 2026-05-22 |
| 既存4スキル v2.0リファクタリング | 2026-05-22 |
| YouTube insight 126本インデックス・蒸留ナレッジ作成 | 2026-05-22 |
| L3 DEVパイプライン✅確認 | 2026-05-22 |
| DeepSeek認証共通化修復 | 2026-05-22 |
| 福岡プラントLINE Bot完全復旧 | 2026-05-22（OPS） |

---

## 2026-05-23 確立したアーキテクチャ（重要・次セッション必読）

### knowledge/ vs skill/references/ 役割分担（確定）
- `knowledge/`（/Users/fuminariaksse/northstar-os/knowledge/）= 実装パターン・デバッグ手順（Antigravity書く）
- `skill/references/`（/Users/fuminariaksse/.claude/commands/*-skill/references/）= ドメイン専門知識・常時ロード（Claude Code管理）
- **統合不要・役割が根本的に異なる**

### Layer B結晶化サイクル（確定）
Type D指示書 → 実行 → 報告書💡 → knowledge/またはdistilled_*.md → 次のref_skills参照 → ループ

### スキル構成（2026-05-23現在）
```
coo-skill/references/
  youtube_insights_distilled.md / youtube_knowledge_index.md
  distilled_ai_agent.md ← NEW
  distilled_mkt_sales.md ← NEW
  distilled_pkm.md ← NEW
  three_tool_integration.md / obsidian_vault_design.md
  obsidian_setup_guide.md / daily_note_template.md

fin-skill/references/ ← 介護・障害福祉法令・KPI（9ファイル）
rsc-skill/references/ ← BIZ_SCORING・YouTube収集設計（102キーワード）
mkt-skill/references/ ← 空（次フェーズ）
sales-skill/references/ ← 空（次フェーズ）
dev-skill/references/ ← 空（次フェーズ）
```

---

## インフラ・技術メモ（重要）

- VPS SSH：ssh root@162.43.78.67 | n8n: http://162.43.78.67:5678
- n8n TZ=Asia/Tokyo（JST）：cronは JST値で設定
- YouTube API: docker-compose.yml の YOUTUBE_API_KEY 環境変数で管理
- N8N_BLOCK_ENV_ACCESS_IN_NODE=false を設定（$env.変数名 を WF内で使用可）
- 共通OAuthWF: http://localhost:5678/webhook/google-oauth-token
- LINE月次上限：6月1日リセット
- OPSシステム注意：appsscript.jsonにoauthScopes追加禁止（Webhookが302になる）
- バックアップ：GitHub日次（WF定義・3:00 JST）+ VPS SQLite日次（3:30 JST）

## OPSシステム注意事項（2026-05-22追加）
- appsscript.jsonにoauthScopes追加禁止: Webhookが302になる
- GASの権限再認証はGASエディタから手動実行のみ有効
- Gemini APIキーは定期更新が必要（AI Studio）
- clasp tokenが期限切れの可能性: 次回push時は clasp login が必要

# NS-OSV2 Architecture Context

更新日: 2026-05-30

## 中核構造

```
BUN_CEO
  └── COO（Codex/Claude Code/Antigravity）
        ├── Board（00_Projects/NS-OSV2_Board/）
        │     └── tickets/ [todo/doing/qa/needs_rework/blocked/error/done/archived]
        ├── AUDIT Director v1（独立内部監査人・COOから独立）
        │     ├── 自動実行: crontab 毎週金曜21:03 / 毎月最終金曜21:03
        │     ├── Provider: OpenAI gpt-5.4（切替: audit-use anthropic/openai）
        │     ├── レポート: 01_Areas/AUDIT/AUDIT_Report_*.md
        │     └── 是正追跡: 01_Areas/AUDIT/remediation_log.md
        ├── Context Packages（各部門の人格PKG）
        │     ├── BizDev: biz_director_v1 / market_intelligence_v1 / product_strategist_v1
        │     ├── MKT: mkt_director_v1 / offer_strategist_v1 / direct_response_writer_v1
        │     │        gary_vaynerchuk_sns_strategy_v1 / jay_abraham_strategy_v1 / revenue_operator_v1
        │     ├── RSC: rsc_scout_v1 / trend_scout_v1
        │     ├── SALES: sales_director_v1 / russell_brunson_sales_flow_v1
        │     │          satou_masahiro_practical_sales_v1 / brian_tracy_closing_discipline_v1
        │     ├── FIN: barry_fin_ops_v1
        │     ├── DEV: dev_director_v1 / dev_engineer_v1
        │     └── INFRA: infra_orchestrator_v1（⚠️全面書き直し中: 20260530_0001）/ coo_dispatch_agent_v1
        ├── KnowledgeBase（02_Resources/KnowledgeBase/）
        │     ├── domain_coo_operations.md
        │     ├── domain_bizdev_mkt.md
        │     ├── domain_kaigo_ops.md
        │     ├── domain_ns_os.md
        │     └── rsc_daily_patrol/
        └── COO管理ファイル（01_Areas/COO/）
              ├── ClaudeCode_Handoff_Latest.md
              ├── AI_Runner_Status_Latest.md
              └── signal_pipeline_ops_spec_20260529.md
```

## V2 の要点

- Board中心主義（Board外の仕事は禁止）
- AI同士の直接会話禁止（チケット・成果物・コンテキスト経由）
- 成果物必須・QA→COO現物確認→done
- COO実動禁止・例外条項なし（2026-05-30 BUN_CEO確定）
- latest面は入口、実チケットとアーカイブ文脈が正本
- V1参照・混用禁止（V1 WFはVPS上で並行稼働中だがV2 PKGには記述しない）

## Board ステータス（正式8種のみ）

`todo` / `doing` / `qa` / `needs_rework` / `blocked` / `error` / `done` / `archived`
※ `qa_ready` 等の非公式ステータスは禁止

## AI Runner状態（2026-05-30時点）

| AI | Status |
|----|--------|
| Codex（GPT-5.4） | offline |
| Claude Code | idle |
| Antigravity | limited |
| AUDIT Director | 自動実行（crontab） |

## パイプライン（設計済み・復旧中）

```
06:30 RSC Scout → Daily_Report → rsc_daily_patrol/
07:15 → signal_YYYYMMDD.md → BizDev/inbox/
当日中 → feedback_YYYYMMDD.md → SALES/feedback/
```
⚠️ 現状断絶中。復旧チケット: 20260530_0002

## 本命

NorthStar-OSの本命は、介護・福祉現場で忙殺されているスタッフを少しでも楽にするための総合アプリ。
年配スタッフでも使えるように、音声/OCR/PC入力のマルチ入力を前提にし、
記録/労務/請求/加算/監査までを通す。

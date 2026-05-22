# NorthStar OS — レポートフォーム統一ガイド
# 更新日: 2026-05-23
# 管理者: COO

---

## 概要

NorthStar OSで生成される全レポート・チケットの書式を5つのタイプに統一し、
各レポートにナレッジ蓄積セクション（💡）を組み込むことで、
組織の知識を体系的に蓄積・再利用する仕組みを構築する。

---

## フォーム一覧

| Type | 名称 | 用途 | テンプレートパス | 主な生成者 |
|------|------|------|-----------------|-----------|
| A | 運用レポート | 日次/週次/月次の定常運用報告 | dev/templates/reports/TYPE_A_OPS_REPORT.md | n8n WF（自動） |
| B | 開発・実装レポート | 新機能の開発・実装の記録 | dev/templates/reports/TYPE_B_DEV_REPORT.md | DEV-AI / COO |
| C | デバッグレポート | 障害・エラーの調査・解決の記録 | dev/templates/reports/TYPE_C_DEBUG_REPORT.md | DEV-AI / COO |
| D | COO指示書（チケット） | チケットの標準書式 | dev/templates/tickets/TYPE_D_COO_TICKET.md | COO |
| E | 調査・分析レポート | 競合調査・法改正分析・技術検証 | dev/templates/reports/TYPE_E_RESEARCH_REPORT.md | 各部門AI |

---

## 使い分けフローチャート

```
タスクの発生
    ↓
何をやる？
├── 新しいものを作る → Type B（開発・実装レポート）
├── 壊れたものを直す → Type C（デバッグレポート）
├── 定常的な報告      → Type A（運用レポート）
├── 何かを調べる      → Type E（調査・分析レポート）
└── 誰かに指示する    → Type D（COO指示書/チケット）
```

---

## 各Typeの必須セクション

### 全Type共通

| セクション | 目的 |
|-----------|------|
| ⚡ サマリー / 📋 概要 | BUN_CEOが30秒で把握 |
| 💡 ナレッジ / スキル化候補 | 知識蓄積の起点 |
| ➡️ 次のアクション | 連続性の担保 |

### Type別の特徴セクション

| Type | 特徴セクション | 目的 |
|------|--------------|------|
| A | 📊 詳細 / 🔴 要アクション | 定常報告の構造化 |
| B | 🔧 技術的アプローチ / ✅ テスト結果 | 設計判断の記録・品質担保 |
| C | 🔍 根本原因 / 🛡️ 再発防止策 / 💡 パターン登録 | 障害の体系的記録 |
| D | yaml メタデータ / ref_skills / 成功条件 | インプットの統一 |
| E | 🎯 調査目的 / 📊 調査結果（事実/分析分離） | 客観的分析の担保 |

---

## ナレッジシステム（knowledge/）との連携

### 全体フロー（Layer B 結晶化サイクル）

```
COO指示書（Type D）発行
        ↓
各部門AIが実行
        ↓
報告書（Type A/B/C/E）の「💡ナレッジ」セクションに記録
        ↓
        COO判定
  ┌── 実装パターン（n8n/API/デバッグ）
  │       → knowledge/[分野]/ に登録（Antigravity側）
  ├── ドメイン専門知識（法令/KPI/業務手順）
  │       → skill/fin-skill(or mkt/sales)/references/ に登録（Claude Code側）
  └── YouTube収集・MKT/SALES実行結果
          → skill/coo-skill/references/distilled_[カテゴリ].md に追記
                  ↓
          月1回：distilledを集約 → YouTube自動蒸留サイクル

knowledge/ / skill/references/ / distilled_*.md に蓄積された知識
        ↓
次のType Dチケットの「ref_skills:」に記載
        ↓
実行AIが参照 → 解決時間・コスト削減 → さらに良い報告書
        ↓
      （ループ継続：バリーが育ち続ける）
```

**このループこそがNorthStar OSの競争優位の源泉。**
- 介護ドメイン知識（fin-skill/references/）= **不変の核（バリーの専門知識）**
- YouTube蒸留・実行結果（distilled_*.md）= **動的経験値（バリーの継続学習）**
- 実装パターン（knowledge/）= **作業効率化（バリーの引き出し）**

### knowledge/ ディレクトリ構造

```
knowledge/
├── README.md              ← 運用ルール・登録フロー
├── n8n/                   ← n8nワークフロー関連
├── api/                   ← 外部API連携
├── ops/                   ← 労務・OPS関連
├── debug/                 ← デバッグ共通
├── dev/                   ← 開発パターン
├── infra/                 ← インフラ
├── mkt/                   ← MKT実行知見（自動収集WF稼働後に蓄積）
├── sales/                 ← SALES実行知見（PRタイムズ・Playwright結果）
├── pkm/                   ← Obsidian・NotebookLM活用パターン
├── kaigo/                 ← 介護・障害福祉ドメイン知識
└── youtube-insights/      ← YouTube週次収集の蒸留ナレッジ（Layer 2）
    ├── ai_agent/
    ├── mkt_sales/
    └── pkm/
```

### skill/references/ との役割分担（重要）

knowledge/ と Claude Code の skill/references/ は **別物**。混同しない。

| 保管場所 | 対象知識 | 更新タイミング |
|---------|---------|--------------|
| `knowledge/` (Antigravity側) | 実装パターン・デバッグ解決手順・WF設計ノウハウ | 事故・実装完了のたびに即時 |
| `skill/references/` (Claude Code側) | ドメイン専門知識・法令・KPI基準・定常業務ルール | 法改正・月次レビュー・YouTube蒸留サイクル |

**Type D の `ref_skills` に書く際は両方を参照できる：**
```yaml
ref_skills:
  - knowledge/n8n/oauth_unified_pattern           # Antigravity knowledge/
  - skill/fin-skill/references/shogukaizen_rules  # Claude Code skill/references/
```

### 登録済みナレッジ一覧（2026-05-23現在）

| パターン名 | 分野 | 信頼度 | 概要 |
|-----------|------|--------|------|
| oauth_unified_pattern | n8n | high | 共通OAuth WFによるtoken一括管理 |
| http_request_json_body | n8n | high | HTTP Request v4のJSON Body正しい使い方 |
| error_workflow_setup | n8n | high | 全WFへのerrorWorkflow一括設定 |
| drive_multipart_upload | api | high | Google Drive multipartアップロード |
| line_messaging_api | api | high | LINE Harness経由の通知送信 |
| credential_rotation | debug | high | APIキー流出時のcredential更新手順 |

---

## ファイル命名規則（フォーム統一版）

| Type | ファイル名 | 例 |
|------|-----------|-----|
| A | [部門]_[内容]_YYYYMMDD.md | RSC_介護動向_20260520.md |
| B | DEV_[機能名]_YYYYMMDD.md | DEV_共通OAuth構築_20260520.md |
| C | DEBUG_[対象]_YYYYMMDD.md | DEBUG_夕リフレクション_20260520.md |
| D | YYYYMMDD_HHMM_[部門]_[タスク名].md | 20260520_0900_DEV_KENZAI修正.md |
| E | [部門]_[調査テーマ]_YYYYMMDD.md | MKT_競合機能ベンチマーク_20260518.md |

---

## WFプロンプトへの統一フォーム適用（Phase 3）

### 対象WFとType対応

| WF | WF ID | 適用Type |
|----|-------|---------|
| RSCリサーチ巡回 | 796EUn4zvboKFQiP | Type A |
| MKT_PRタイムズ4エージェント | ht60IBCItF9vt1vO | Type A + Type E |
| MKT_SNSコンテンツ | YGacVsIyaf43mfG2 | Type A |
| BizDevスキャン | 0zftWq8EAnbcJwrE | Type A + Type E |
| Signal DB週次分析 | wxJUU8dPwbWqFyGP | Type E |
| FIN月次レポート | uxIDllsGUiDilADI | Type A |
| 部門日次報告 | 4LTj5vfwCcDqVUKc | Type A |
| System QA夜間 | dSItw958pDfl3fMs | Type C（障害検知時） |
| YouTube自動ナレッジ収集（新設） | — | Type E |

---

## 品質基準

| 基準 | 内容 |
|------|------|
| 省略禁止 | 「以下略」「...」は職務放棄 |
| 事実とデータ | 感想・推測ではなく数字と事実で記述 |
| 再現可能性 | 第三者が読んで同じ作業を再現できる粒度 |
| ナレッジ記述 | 💡セクションは「なし」でも記述必須。空欄禁止 |
| 成果物保存 | Google Drive Reports/[部門]/ に保存してから完了 |

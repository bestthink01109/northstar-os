# NorthStar OS — レポートフォーム統一ガイド
# 更新日: 2026-05-20
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

### 全体フロー

```
問題発生・作業実施
        ↓
レポートの「💡スキル化候補」セクションに記録
        ↓
     判定（COO）
  ┌── 再利用性高い ──→ knowledge/ に登録
  └── 一回限り ──────→ レポートのみ保存

knowledge/ に蓄積された知識
        ↓
次の同様タスクのチケット（Type D）の「ref_skills:」に記載
        ↓
実行AIが参照 → 解決時間・コスト削減
```

### knowledge/ ディレクトリ構造

```
knowledge/
├── README.md              ← 運用ルール・登録フロー
├── n8n/                   ← n8nワークフロー関連
│   ├── oauth_unified_pattern.md      ← OAuth一括管理
│   ├── http_request_json_body.md     ← HTTP Request JSON Body
│   └── error_workflow_setup.md       ← エラーWF設定
├── api/                   ← 外部API連携
│   ├── drive_multipart_upload.md     ← Driveアップロード
│   └── line_messaging_api.md         ← LINE通知
├── ops/                   ← 労務・OPS関連（将来追加）
├── debug/                 ← デバッグ共通
│   └── credential_rotation.md        ← Credential更新
├── dev/                   ← 開発パターン（将来追加）
└── infra/                 ← インフラ（将来追加）
```

### 登録済みナレッジ一覧（2026-05-20現在）

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

n8n WFのプロンプトを統一フォームに準拠させる:

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

### プロンプト改修方針

各WFのAI呼び出しプロンプトに以下を追加:

```
## 出力フォーマット指定

以下のフォーマットに従って出力してください。省略禁止。

[Type A/B/C/Eのテンプレート構造を挿入]

特に「💡 今回のナレッジ」セクションは必ず記述してください。
新規ナレッジがない場合は「新規ナレッジなし」と明記してください。
```

---

## 品質基準

| 基準 | 内容 |
|------|------|
| 省略禁止 | 「以下略」「...」は職務放棄 |
| 事実とデータ | 感想・推測ではなく数字と事実で記述 |
| 再現可能性 | 第三者が読んで同じ作業を再現できる粒度 |
| ナレッジ記述 | 💡セクションは「なし」でも記述必須。空欄禁止 |
| 成果物保存 | Google Drive Reports/[部門]/ に保存してから完了 |

---

## Claude Code スキル登録

knowledge/ に蓄積されたパターンのうち、以下の条件を満たすものはClaude Codeのskillとしても登録可能:

- 繰り返し実施するデバッグ手順
- n8nの典型的な修正パターン
- レポート生成の定型処理
- COO判断の定型ロジック

登録場所: Claude Codeのメモリ / CLAUDE.md / .claude/ 配下

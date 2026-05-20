# NorthStar OS — ナレッジベース（knowledge/）

> 日々の作業から得られた再利用可能な知識を蓄積・管理するリポジトリ。
> COOセッションで発見したパターン・決定事項・スキル候補をここに集約する。

---

## ディレクトリ構成

```
knowledge/
├── README.md              ← このファイル（全体インデックス・使い方）
├── n8n/                   ← n8nワークフロー関連パターン
│   ├── oauth_unified_pattern.md
│   ├── http_request_json_body.md
│   └── error_workflow_setup.md
├── api/                   ← 外部API連携パターン
│   ├── drive_multipart_upload.md
│   └── line_messaging_api.md
├── ops/                   ← 労務・OPS関連パターン（将来追加）
├── debug/                 ← デバッグ共通パターン
│   └── credential_rotation.md
├── dev/                   ← 開発パターン（将来追加）
├── infra/                 ← インフラ・VPS関連パターン（将来追加）
├── decisions/             ← 重要な意思決定の記録
│   └── 20260520_基盤整備完了.md
└── skills/                ← Claude Codeスキル候補（3回以上登場で昇格）
    └── templates/
        └── skill_template.md
```

---

## ナレッジエントリの書式

各ナレッジファイルは以下のYAMLフロントマター + Markdown本文で構成する:

```yaml
---
pattern_name: "パターン名（英語snake_case）"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
author: "COO / DEV-AI / RSC-AI 等"
tags:
  - n8n
  - OAuth
  - API
source_reports:
  - "DEBUG_夕リフレクション_20260520.md"
  - "DEV_共通OAuth構築_20260520.md"
applicable_scene: "このパターンを使うべき場面の説明"
confidence: high  # high / medium / low / deprecated（実証済みかどうか）
---
```

---

## 使い方

### 1. パターンを登録する（作業後）

レポートの「💡スキル化候補」セクションで記録されたパターンを該当分野ディレクトリに登録する。

登録先の選び方：
| 内容 | 登録先 |
|------|-------|
| n8nノード設定・エラー対処 | n8n/ |
| 外部API呼び出し・認証 | api/ |
| シフト計算・給与・帳票 | ops/ |
| デバッグ共通手順 | debug/ |
| 開発・実装パターン | dev/ |
| インフラ・VPS | infra/ |

### 2. 決定事項を記録する（重要判断後）

経営・技術・業務に関わる重要な決定は `decisions/YYYYMMDD_タイトル.md` として保存する。
後から「なぜそう決めたか」を参照できるようにする。

### 3. スキル候補を登録する

繰り返し使えるパターンが3回以上登場したら `skills/` にスキル候補として登録する。
テンプレートは `skills/templates/skill_template.md` を使う。

---

## 登録フロー

```
レポート作成（Type A〜C）
    ↓
「💡スキル化候補」セクションに記録
    ↓
COOが判定
├── 再利用性 高 → knowledge/[分野]/ に登録
│     └── pattern_name でファイル作成
│     └── チケットテンプレートの ref_skills に追加可能に
└── 再利用性 低 → レポートのみ保存（knowledge/には登録しない）

knowledge/ に蓄積
    ↓
次の類似タスクのチケット（Type D）
    └── ref_skills: にパターン名を記載
    └── 参照ナレッジセクションにリンク
    ↓
解決時間・APIコスト削減

3回以上登場
    ↓
skills/ にスキル候補として昇格
    ↓
Claude Code の skills/ に実装 → テスト → 本番運用
```

---

## 蓄積ルール

1. 作業後即登録 — セッション終了前に必ずパターン/決定事項を記録する
2. 省略禁止 — 「後で書く」は消滅と同義。必ずその場で書く
3. 具体的に書く — 「エラーが出た」ではなく「HTTP 400 + 原因 + 解決コード」まで書く
4. 日付を付ける — すべてのエントリに確認日を付与する
5. 重複を統合 — 同じパターンが複数回登場したら既存エントリを更新し件数を増やす
6. 削除禁止 — 陳腐化した場合は `confidence: deprecated` に変更
7. ファイル名統一 — `pattern_name` と一致させる（英語snake_case.md）

---

## タグ一覧（分類用）

| タグ | 対象 |
|------|------|
| n8n | n8nワークフロー全般 |
| OAuth | Google OAuth認証 |
| API | 外部API連携 |
| LINE | LINE Messaging API |
| Drive | Google Drive操作 |
| Sheets | Google Sheets操作 |
| VPS | VPSインフラ・systemd |
| GitHub | GitHub操作・チケット管理 |
| 労務 | 労務計算・給与・シフト |
| MKT | マーケティング関連 |
| SALES | 営業関連 |
| debug | デバッグ手法 |
| security | セキュリティ・認証情報管理 |

---

## 検索方法

チケット作成時に参照すべきナレッジを探す場合:

```bash
# タグで検索
grep -rl "tags:.*n8n" knowledge/

# パターン名で検索
grep -rl "pattern_name:.*oauth" knowledge/

# エラーメッセージで検索
grep -rl "JSON Body not valid" knowledge/
```

---

## 索引（最終更新: 2026-05-20）

### n8n/
| パターン名 | 確認日 | 信頼度 | 概要 |
|-----------|--------|--------|------|
| oauth_unified_pattern | 2026-05-20 | high | 共通OAuth WFによるtoken一括管理 |
| http_request_json_body | 2026-05-20 | high | HTTP Request v4のJSON Body正しい使い方 |
| error_workflow_setup | 2026-05-20 | high | 全WFへのerrorWorkflow一括設定 |

### api/
| パターン名 | 確認日 | 信頼度 | 概要 |
|-----------|--------|--------|------|
| drive_multipart_upload | 2026-05-20 | high | Google Drive multipartアップロード |
| line_messaging_api | 2026-05-20 | high | LINE Harness経由の通知送信 |

### debug/
| パターン名 | 確認日 | 信頼度 | 概要 |
|-----------|--------|--------|------|
| credential_rotation | 2026-05-20 | high | APIキー流出時のcredential更新手順 |

### decisions/
- [20260520_基盤整備完了](decisions/20260520_基盤整備完了.md) — LINEプラン・バックアップ・SNS展開等の方針確定

### skills/
- skill_template.md（テンプレートのみ、候補未登録）

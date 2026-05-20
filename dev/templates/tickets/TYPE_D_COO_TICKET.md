---
# NorthStar OS — Type D: COO指示書（チケット）テンプレート
# このテンプレートはtickets/todo/に配置するチケットの標準書式
# ファイル名: YYYYMMDD_HHMM_[部門]_[タスク名].md
# 更新日: 2026-05-20
---

```yaml
# === チケットメタデータ（必須） ===
layer: L1          # L1(テンプレ・¥0) / L2(claude --print・¥10-30) / L3(フルエージェント・¥100-800)
dept: DEV          # DEV / RSC / MKT / SALES / FIN / OPS
priority: high     # critical / high / medium / low
estimated_cost: ¥0 # 概算APIコスト

# === ナレッジ連携（重要） ===
knowledge_area: n8n           # n8n / API / LINE / OPS / Drive / OAuth / Sheets / 労務 / SALES / MKT
ref_skills:                    # 参照すべき既存スキル・パターン（knowledge/から検索）
  - n8n_oauth_token_pattern    # 例: OAuthトークン取得パターン
  - drive_multipart_upload     # 例: Driveマルチパートアップロード
related_tickets:               # 関連チケット（過去の類似作業）
  - 20260518_0300_DEV_KENZAI会社設定タブ追加

# === テンプレート指定（L1のみ） ===
template: none     # line-notify / drive-read / drive-write / schedule-claude / http-get / error-alert / webhook-trigger / drive-to-line / none
vars:              # テンプレート変数（L1使用時のみ）
  # - KEY: value
```

---

## 背景・目的（なぜやるか）

<!-- 
  このタスクが必要な理由を1〜3文で記述
  BUN_CEOの判断3軸との関連:
  1. OPS自動化を加速させるか？
  2. 1日1時間経営に近づくか？
  3. 月200万円の自動収益につながるか？
-->

（ここに記述）

---

## 具体的な指示

<!-- 
  実行AIが迷わない粒度で指示を記述
  曖昧な表現禁止（「適切に」「いい感じに」等は職務放棄）
  入力データ・出力先・ファイル名を明示
-->

1. （ステップ1）
2. （ステップ2）
3. （ステップ3）

---

## 成功条件

<!-- 
  完了とみなす客観的・検証可能な条件を列挙
  「動くこと」ではなく「何がどう動くか」を数値・事実で定義
-->

- [ ] （条件1）
- [ ] （条件2）
- [ ] （条件3）
- [ ] 成果物がGoogle Drive Reports/[部門]/ に保存されていること
- [ ] 全社ボードに反映されていること

---

## 参照ナレッジ

<!-- 
  knowledge/ ディレクトリ内の関連パターンへのリンク
  過去の類似タスクのレポートへの参照
  ref_skillsに書いたものの詳細を展開
-->

| パターン名 | ファイル | 適用箇所 |
|-----------|---------|---------|
| （例）n8n OAuth統一パターン | knowledge/n8n/oauth_unified_pattern.md | OAuth認証部分 |

---

## 制約・注意事項

<!-- 省略可。ただし以下に該当する場合は必須記述 -->

- APIコスト上限: （月次上限との関連）
- BUN_CEO判断必要事項: （お金・契約・方向性・OPS現状に該当する場合のみ）
- 依存タスク: （先行タスクがある場合）
- セキュリティ注意: （APIキー・個人情報を扱う場合）

---
# NorthStar OS — Type D: COO指示書（チケット）テンプレート
# このテンプレートはtickets/todo/に配置するチケットの標準書式
# ファイル名: YYYYMMDD_HHMM_[部門]_[タスク名].md
# 更新日: 2026-05-23（リファクタリング v2.0）
---

```yaml
# === チケットメタデータ（必須） ===
layer: L1          # L1(テンプレ・¥0) / L2(claude --print・¥10-30) / L3(フルエージェント・¥100-800)
dept: DEV          # DEV / RSC / MKT / SALES / FIN / OPS
priority: high     # critical / high / medium / low
estimated_cost: ¥0 # 概算APIコスト

# === ナレッジ連携（重要） ===
knowledge_area: n8n           # n8n / API / LINE / OPS / Drive / OAuth / Sheets / 労務 / SALES / MKT / kaigo / youtube
ref_skills:                    # 参照すべき既存スキル・パターン
  # knowledge/ (実装パターン・デバッグ手順)
  - knowledge/n8n/oauth_unified_pattern
  # skill/references/ (ドメイン専門知識)
  - skill/fin-skill/references/shogukaizen_rules
related_tickets:
  - （類似の過去チケットID）
template: none     # line-notify / drive-read / drive-write / schedule-claude / http-get / error-alert / webhook-trigger / drive-to-line / none
vars:
  # - KEY: value
```

---

## 🚨 CRITICAL（チケット起票前チェック）

**以下を全て満たしていないチケットは受理しない。**

- [ ] 具体的な指示にステップ番号が振られているか
- [ ] 成功条件が「数値・事実」で定義されているか（「動くこと」「確認できること」は不可）
- [ ] 入力データのパス・ファイル名・IDが明記されているか
- [ ] 出力先（Drive フォルダID / GitHubパス / VPSパス）が明記されているか
- [ ] APIコスト上限が設定されているか（L3は必須・上限¥800）
- [ ] BUN_CEO判断が必要な事項を先に確認済みか

---

## 背景・目的（なぜやるか）

<!-- BUN_CEOの判断3軸との関連を明記:
  1. OPS自動化を加速させるか？
  2. 1日1時間経営に近づくか？
  3. 月200万円の自動収益につながるか？ -->

（ここに記述）

---

## 具体的な指示

<!-- 曖昧な表現禁止（「適切に」「いい感じに」「確認して」は職務放棄）
  入力データ・出力先・ファイル名を必ず明示 -->

1. （ステップ1：「〜を実行し、〜を確認する」形式で）
2. （ステップ2）
3. （ステップ3）

---

## 成功条件（done-の定義）

<!-- 完了とみなす客観的・検証可能な条件。数値・事実で定義 -->

- [ ] （条件1：例「n8n実行IDが返り、statusがsuccessであること」）
- [ ] （条件2：例「Drive Reports/DEV/にファイルが存在し、サイズが1KB以上であること」）
- [ ] 成果物がGoogle Drive Reports/[部門]/ に保存されていること
- [ ] 全社ボード成果物管理に登録されていること
- [ ] TYPE Bレポート（DEV_[機能名]_YYYYMMDD.md）が作成されていること

---

## 参照ナレッジ

| パターン名 | ファイル | 適用箇所 |
|-----------|---------|---------|
| （例）n8n OAuth統一パターン | knowledge/n8n/oauth_unified_pattern.md | OAuth認証部分 |

---

## 制約・注意事項

- APIコスト上限: ¥（月次¥10,000上限との関連）
- BUN_CEO判断必要事項: （お金・契約・方向性・OPS現状に該当する場合のみ）
- 依存タスク: （先行タスクがある場合）
- セキュリティ注意: （APIキー・個人情報を扱う場合）
- イテレーション上限: 3回（3回失敗したらBUN_CEOに報告）

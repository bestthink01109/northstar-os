# distilled_ai_agent.md
# AIエージェント設計・Claude技術・n8n実装 蒸留ナレッジ
# 更新日: 2026-05-23
# 更新ルール: YouTube収集・実装完了・事故のたびに追記しろ。空欄禁止

---

## 1. AIエージェント成熟度4段階（NS-OSの現在地判定に使え）

| Level | 定義 | NS-OS現在地 |
|-------|------|------------|
| L1 | フレームワーク依存・PMF探索中 | — |
| L2 | 独自ループ実装・5ルール実践 | ✅ ここにいる |
| L3 | 複数エージェント並列・カンバンUX | → 移行中 |
| L4 | クラウドデプロイ・完全自律稼働 | 2027年目標 |

**Level2の5つの必須ルール：**
1. 状態機械として設計しろ
2. 追加するものすべてがリスク
3. pseudo-RL対応（成功パターンを強化）
4. スロップを作るな
5. フロンティアラボのロックダウンを監視しろ

## 2. スキル設計3原則（Anthropic Barry & Mahes）

| 原則 | 内容 |
|------|------|
| 重複排除 | 同じ知識を2箇所に書くな |
| スキップ防止 | 重要なことはCRITICAL冒頭に置く |
| 断言形式 | 「〜すべき」でなく「〜する」で書く |

> 「300IQの天才より経験豊富な専門家を選ぶ。スキルがその専門家を作る。」
> 「スキップされうるものはスキップされる。重要なことは無視できない場所に置け。」

## 3. エージェント必要性の4軸チェック

1. 複雑性：単純なif-thenで解決できるか？
2. 価値：月間節約価値が5,000円を超えるか？
3. クリティカルケイパビリティ：推論・判断が必要か？
4. エラーコスト：法定計算に関わるか？→人間レビュー必須

## 4. GANパターン（品質担保）

Generator AI → 出力 → Adversary AI（評価・批判）→ 合格なら出力

NS-OS適用：DEV QA（DeepSeek）✅ / System QA（GPT-4o）✅

## 5. n8n × Claude API 実装知見（実運用から）

**安定設定（docker-compose.yml）：**
- NODE_FUNCTION_ALLOW_BUILTIN=crypto
- N8N_BLOCK_ENV_ACCESS_IN_NODE=false（$env.変数名 を使う場合）

**よくあるエラー：**
- access to env vars denied → N8N_BLOCK_ENV_ACCESS_IN_NODE=false を追加
- Referenced node doesn't exist → ノード名参照を確認
- HTTP Request JSON Body不正 → specifyBody:json + jsonBody フィールド

## 6. 役割分担の原則

1エージェントに複数の役割を持たせない。
台本係・素材係・QA係・保存係は別エージェント。
NS-OS部門エージェントの分離設計はこの原則に合致している ✅

## 更新ルール
- 新しいAI技術・Claude API変更 → 即追記
- WF事故から学んだパターン → 即追記
- YouTube収集WF稼働後 → 月次でNotebookLM質問して追記

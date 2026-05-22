# distilled_pkm.md
# PKM・Obsidian・NotebookLM・個人成長 蒸留ナレッジ
# 更新日: 2026-05-23
# 更新ルール: Obsidian運用・NotebookLM活用で得た知見を随時追記しろ

---

## 1. Obsidian × NS-OS 連携の核心設計

PARAフォルダ（NS-OS連携版）：
- Projects/ ← 現在進行中のNS-OSプロジェクト
- Areas/    ← 継続的な責任領域（MKT/SALES/FIN/OPS/COO）
- Resources/ ← fin-skill/references/と連動
- Archives/ ← 完了プロジェクト・過去レポート

Claudian設定の3ポイント：
1. claude-desktop型プラグイン = .mdファイルとしてClaude Codeと相互運用
2. OpenCode経由でOllama（ローカルLLM）とも連携可
3. デイリーノートテンプレートをDashboard 7セクション構造に合わせて設計済み ✅

## 2. NS-OS × Obsidian × NotebookLM 3点連携

| ツール | 役割 |
|--------|------|
| NS-OS (n8n + Claude) | 自動収集・分析・実行 |
| Obsidian | 思考整理・デイリーログ |
| NotebookLM | 126本+の横断検索・質問 |

情報の流れ：YouTube収集WF → individual/MD → NotebookLM
→ 質問で即答 → 重要回答をdistilled_*.mdに追記 → COOが常時ロード

## 3. NotebookLM 有効な質問パターン

会社用：
「スキルファイルを正しく設計するための原則を動画ごとに引用して」
「n8nとClaudeの組み合わせで複数の動画が共通して注意した点を全て教えて」
「コントラクト（done-の定義）について複数の動画がまとめた内容を教えて」

個人用：
「1日1時間経営を実現する方法を全動画から引用して」
「燃え尽き・疲れへの対処法を全動画からまとめて」

⚠️ 126本のアップロード完了後に使え（現時点未実施）

## 4. 個人成長・精神的断捨離

3軸でシンプル化：
- お金：キャッシュレス統一
- 人間関係：消耗する関係から距離を置く
- 思考・習慣：「気にすること」の数を減らす

停滞感が出たとき：
「2031年のゴールへの近さを0〜10で表すと今は何点？」
「1点上げるために今週できる最も小さなことは？」

## 5. PKMツール選択基準

| 問い | ツール |
|------|--------|
| 複数動画の横断検索 | NotebookLM |
| 今日の思考・行動ログ | Obsidian |
| 朝の行動方針決定 | Obsidianデイリーノート |

## 更新ルール
- NotebookLMで有効だった質問と要点 → 追記（「Q:...→要点:...」形式）
- Claudianの新設定で効いたもの → 追記
- 月1回 NotebookLMサイクルでdistilled全体を見直す

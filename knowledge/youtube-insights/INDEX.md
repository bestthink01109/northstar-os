---
# YouTube Insight ナレッジ インデックス
# 更新日: 2026-05-22
# 総動画数: 126本
# 用途: 必要な時に「どの動画を見ればいいか・何が書いてあったか」を素早く引き出す
---

## 3層ナレッジ構造

```
Layer 1【即座に検索】NotebookLM
  → 全126本の文字起こしをアップロード
  → 「Claude Proリミット時の対処法は？」→ 引用付きで複数動画から即答

Layer 2【テーマ別蒸留】knowledge/youtube-insights/
  → このファイル（インデックス）+ DISTILLED.md

Layer 3【常時ロード】references/（スキルライブラリ）
  → 既にここに結晶化済み（kaigo_kpi_standards等）
```

## NotebookLM アップロード計画（BUN_CEO手動作業）

ファイルパス：`/Users/fuminariaksse/youtube-insight/output/individual/`

| Notebook | 内容 | 本数 |
|---------|------|-----|
| NS-OS改善・AI設計 | AIエージェント・スキル・Claude Code・ビジネス系 | 約40本 |
| 個人成長・Obsidian | Obsidian・生産性・マインドセット | 約46本 |
| シリコンバレー・UX | キャリア・デザイン・英語 | 約40本 |

## 分析状態サマリー

| 状態 | 本数 |
|------|-----|
| ✅ 詳細分析済 | 10本 |
| ✅ 概要分析済 | 15本 |
| 📄 文字起こしのみ（NotebookLMで検索可能） | 101本 |
| **合計** | **126本** |

## カテゴリ別 全動画リスト

### 🤖 AIエージェント・設計（9本）
- Anthropic_エージェントを作るのではなくスキルを作ろう ✅ | スキル4層・プログレッシブディスクロージャー
- AIにおけるハーネス詳細解説 ✅ | ハーネス6要素・ベリファイ・ガードレール
- Build_Agents_That_Run_for_Hours ✅ | コントラクト・GANパターン・12時間エージェント
- 効果的なエージェントの育成方法 ✅ | 4軸チェックリスト・3要素・スロップ禁止
- 使い物にならないものを作るな_AIエージェント成熟度4段階 ✅ | Level1-4・状態機械
- スキルとMCPを組み合わせてコンテキストギャップを埋める ✅ | 3原則・evals
- エージェントはスタンドアップを行わない ✅ | ポストエンジニア・組織設計
- AnyToAny_ネイティブマルチモーダルエージェント構築 ✅ | Gemini・PDF処理・2フェーズ
- AIエージェントが生む「新・階級社会」📄 | 階級社会・ポジショニング

### 📚 スキル・Claude Code設計（14本）
- 5分でClaudeを優秀な部下にする方法 📄 | スキル設計・非エンジニア
- 非エンジニアでもClaude_Skillsは自作できる 📄 | スキル自作・3つの方法
- 非エンジニア向けClaudeサブエージェントの3つの使い方 📄 | サブエージェント・品質維持
- 非エンジニアの為の「AIエージェント」完全講義 📄 | 完全講義
- Claude_Codeでマーケティングを自動化 ✅ | 5スキル連鎖・CLAUDE.md
- ClaudeCodeで動画工場を作ったら、_1人で月240本 ✅ | 役割分担・事故ドリブン
- 【Claude_Code完全入門】 📄 | 入門・基礎
- これさえ見ればClaude_Codeぜんぶキャッチアップ 📄 | 総まとめ
- 【爆速起業】Claude_Code 📄 | 起業・副業
- 【初心者OK】AI社員に仕事を任せる方法 📄 | AI社員・会社経営
- 【一人社長】Claudeで会社を作ってAI社員を育てる 📄 | 一人社長
- Claude_codeで作る、最も理想的なタスク管理アプリ 📄 | タスク管理
- 資料を「動画」で撮ってAIに投げるだけ 📄 | マルチモーダル
- みかみ_AI業務自動化ゼロから実演 ✅ | 業務自動化・実演

### 🍃 Obsidian・生産性（26本）
（全タイトルは coo-skill/references/youtube_knowledge_index.md を参照）

### 💰 ビジネス・NS-OS改善（6本）
- 月次P&Lを4つのスキルに通したらコンサル並みの分析 ✅ | P&L 4ステップ
- AIツールを追うな。年200時間を奪う『スペック病』 ✅ | スペック病・モジュラー思考
- 3000時間の結論を20分で教えます ✅ | マルチスタック・AI正解スタック
- AIエージェントが生む「新・階級社会」 📄 | 階級社会・差別化
- AI時代_「作れない人」はマジで腐る 📄 | 作れる人・AIワークフロー
- Githubの情報漏洩がヤバすぎる…Google_IO_2026 ✅ | セキュリティ・Gemini 3.5

### 🔐 セキュリティ・AI論（5本）
（詳細は coo-skill/references/youtube_knowledge_index.md）

### 🧠 マインドセット・個人成長（19本）
（詳細は coo-skill/references/youtube_knowledge_index.md）

### 🌏 シリコンバレー・海外キャリア（23本）
（詳細は coo-skill/references/youtube_knowledge_index.md）

### 🎨 UX・デザイン（15本）
（詳細は coo-skill/references/youtube_knowledge_index.md）

## 更新ルール

- 新しい動画を分析したら状態を📄→✅に更新しろ
- NotebookLMで有益な回答が得られたら DISTILLED.md に追記しろ

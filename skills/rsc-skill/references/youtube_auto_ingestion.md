---
# YouTube自動ナレッジ収集パイプライン 設計書
# 更新日: 2026-05-22
# 用途: MKT・SALES・AI技術カテゴリのYouTube動画を自動収集・分析・蓄積する仕組み
---

## 全体アーキテクチャ

```
YouTube Data API v3（週次検索）
    ↓ キーワード×カテゴリで新着動画を取得
品質フィルター（YouTube版BIZ_SCORING・60点以上のみ）
    ↓
文字起こし取得（YouTube字幕）
    ↓
Claude API で PART1自動分析（カテゴリ別プロンプト）
    ↓
individual/ フォルダに保存 + Obsidian
    ↓
LINE通知 → BUN_CEO確認（任意）
```

## 検索カテゴリ × キーワード

### MKT
- SNS自動化 Claude / コンテンツマーケティング AI / X Twitter 自動投稿
- インスタグラム AI マーケティング / note AI 集客
- Claude Code marketing automation / AI content marketing

### SALES
- 営業 AI 自動化 / 介護 営業 顧客獲得 / LINE 営業 自動化
- sales automation AI / CRM AI integration

### AI技術
- Claude Code 使い方 / AIエージェント 自動化 / n8n AI workflow
- Claude スキル 作り方 / Anthropic 新機能 / MCP server 使い方

## 品質フィルター（60点以上のみ収集）

| 軸 | 基準 | 満点 |
|----|-----|-----|
| 関連性 | NS-OSのMKT/SALES/AI技術に直接関係するか | 30 |
| 信頼性 | チャンネル登録者1000人以上・再生回数1000回以上 | 20 |
| 鮮度 | 公開から30日以内 | 20 |
| 実用性 | 実装・手順・事例が含まれているか | 20 |
| 時間 | 5〜60分 | 10 |

**除外：** 再生500回未満 / 3分未満 or 90分超 / 既収集済み

## n8n WF設計

- スケジュール：毎週月曜 8:30 JST
- YouTube Data API v3（無料：10,000ユニット/日）
- 検索→重複チェック→品質スコア→字幕取得→Claude分析→保存→LOG→LINE通知

## YouTube APIキー取得（BUN_CEO初回設定・30分）

1. Google Cloud Console → YouTube Data API v3 を有効化
2. APIキーを作成 → n8n credentialsに登録

## 実装ロードマップ

| フェーズ | 内容 | 工数 |
|---------|------|-----|
| Phase 1 | YouTubeAPIキー取得（BUN_CEO） | 30min |
| Phase 2 | n8n WF作成（検索→品質→保存） | 3h |
| Phase 3 | Claude API自動分析追加 | 2h |
| Phase 4 | 全社ボードナレッジシート追加 | 1h |
| Phase 5 | NotebookLM API公開後に自動化 | 待機 |

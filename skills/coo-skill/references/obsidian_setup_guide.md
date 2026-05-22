---
# Obsidian × NS-OS セットアップガイド
# 更新日: 2026-05-22
# 用途: インストール後に迷わず設定できる完全手順
---

## Step 0：インストール（5分）
1. https://obsidian.md からダウンロード・インストール
2. 「新しいVaultを作成」→ 名前: `NorthStar-Brain`
3. 保存場所: `~/Desktop/NorthStar-Brain/`

## Step 1：フォルダ構造を作れ（10分）
00_Projects / 01_Areas / 02_Resources / 03_Archives / 04_Inbox を作成。
詳細構造は `obsidian_vault_design.md` 参照。

## Step 2：コアプラグイン有効化（5分）
設定 → コアプラグイン：
- [x] テンプレート → テンプレートフォルダ: `02_Resources/テンプレート`
- [x] デイリーノート → テンプレート: `02_Resources/テンプレート/朝デイリーノート.md`

## Step 3：Claudian インストール（15分）
1. 設定 → コミュニティプラグイン → 制限モードをオフ
2. 「Claudian」検索 → インストール → 有効化
3. 設定：
   - Provider: Anthropic
   - API Key: `[AnthropicのAPIキー]`
   - Model: `claude-sonnet-4-6`（または `gemini-3-5-flash`）

## Step 4：NS-OSスキルをコピー（5分）

```bash
mkdir -p ~/Desktop/NorthStar-Brain/.claude/commands/fin-skill/references
mkdir -p ~/Desktop/NorthStar-Brain/.claude/commands/rsc-skill/references
mkdir -p ~/Desktop/NorthStar-Brain/.claude/commands/coo-skill/references
cp ~/.claude/commands/fin.md ~/Desktop/NorthStar-Brain/.claude/commands/
cp ~/.claude/commands/rsc.md ~/Desktop/NorthStar-Brain/.claude/commands/
cp ~/.claude/commands/bizdev.md ~/Desktop/NorthStar-Brain/.claude/commands/
cp ~/.claude/commands/coo.md ~/Desktop/NorthStar-Brain/.claude/commands/
cp -r ~/.claude/commands/fin-skill/ ~/Desktop/NorthStar-Brain/.claude/commands/
cp -r ~/.claude/commands/rsc-skill/ ~/Desktop/NorthStar-Brain/.claude/commands/
cp -r ~/.claude/commands/coo-skill/ ~/Desktop/NorthStar-Brain/.claude/commands/
echo "✅ スキルコピー完了"
```

## Step 5：既存ナレッジの移植（30分）

| 移植元 | 移植先 |
|--------|--------|
| fin-skill/references/kaigo_kpi_standards.md | 02_Resources/介護法令/介護事業所KPI標準値.md |
| fin-skill/references/shogukaizen_rules.md | 02_Resources/介護法令/処遇改善加算ルール.md |
| rsc-skill/references/biz_scoring_examples.md | 01_Areas/RSC/BIZ_SCORING採点事例.md |
| 最新の COO_Context_*.md | 03_Archives/COO_Context_履歴/ |

## Step 6（1週間後）：arscontexta インストール
コミュニティプラグイン → `arscontexta` → インストール → API Key設定
→ 既存ノートに対して「セカンドブレイン化」を実行
→ 過去のCOO_Contextが自動連結され関連情報が浮き上がる

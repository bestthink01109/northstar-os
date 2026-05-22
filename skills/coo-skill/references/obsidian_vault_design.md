---
# NorthStar OS × Obsidian Vault 設計書
# 更新日: 2026-05-22
# 用途: BUN_CEO個人の知識管理 + NS-OSのナレッジ永続化
---

## 設計思想：PARAとNS-OSのマッピング

PARA（Projects / Areas / Resources / Archives）はNS-OSの既存構造と完全に対応している。

```
PARA         NS-OS対応                              Obsidian フォルダ
─────────────────────────────────────────────────────────────────────
Projects  ←  tickets/todo/ + doing/（期限付き作業）  → 00_Projects/
Areas     ←  n8n WF（定常業務）+ スキル              → 01_Areas/
Resources ←  knowledge/ + references/ + templates/  → 02_Resources/
Archives  ←  tickets/done/ + 過去COO_Context        → 03_Archives/
```

---

## Vault 完全構造

```
NorthStar-Brain/
├── 00_Projects/
│   ├── KENZAI開発/
│   │   ├── _index.md
│   │   ├── 進捗ログ.md
│   │   └── 決定事項記録.md
│   ├── OPS純青Python実装/
│   ├── コントラクト設計（FIN・RSC・OPS）/
│   └── SNSマルチプラットフォーム展開/
│
├── 01_Areas/
│   ├── FIN/
│   │   ├── 月次レポート手順.md
│   │   └── APIコスト管理.md
│   ├── RSC/
│   │   ├── BIZ_SCORING基準.md
│   │   └── 収集対象カテゴリ.md
│   ├── OPS/
│   │   ├── 純青_仕様書.md
│   │   └── 処遇改善加算チェック.md
│   ├── クライアント/
│   │   └── 特定施設_KPI基準.md
│   └── n8n_WF管理/
│       ├── WF一覧.md
│       └── エラー対応履歴.md
│
├── 02_Resources/
│   ├── 介護法令/
│   │   ├── 処遇改善加算ルール.md
│   │   ├── 介護報酬単価.md
│   │   └── 人員配置基準.md
│   ├── NS-OS設計/
│   │   ├── ARCHITECTURE.md
│   │   └── スキル一覧.md
│   ├── BizDev/
│   │   ├── KENZAI仕様.md
│   │   └── 競合分析.md
│   └── テンプレート/
│       ├── 朝デイリーノート.md
│       └── 週次振り返り.md
│
├── 03_Archives/
│   ├── COO_Context_履歴/
│   ├── 完了チケット/
│   └── 過去レポート/
│
└── 04_Inbox/
```

---

## COO_Context との連携設計

### セカンドブレイン化のフロー（arscontexta導入後）
```
Claude Code セッション終了
  ↓
COO_Context_YYYYMMDD_MAIN.md を Drive + GitHub に保存（現行通り）
  ↓
同じ内容を 03_Archives/COO_Context_履歴/ にコピー
  ↓
arscontexta が自動でノート同士を連結
  ↓
「3ヶ月前の同じ問題の解決策」が即座に引き出せる
```

---

## 必須プラグイン

### Step 1：インストール直後（必須）
| プラグイン | 役割 |
|-----------|------|
| Claudian | Claude Code / Gemini 3.5 Flash を呼び出す |
| Dataview | フォルダをデータベースとして検索 |
| Templater | テンプレートを変数付きで挿入 |

### Step 2：1週間後
| プラグイン | 役割 |
|-----------|------|
| arscontexta | ノートを自動連結・グラフ可視化 |
| Periodic Notes | 日次/週次/月次ノートを自動生成 |

### Step 3：スマホ連携
| ツール | 役割 |
|-------|------|
| Obsidian Sync または Syncthing | Vault をスマホと同期 |
| Remote for Obsidian（iOS） | スマホからClaude Code をリモート操作 |

---

## Claudian の設定

```
Provider: Anthropic（メイン）または Google（Antigravity 2.0）
Model: claude-sonnet-4-6 または gemini-3-5-flash
Skills path: /path/to/vault/.claude/commands/
```

既存スキル（fin.md / rsc.md / bizdev.md / coo.md）を Vault の `.claude/commands/` にコピーすれば
Claude Code と同じスキルが Claudian で即使える。

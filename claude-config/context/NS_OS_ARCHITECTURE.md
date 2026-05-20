---
# NS_OS_ARCHITECTURE | NorthStar OS
# 更新日: 2026-05-20（セッション終了版・最終）
# ※このファイルはアーキテクチャ変更時・セッション終了時に更新する
# ※全体図はこのASCIIボックス形式を必ず守り、ステータスを含めること
---

## NorthStar OS 全体アーキテクチャ図

```
╔══════════════════════════════════════════════════════════════════╗
║  BUN_CEO                                                         ║
║  【主】ダッシュボード（朝夕）議論・方向性・承認                     ║
║  【副】LINE アラート受信・緊急指示                                 ║
╚══════════════════╦═══════════════════════════════════════════════╝
                   ║
╔══════════════════▼═══════════════════════════════════════════════╗
║  COO                                                             ║
║  【主】Claude Code（このインターフェース）✅ 稼働中                 ║
║  【副】Antigravity（PC使用不可時のみ・実行は制限あり）              ║
║  役割：設計・監督・チケット起票・例外処理のみ                       ║
╚══════╦═══════════════════════════════════════╦══════════════════╝
       ║ チケット起票                           ║ 状態監視・制御
       ▼                                       ▼
╔════════════════════════╗  ╔═══════════════════════════════════════╗
║  チケットシステム        ║  ║  n8n（VPS 162.43.78.67・24/7）        ║
║  GitHub northstar-os   ║  ║                                       ║
║                        ║  ║  定期WF ✅ 稼働中                     ║
║  tickets/              ║  ║  朝7:00ブリーフィング+Dashboard        ║
║    todo/   ← 未着手    ║  ║  夕19:00リフレクション                 ║
║    doing/  ← 処理中    ║  ║  部門日次報告18:45                    ║
║    waiting/← Codex待ち ║  ║  RSCリサーチ6:00                     ║
║    done/   ← 完了      ║  ║  BizDevスキャン月曜8:00               ║
║                        ║  ║  Signal DB分析日曜4:00                ║
║  dev/templates/n8n/   ║  ║  FIN月次レポート月1日9:00              ║
║    L1テンプレ6本 ✅     ║  ║  n8nバックアップ日曜3:00              ║
║                        ║  ║                                       ║
║  dev/SPECIALIST_       ║  ║  常時Webhook ✅ 稼働中                 ║
║    PERSONAS.md ✅      ║  ║  LINEコマンド処理                     ║
║                        ║  ║  エラーアラート（全社共通）             ║
╚════════════════════════╝  ║  プリフライト3回パス                   ║
                            ║  DEV QAレビュー（DeepSeek）            ║
                            ║                                       ║
                            ║  MKT/SALES WF ✅ 稼働中（2026-05-18）  ║
                            ║  PRタイムズ4エージェント 毎日9:00       ║
                            ║  SNSコンテンツ生成 月水金10:00         ║
                            ║                                       ║
                            ║  System QA夜間 ✅ 毎日21:00 JST        ║
                            ╚═══════════════════════════════════════╝
                                           ║
╔══════════════════════════════════════════▼══════════════════════╗
║  DEVパイプライン（VPS systemd常時稼働）                          ║
║                                                                  ║
║  ticket-puller.sh ✅ 稼働中（60秒ポーリング）                    ║
║    └── L1: テンプレート適用 → done/ ✅ 動作確認済み              ║
║    └── L2: claude --print → done/ ✅ 動作確認済み               ║
║    └── L3: Claude Code DEV Agent → waiting/ ⚠️ 要修正           ║
║           （Claude Code CLIがバックグラウンドで動かない問題）      ║
║                                                                  ║
║  codex-watcher.sh ✅ 稼働中（30秒ポーリング）                    ║
║    └── waiting/ を監視 → codex exec でデバッグ → done/          ║
║                                                                  ║
║  devagentユーザー ✅ 設定済み（ANTHROPIC_API_KEY渡し修正済み）    ║
╚══════════════════════════════════════════════════════╦═══════════╝
                                                       ║
╔══════════════════════════════════════════════════════▼══════════╗
║  部門AI・専門人格エージェント                                     ║
║                                                                  ║
║  MKT部門                                                         ║
║    Jay Abraham（PRタイムズスキャン・市場機会発見）✅ 稼働中        ║
║    Alex Hormozi（オファー設計）✅ 稼働中                          ║
║    Dan Kennedy（アウトリーチ文案・4フォーミュラ）✅ 稼働中         ║
║    GPT-4o QA（Playwright自動送信時に有効化）⏳ 待機中             ║
║    Gary V + Hormozi（SNSコンテンツ週3回）✅ 稼働中               ║
║    Neil Patel（SEO WF）🔴 未実装                                 ║
║                                                                  ║
║  RSC部門                                                         ║
║    Gemini（リサーチ巡回・毎日6:00）✅ 稼働中                     ║
║                                                                  ║
║  DEV部門                                                         ║
║    Claude Code DEV Agent（L3実装）⚠️ 要修正                     ║
║    Codex CLI（デバッグ専任）✅ 稼働中                            ║
║    DeepSeek QA（WF経由）✅ 稼働中                               ║
║                                                                  ║
║  FIN部門                                                         ║
║    Claude Sonnet（月次レポート）✅ 稼働中                         ║
║    専門人格細分化 🔴 未実装                                       ║
║                                                                  ║
║  OPS部門                                                         ║
║    純青: 仕様確定済み・Python実装待ち 🔴 未実装                   ║
║    信和・共生: 仕様ヒアリング待ち 🔴 未実施                       ║
╚═══════════════════════════════════════════════╦═════════════════╝
                                                ║
╔═══════════════════════════════════════════════▼═════════════════╗
║  ストレージ・全社管理                                             ║
║                                                                  ║
║  Google Drive ✅ 稼働中                                          ║
║    Reports/{DEV/RSC/BizDev/FIN/OPS}/                            ║
║    research/Daily_Report/（Dashboard・COO_Context）              ║
║                                                                  ║
║  全社ボード（Google Sheets）✅ 自動管理中                         ║
║    チケットボード / n8n稼働ログ（エラー中WFのみ表示）              ║
║    APIコスト（DeepSeek差分自動・他0表示）/ 成果物管理              ║
║    SALES_リード管理 / システム状態 / 経営状態                     ║
║    ※全21WFにerrorWorkflow設定済み → エラー時自動アラート          ║
║                                                                  ║
║  GitHub（northstar-os）✅ 稼働中                                 ║
║    tickets/ / dev/templates/ / SPECIALIST_PERSONAS.md           ║
║                                                                  ║
║  LINE Harness ✅ 稼働中                                          ║
║    northstar-line.bestthink01109.workers.dev                    ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## ステータス凡例
| 記号 | 意味 |
|------|------|
| ✅ 稼働中 | 正常動作・本番稼働 |
| ⚠️ 要修正 | 動作するが問題あり・次セッションで修正 |
| ⏳ 待機中 | 設定済みだが条件待ち |
| 🔴 未実装 | 未着手・未構築 |

---

## VPSインフラ詳細

| 項目 | 内容 |
|------|------|
| IP | 162.43.78.67（シンVPS） |
| OS | Ubuntu 24.04.4 LTS |
| Node.js | v24.15.0 |
| Claude Code CLI | v2.1.143（/usr/bin/claude） |
| Codex CLI | v0.130.0（/usr/bin/codex） |
| Python | 3.12.3 |
| n8n | 最新（:5678） |
| SSH | ~/.ssh/vps_key（ssh-agentに登録） |

### VPSディレクトリ構造
```
/root/
├── .claude/CLAUDE.md          ← DEV Agent専用ルール
├── .config/northstar/keys.sh  ← APIキー（ANTHROPIC/OPENAI/GITHUB）
├── northstar/                 ← スクリプト置き場
│   ├── ticket_puller.sh       ✅
│   ├── apply_template.sh      ✅
│   ├── dev_agent_trigger.sh   ⚠️ L3動作に問題あり
│   ├── codex_watcher.sh       ✅
│   └── logs/
├── northstar-os/              ← GitHubクローン
│   ├── tickets/{todo,doing,waiting,done}/
│   ├── dev/templates/n8n/     ✅ 6テンプレート
│   └── workspace/
└── n8n-api.sh                 ✅
```

---

## 専門人格フレームワーク（確定 2026-05-18）

詳細：`northstar-os/dev/SPECIALIST_PERSONAS.md`
フォーミュラ集：`northstar-os/dev/templates/sales/DIRECT_RESPONSE_FORMULAS.md`

---

## 共通GoogleOAuth WF（2026-05-20新設）
```
ID: Eu3kQaH8vQpJmyqd
Webhook: http://localhost:5678/webhook/google-oauth-token
用途: 全WFのOAuth token一括発行・管理
変更方法: このWF1本だけ修正すれば全WFに反映
```

## n8n認証情報（クレデンシャルID）

| プロバイダー | ID | 用途 |
|------------|-----|------|
| Anthropic | 6RjA3eGBjtQkbNiy | 全部門AI |
| OpenAI | x2D3cGEreDX5TCzW | QA・System QA |
| Google Gemini | 8hPuwgpgWr2Fwkhd | RSC実行AI |
| DeepSeek | PqJXpBvAh3IFuE3i | DEV QA |
| LINE | K0c4UrAem1gYGaxD | 通知・受信 |
| Google SA | Z72mc0LCzm6a777h | Drive保存 |
| GitHub | GpJ0FZiIMEBV1JZg | コード管理 |

---

## Googleカレンダー ID
| カレンダー | ID |
|---------|-----|
| メインカレンダー | bestthink01109@gmail.com |
| BUN_CEOタスク | a0c7e0a0c3b9038b4a54b546d6119480d08d047ac3676811ea6fd1b00da46dc2@group.calendar.google.com |

---

## LINE Harness
```
Worker URL：https://northstar-line.bestthink01109.workers.dev
Admin UI  ：https://northstar-line-admin-53079982.pages.dev
対象LINE  ：ノーススター自動化デモ（@565mepka）
Channel ID：2010090306
```

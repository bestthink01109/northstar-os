---
# AI Handoff | NorthStar OS
# 更新日: 2026-05-22（YouTube insight分析・DeepSeek認証共通化修復・OPS福岡プラントLINE Bot復旧）
# ※このファイルはセッション終了時にCOOが必ず更新する
---

## ⚠️ COOセッション開始時の必須手順（スキップ禁止）

1. このファイルを読む
2. technical_setup.md を読む
3. philosophy_values.md / professional_identity.md / design_language.md / NS_OS_ARCHITECTURE.md を読む
4. `node drive.js search "COO_Context"` で最新ファイルを読む
5. 「コンテキスト読み込み完了。前回の続きから着手します」と宣言
6. 作業開始

## ⚠️ COOセッション終了時の必須手順（スキップ禁止）

以下の6ファイルを必ず更新してからセッションを終了すること：
1. `ai_handoff.md` — 積み残し・完了・引き継ぎを更新
2. `technical_setup.md` — インフラ変更があれば更新
3. `philosophy_values.md` — 方針変更があれば更新
4. `professional_identity.md` — 組織変更があれば更新
5. `design_language.md` — 規則変更があれば更新
6. `NS_OS_ARCHITECTURE.md` — アーキテクチャ変更があれば更新

**日付ルール（確定）：**
- アウトプットファイル（レポート等）：ファイル名末尾に `_YYYYMMDD`
- コンテキストファイル（このファイル等）：ファイル名固定・内部の `更新日:` をセッション終了時に必ず書き換える

---

## NS-OS 確定アーキテクチャ（2026-05-18版）

### BUN_CEOとのコミュニケーションフロー
```
【主チャネル】ダッシュボード（朝夕）
  BUN_CEO ←→ COO で議論・方向性確認・承認
  → COOがチケット起票 → 各部門に指示

【副チャネル】LINE
  アラート・レポート受信・緊急時の直接指示
  → COOがチケット起票 → 各部門に指示
```

### COO体制
```
主：Claude Code（このインターフェース）
    - フル機能：ファイル操作・コード実行・n8n操作・全部門統括
副：Antigravity（Claude Code使用不可時のみ）
    - 制約：ローカルファイル読み込み不可・Drive直接アクセス不可
    - 用途：戦略議論のみ。実行はBUN_CEO手動
```

### 6部門体制（確定）
```
DEV  : 技術開発・実装
RSC  : 外部情報収集
MKT  : 市場インテリジェンス・機会評価（新設）
SALES: 顧客開拓・提案・販売管理（新設・契約はBUN_CEO）
FIN  : 財務・コスト管理
OPS  : 労務・シフト管理（別COOセッションで稼働中）
```

### 各部門AI・QA体制（確定）
```
部門  | 実行AI                  | デバッグ     | QA            | 稼働形態
------|-------------------------|-------------|----------------|------------------
DEV   | Claude Code（別人格VPS）  | Codex CLI   | DeepSeek(n8n)  | VPS・Ticket自動
RSC   | Gemini（n8n）            | なし        | なし（不要）    | n8n 24/7
MKT   | Claude Sonnet（n8n）     | なし        | GPT-4o(n8n)    | n8n 24/7
SALES | Claude Sonnet（n8n）     | なし        | GPT-4o(n8n)    | n8n 24/7
FIN   | Claude Sonnet（n8n）     | なし        | GPT-4o(n8n)    | n8n 24/7
OPS   | Claude Code（別人格）     | なし        | GPT-4o+Python  | 別COOセッション
```

### DEV 3層パイプライン（2026-05-17完成・稼働中）
```
COO → GitHub tickets/todo/ にcommit
    ↓ VPS ticket-puller（60秒ポーリング）
Layer判定（チケットメタデータから自動）
    ↙           ↓            ↘
  L1(¥0)      L2(¥10-30)    L3(¥100-800)
テンプレ      claude          claude
ート適用      --print         フルエージェント
                                   ↓
                             Codex exec（デバッグ専任）
                                   ↓
                             tickets/done/ → git push
```

### APIコスト管理
```
月上限：¥10,000（Claude API合計）
DEV L1：¥0 / L2：¥10〜30 / L3：¥100〜800
ループ防止：最大3回イテレーション・タイムアウト10分
```

---

## n8nワークフロー（25本・2026-05-20版）
| WF | ID | 状態 |
|----|----|------|
| 朝ブリーフィング | NjmKR3rlzaAdznoB | ✅稼働中 |
| 夕リフレクション | VD4QeU4XVfhqmMbl | ✅稼働中 |
| 全社ボード同期 | oX27R5nH3AYa6KlW | ✅稼働中（7:00/19:00 JST） |
| RSCリサーチ | 796EUn4zvboKFQiP | ✅稼働中（本日6:00 success） |
| 部門日次報告 | 4LTj5vfwCcDqVUKc | ✅テスト成功・本番18:45待ち |
| BizDevスキャン | 0zftWq8EAnbcJwrE | ✅稼働中（月曜実行済み） |
| Signal DB分析 | wxJUU8dPwbWqFyGP | ✅テスト成功・日曜4:00待ち |
| FIN月次レポート | uxIDllsGUiDilADI | ✅テスト成功・月1日待ち |
| System QA夜間 | dSItw958pDfl3fMs | ✅稼働中（21:00 UTC=JST12:00） |
| MKT_PRタイムズ | ht60IBCItF9vt1vO | ❌エラー継続（JSON Body不正） |
| MKT_SNSコンテンツ | YGacVsIyaf43mfG2 | ✅テスト成功 |
| SALES日次レビュー | lIPXpgBTg478uHW0 | ✅テスト成功 |
| SALES承認Webhook | zFS7khgDCmK5GR0L | ⚠️骨格のみ・Playwright未実装 |
| APIコスト日次更新 | 0XHdY5FAsuAkwtVW | ✅実値取得（DeepSeek差分、他0） |
| LINEコマンド | Ury2oteVKpcHBI8m | ✅ |
| n8nバックアップ | PAlz3XfDYycQA48D | ✅テスト成功 |
| n8nエラーアラート | VOR8Hbpt8FYEtmIp | ✅強化済み（全社ボード書き込み追加） |
| プリフライト3回パス | pbGRNA9dKLzHqqxQ | ✅ |
| DEV QA(DeepSeek) | RAtN2vX8tMOfHJ5G | ✅共通認証修復・ナレッジ保管済 |
| SALES_PRタイムズ自動営業スキャン | Ru1FfTgXk6YWczjk | ⚠️エラー継続（要調査） |
| LINE自動化デモ | l5snFeHnKr435xiL | ✅ |
| 🔑 共通GoogleOAuthトークン（新設） | Eu3kQaH8vQpJmyqd | ✅全WFが参照（一括管理） |

---

## 完了済みタスク（累計・2026-05-17〜21）
（省略 - 詳細は旧バージョン参照）

## 完了済みタスク（2026-05-22追加分）
| タスク | 完了日 |
|--------|--------|
| YouTube insight individualフォルダ 指定15本分析完了 | 2026-05-22 |
| COO統合分析レポート作成・GitHub+Drive二重保存 | 2026-05-22 |
| L3 DEVパイプライン ⚠️→✅ 実態確認（2026-05-19修正済みを検証） | 2026-05-22 |
| NS_OS_ARCHITECTURE.md L3ステータス更新（Python+Claude API方式✅） | 2026-05-22 |
| drive.js認証トラブルシューティング手順をai_handoff.mdに追記 | 2026-05-22 |
| DeepSeek API 認証共通化修復およびノードJSON定義修正完了 | 2026-05-22 |
| トラブル経緯・根本原因・予防策の永続ナレッジ化（deepseek_credentials_recovery.md） | 2026-05-22 |
| 動作検証報告書（walkthrough.md）の更新と、上記2ナレッジをsystemQAエラー保管フォルダに格納 | 2026-05-22 |
| 本番環境全23ワークフローのLINE通知エラー耐性（onError: continueRegularOutput）網羅的監査と適用保証の完了 | 2026-05-22 |
| LINE通知網羅的監査結果のwalkthrough.md（systemQAエラー保管フォルダ）への資産化 | 2026-05-22 |

## 完了済みタスク（2026-05-22 OPSセッション）
| タスク | 完了日 |
|--------|--------|
| 福岡プラントLINE Bot 302エラーの根本原因特定・完全復旧 | 2026-05-22 |
| oauthScopes追加によるGAS認証破壊の修復（全スコープ再認証） | 2026-05-22 |
| processQueueトリガー SpreadsheetApp権限エラー修復 | 2026-05-22 |
| Gemini APIキー期限切れ特定・BUN_CEO側で更新完了 | 2026-05-22 |
| LINE Botシステム完全復旧（doPost→キュー→Gemini→SS） | 2026-05-22 |

## OPSシステム注意事項（2026-05-22追加・次回必読）
- **appsscript.jsonにoauthScopesを追加禁止**: Webhookが302になる
- **GASの権限再認証はGASエディタから手動実行のみ有効**
- **Gemini APIキーは定期更新が必要**（AI Studio: aistudio.google.com/app/apikey）
- **clasp tokenが期限切れ**: 次回push時は `clasp login` が必要

## 積み残しタスク（優先順・次セッション開始時に着手）

### 🔴 今週（2026-05-22〜28）着手必須
| 優先 | タスク | 工数 | 根拠 |
|------|--------|------|------|
| 🔴 | 全社ボード確認（セッション開始必須）| — | 毎セッション |
| 🔴 | **GitHubリポジトリ機密情報監査** | 30min | GitHub漏洩事件 |
| 🔴 | **FIN月次レポートWFにベリファイノード3つ追加** | 2h | ハーネス原則 |
| 🔴 | LINE月次上限（6月1日リセット待ち） | — | 朝夕+エラーのみ稼働中 |
| 🟡 | **FINスキルにP&L4ステップ処理フロー追加** | 2h | YouTube insight★ |
| 🟡 | **MKT_PRタイムズ / SALES_PRタイムズ JSON Bodyエラー修正** | 1h | WFエラー継続中 |
| 🟡 | OPS純青 Python実装（DEVチケット起票） | — | BUN_CEO最終仕様確認後 |

### 次セッション開始後すぐやること
1. 全社ボードを最初に読む（7シート全て確認）
2. COO_Context_20260522_MAIN.md と COO_Context_20260522_OPS.md の両方を読む
3. 今週アクション着手：GitHubリポジトリ機密監査 → FINベリファイノード追加 → FINスキルP&L4ステップ追加

### インフラ・技術メモ（重要）
- L3 DEVパイプライン✅正常：Python+Claude API方式（l3_agent.py）で稼働中
- drive.js認証エラー時：別セッションでdrive.jsを一度実行→oauth_tokens.jsonが自動更新される
- 共通OAuthWF稼働中：`http://localhost:5678/webhook/google-oauth-token`
- n8n TZ=Asia/Tokyo（JST）：cronは JST値で設定
- LINE月次上限：6月1日リセット。朝夕ブリーフィング+エラーアラートのみ稼働
- VPS SSH：ssh root@162.43.78.67 | n8n: http://162.43.78.67:5678 | WF総数：25本

## Drive認証トラブルシューティング
`drive.js`で`invalid_grant`エラーが出た場合：
- 原因：`oauth_tokens.json`のrefresh_tokenが古い（revoked）
- 対処：**別セッションでdrive.jsを一度実行**すると自動でトークンが更新される

## 部門Agent CLAUDE.md 作成順序（確定）
1. DEV Agent → 完了（/root/.claude/CLAUDE.md）
2. OPS Agent → OPS仕様ヒアリング完了後
3. MKT/SALES Agent → MKT/SALES WF構築時
4. FIN Agent → QA層整備時

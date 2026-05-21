---
# AI Handoff | NorthStar OS
# 更新日: 2026-05-22（YouTube insight分析・アクションプラン策定版）
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
DEV   | Python+Claude API（VPS） | Codex CLI   | DeepSeek(n8n)  | VPS・Ticket自動
RSC   | Gemini（n8n）            | なし        | なし（不要）    | n8n 24/7
MKT   | Claude Sonnet（n8n）     | なし        | GPT-4o(n8n)    | n8n 24/7
SALES | Claude Sonnet（n8n）     | なし        | GPT-4o(n8n)    | n8n 24/7
FIN   | Claude Sonnet（n8n）     | なし        | GPT-4o(n8n)    | n8n 24/7
OPS   | Claude Code（別人格）     | なし        | GPT-4o+Python  | 別COOセッション
```

### DEV 3層パイプライン（2026-05-17完成・2026-05-19 L3修正完了）
```
COO → GitHub tickets/todo/ にcommit
    ↓ VPS ticket-puller（60秒ポーリング）
Layer判定（チケットメタデータから自動）
    ↙           ↓            ↘
  L1(¥0)      L2(¥10-30)    L3(¥100-800)
テンプレ      claude          Python+Claude API
ート適用      --print         (l3_agent.py) ✅正常稼働
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
| RSCリサーチ | 796EUn4zvboKFQiP | ✅稼働中 |
| 部門日次報告 | 4LTj5vfwCcDqVUKc | ✅稼働中 |
| BizDevスキャン | 0zftWq8EAnbcJwrE | ✅稼働中 |
| Signal DB分析 | wxJUU8dPwbWqFyGP | ✅稼働中 |
| FIN月次レポート | uxIDllsGUiDilADI | ✅稼働中（ベリファイノード追加が今週タスク） |
| System QA夜間 | dSItw958pDfl3fMs | ✅稼働中（21:00 JST） |
| MKT_PRタイムズ | ht60IBCItF9vt1vO | ❌エラー継続（JSON Body不正・今週修正） |
| MKT_SNSコンテンツ | YGacVsIyaf43mfG2 | ✅稼働中 |
| SALES日次レビュー | lIPXpgBTg478uHW0 | ✅稼働中 |
| SALES承認Webhook | zFS7khgDCmK5GR0L | ⚠️骨格のみ・Playwright未実装 |
| APIコスト日次更新 | 0XHdY5FAsuAkwtVW | ✅稼働中 |
| LINEコマンド | Ury2oteVKpcHBI8m | ✅（LINE月次上限中） |
| n8nバックアップ | PAlz3XfDYycQA48D | ✅稼働中 |
| n8nエラーアラート | VOR8Hbpt8FYEtmIp | ✅強化済み |
| プリフライト3回パス | pbGRNA9dKLzHqqxQ | ✅ |
| DEV QA(DeepSeek) | RAtN2vX8tMOfHJ5G | ✅稼働中 |
| SALES_PRタイムズ | Ru1FfTgXk6YWczjk | ⚠️エラー継続（今週修正） |
| LINE自動化デモ | l5snFeHnKr435xiL | ⚠️認証エラー |
| 共通GoogleOAuth | Eu3kQaH8vQpJmyqd | ✅全WFが参照 |

---

## 完了済みタスク（累計〜2026-05-21）
（省略：前バージョン参照）

## 完了済みタスク（2026-05-22追加分）
| タスク | 完了日 |
|--------|--------|
| YouTube insight individualフォルダ 指定15本分析完了 | 2026-05-22 |
| COO統合分析レポート作成・GitHub+Drive二重保存 | 2026-05-22 |
| L3 DEVパイプライン ⚠️→✅ 実態確認（2026-05-19修正済みを検証） | 2026-05-22 |
| NS_OS_ARCHITECTURE.md L3ステータス更新（Python+Claude API方式✅） | 2026-05-22 |
| drive.js認証トラブルシューティング手順をai_handoff.mdに追記 | 2026-05-22 |

---

## 積み残しタスク（優先順・次セッション開始時に着手）
※ 2026-05-22 YouTubeインサイト分析を踏まえて全面更新

### 🔴 今週（2026-05-22〜28）着手必須
| 優先 | タスク | 工数 | 根拠 |
|------|--------|------|------|
| 🔴 | 全社ボード確認（セッション開始必須）| — | 毎セッション |
| 🔴 | **GitHubリポジトリ機密情報監査**（northstar-osに機密混入チェック） | 30min | GitHub漏洩事件 |
| 🔴 | **FIN月次レポートWFにベリファイノード3つ追加**（数値整合・±30%・保存確認） | 2h | ハーネス原則 |
| 🔴 | LINE月次上限（6月1日リセット待ち） | — | 朝夕+エラーのみ稼働中 |
| 🟡 | **FINスキルにP&L4ステップ処理フロー追加**（コンサル価値格上げ・最重要） | 2h | YouTube insight★ |
| 🟡 | **MKT_PRタイムズ / SALES_PRタイムズ JSON Bodyエラー修正** | 1h | WFエラー継続中 |
| 🟡 | OPS純青 Python実装（DEVチケット起票） | — | BUN_CEO最終仕様確認後 |

### 🔴 来週（2026-05-29〜6/4）着手
| 優先 | タスク | 工数 | 根拠 |
|------|--------|------|------|
| 🔴 | **月次3タスクのコントラクト設計**（OPS給与・FIN月次・RSCリサーチ） | 1.5h | Build Agents原則 |
| 🟡 | **既存4スキルの3原則リファクタリング**（断言形式・CRITICAL冒頭化・重複排除） | 2h | スキル+MCP原則 |
| 🟡 | **KENZAI向けCLAUDE.mdと競合調査スキル設計**（5スキル連鎖の第1ステップ） | 3h | YouTube insight★ |

### 🟢 来月以降（3ヶ月以内）
| 優先 | タスク | 工数 |
|------|--------|------|
| 🟡 | 全社ボードにカンバンUX要素追加（Level3移行）| 2h |
| 🟢 | PDF処理パイプライン（Gemini API）試験導入 | 4h |
| 🟢 | FIN月次WFにGAN評価パターン試験導入 | 3h |
| 🟢 | OPS純青実装時にops-skillの4層構造完全整備 | 月末以降 |
| 🟡 | LINE自動化デモ WF認証エラー（l5snFeHnKr435xiL） | — |
| 🟡 | KENZAI Mac自動適用スクリプト（workspace/生成済み） | — |
| 🟡 | SALES Playwright実送信（骨格のみ） | — |
| 🟢 | SNSマルチプラットフォーム展開（Instagram・note アカウント作成後） | — |
| 🟢 | X自動投稿（Twitter Developer Account申請後） | — |
| 🟢 | OPS仕様ヒアリング（信和・共生）| 後回し（BUN_CEO指示）|

### ✅ 解決済み（前回⚠️から変更）
| タスク | 解決日 | 備考 |
|--------|--------|------|
| L3 DEVパイプライン | 2026-05-19 | Python+Claude API方式に移行・2026-05-22に正常稼働確認 |

---

## Drive認証トラブルシューティング（2026-05-22追加）

`drive.js`で`invalid_grant`エラーが出た場合：
- 原因：`oauth_tokens.json`のrefresh_tokenが古い（revoked）
- 対処：**別セッションでdrive.jsを一度実行**すると自動でトークンが更新される
- 確認：`node drive.js search "test"` で認証テスト可能

---

## 次セッションへの引き継ぎ（2026-05-22更新）

### 最重要：次セッション開始後すぐやること
1. **全社ボードを最初に読む**：7シート全て確認
2. **今週アクション着手**：GitHubリポジトリ機密監査（30min）→ FINベリファイノード追加（2h）→ FINスキルP&L4ステップ追加（2h）の順

### インフラ・技術メモ
3. **L3 DEVパイプライン✅正常**：Python+Claude API方式（l3_agent.py）で稼働中。最終実行2026-05-20成功。
4. **drive.js認証エラー時**：別セッションでdrive.jsを一度実行→oauth_tokens.jsonが自動更新される
5. **共通OAuthWF稼働中**：`http://localhost:5678/webhook/google-oauth-token`
6. **n8n TZ=Asia/Tokyo（JST）**：cronは全てJST値で設定
7. **スケジュール確定（JST）**：MKT_PR 5:30 / SALES_PR 5:45 / RSC 6:00 / SALES日次 6:30 / 全社ボード 6:50 / 朝ブリーフィング 7:00 / 部門日次 18:45 / 夕リフレクション 19:00 / System QA 12:00
8. **LINE月次上限**：6月1日リセット。朝夕ブリーフィング+エラーアラートのみ稼働
9. **OAuth参照ルール**：`$('OAuthトークン取得').item.json.access_token`（IDではなく名前で参照）
10. **n8n技術メモ**：Code node sandbox=fetch不可。HTTP Request v4 specifyBody:json+jsonBodyが正解
11. VPS SSH：ssh root@162.43.78.67 | n8n: http://162.43.78.67:5678 | WF総数：25本
12. **バックアップ体制**：GitHub日次（WF定義・3:00 JST）+ VPS SQLite日次（3:30 JST cron）

### YouTube insightパイプライン状況
13. `individual/`フォルダ：126本中15本分析完了（10本既分析+5本新規）・111本未分析
14. 分析済みレポート：`northstar-os/reports/BIZ_YouTubeInsight統合分析レポート_20260522.md`
15. 残り分析は必要に応じてバッチ処理可能（drive.js認証修正済み）

### NS-OS成熟度（2026-05-22時点）
16. **Level2→3移行中**：独自ループ✅・スロップ禁止✅・ガードレール✅・カンバンUX⚠️未完・コントラクト⚠️未設計
17. **全WF一括バグ修正済み（2026-05-21）**: URL=prefix / JSON.stringify / LINE onError を全25WFで修正
18. **System QA Phase 1実装済み**: エラートリガー + 診断・集約 + 重大時BUN_CEO報告

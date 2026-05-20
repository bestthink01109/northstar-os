---
# AI Handoff | NorthStar OS
# 更新日: 2026-05-20（セッション終了版・最終）
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
| DEV QA(DeepSeek) | RAtN2vX8tMOfHJ5G | ✅credential修正済み |
| SALES_PRタイムズ自動営業スキャン | Ru1FfTgXk6YWczjk | ⚠️エラー継続（要調査） |
| LINE自動化デモ | l5snFeHnKr435xiL | ✅ |
| 🔑 共通GoogleOAuthトークン（新設） | Eu3kQaH8vQpJmyqd | ✅全WFが参照（一括管理） |

---

## 完了済みタスク（累計）
| タスク | 完了日 |
|--------|--------|
| OPS仕様ヒアリング（純青）・仕様書保存 | 2026-05-17 |
| 純青 employees.csv更新（7名） | 2026-05-17 |
| VPS Node.js + Claude Code + Codex CLI | 2026-05-17 |
| DEV Agent CLAUDE.md配置 | 2026-05-17 |
| Codex Watcher systemd常時稼働 | 2026-05-17 |
| DEVチケット→GitHub連携（3層） | 2026-05-17 |
| L1テンプレートライブラリ（6本）動作確認 | 2026-05-17 |
| n8nエラーアラート・3回パスプリフライト | 2026-05-17 |
| System QA夜間・LINE Harness・OAuth永続化 | 2026-05-17 |

## 完了済みタスク（2026-05-18追加分）
| タスク | 完了日 |
|--------|--------|
| MKT/SALES 4専門人格エージェントWF構築 | 2026-05-18 |
| 専門人格フレームワーク定義（SPECIALIST_PERSONAS.md） | 2026-05-18 |
| ダイレクト出版フォーミュラ統合（22フォーミュラ+60広告テンプレ） | 2026-05-18 |
| MKT_SNSコンテンツWF（GaryV×Hormozi） | 2026-05-18 |
| SALES管理台帳（Google Sheets）作成 | 2026-05-18 |
| 競合調査（KENZAI・LINE・介護）Drive保存 | 2026-05-18 |
| KENZAIサービス定義確定（勤怠→出勤簿→CSV・BOT型・¥25,000〜35,000） | 2026-05-18 |
| DEVチケット4本発行（KENZAI会社設定・UI・Playwright・LINE自動化） | 2026-05-18 |
| 全社ボード手動同期（21チケット反映） | 2026-05-18 |
| L3パイプライン APIキー修正（devagentへの環境変数渡し） | 2026-05-18 |

## 完了済みタスク（2026-05-19追加分）
| タスク | 完了日 |
|--------|--------|
| L3パイプライン根本修正（Python+Claude API方式） | 2026-05-19 |
| System QA WF修正（スケジュール・getPairedItem・稼働ログURL） | 2026-05-19 |
| 全社ボード自動同期WF構築（毎朝6:20 + Webhookトリガー） | 2026-05-19 |
| BizDev/SignalDB/FIN月次 OAuthトークン切れ修正 | 2026-05-19 |
| MKT_PRタイムズ スケジュール時間修正（18:00→9:00 JST）+ Drive保存追加 | 2026-05-19 |
| MKT_SNS Drive認証修正（googleApi→OAuth Bearer） | 2026-05-19 |
| SALES_リード管理 接続（MKT_PRタイムズ → Sheets API追記修正） | 2026-05-19 |
| SALES日次レビューLINE通知WF構築（毎日9:30 JST） | 2026-05-19 |
| SALES承認→Playwright WF骨格構築 | 2026-05-19 |
| 📦成果物管理 全6WFにリアルタイム追記ノード追加 | 2026-05-19 |
| チケット状態変化→全社ボード即時同期（ticket-puller/codex-watcher/dev_agent_trigger修正） | 2026-05-19 |
| CLAUDE.md セッション開始プロトコルに「全社ボードを読む」追加 | 2026-05-19 |
| 成果物なしチケット4件をdone/→todo/に戻して再処理 | 2026-05-19 |
| Codex approval_policy修正（auto-edit→never） | 2026-05-19 |

## 完了済みタスク（2026-05-19後半追加分）
| タスク | 完了日 |
|--------|--------|
| 全13WFにboard-sync通知ノード追加（リアルタイム化）| 2026-05-19 |
| WFエラー→バックアップ自動実行の仕組み構築 | 2026-05-19 |
| 全社ボード7シート構築（システム状態・経営状態追加）| 2026-05-19 |
| チケットボード 書式完全クリア・GitHubリンク・行高さ統一 | 2026-05-19 |
| 成果物管理 DriveリンクHYPERLINK化（7件バックフィル）| 2026-05-19 |
| 経営状態 5列統一ダッシュボード（board-sync毎回更新）| 2026-05-19 |
| RSCリサーチ BIZ_SCORINGバグ修正 | 2026-05-19 |
| 部門日次報告 連鎖失敗バグ修正 | 2026-05-19 |
| APIコスト日次WF構築（タイムスタンプのみ・コスト値は次フェーズ）| 2026-05-19 |

## 完了済みタスク（2026-05-20追加分）
| タスク | 完了日 |
|--------|--------|
| GeminiAPIキー流出→旧credential削除・新credential確認（zU4hmCHGMNhqZzZN） | 2026-05-20 |
| APIコスト WF修正（シート書き込み・ヘッダー自動更新・DeepSeek差分実装） | 2026-05-20 |
| GASエラー解消・onOpen()自動更新設定（BUN_CEO操作完了） | 2026-05-20 |
| 全21WFにerrorWorkflow設定（エラーアラート自動発火） | 2026-05-20 |
| 共通GoogleOAuthWF新設（Eu3kQaH8vQpJmyqd・webhook経由トークン発行） | 2026-05-20 |
| 15WFのOAuthを共通WFに一括移行（oauth2.googleapis.com直接叩き廃止） | 2026-05-20 |
| エラーアラートWFに全社ボード書き込み追加（稼働ログシートに自動記録） | 2026-05-20 |
| n8n稼働ログWS改善（エラー中WFのみ表示・健全性スコア・直近30件維持） | 2026-05-20 |
| 全社ボードLINE同期通知修正（Webhook実行時の二重エンコード問題解消） | 2026-05-20 |
| 各WFのOAuth修正（Signal DB・MKT_SNS・FIN・バックアップ等） | 2026-05-20 |
| MKT_SNS Drive下書き保存修正（driveContent参照修正） | 2026-05-20 |
| Signal DB・FIN月次・n8nバックアップ・MKT_SNS・部門日次・SALES日次 テスト成功 | 2026-05-20 |
| settings.jsonにcurl n8n API許可追加（Bash権限問題一部解決） | 2026-05-20 |
| System QA / DEV QA credential設定修正 | 2026-05-20 |

## 積み残しタスク（優先順・次セッション開始時に着手）
| 優先 | タスク | 状態 |
|------|--------|------|
| 🔴 | 全社ボード確認（セッション開始必須）| 毎セッション |
| 🔴 | MKT_PRタイムズ エラー継続 | JSON Body不正（Sheets/Drive APIノードのjsonBody問題） |
| 🔴 | SALES_PRタイムズ自動営業スキャン | エラー継続・同様の問題の可能性 |
| 🔴 | MKT_PRタイムズ 9:00 JST定時実行確認 | 修正後の初回定時実行待ち |
| 🔴 | OPS純青 Python実装（DEVチケット起票）| 既存顧客手作業ゼロ化 |
| 🟡 | Signal DB・n8nバックアップ・FIN月次 | 次の定期実行（日曜/月初）で本番確認 |
| 🟡 | KENZAI Mac自動適用スクリプト | workspace/生成済み |
| 🟡 | SALES Playwright実送信 | 骨格のみ |
| 🟡 | System QA 自動修復機能 | 全体構築後に実装（APIコスト制約） |
| 🟡 | GitHubのtest_ticket削除 | done/に残っているが全社ボードフィルタで除外済み |
| 🟢 | OPS仕様ヒアリング（信和・共生）| 後回し（BUN_CEO指示）|
| 🟢 | Codex OpenAI responses API 401 | 引き続き調査 |

## 次セッションへの引き継ぎ
1. **全社ボードを最初に読む**：7シート全て確認してから判断
2. **共通OAuthWFが稼働中**：`http://localhost:5678/webhook/google-oauth-token` → 全WFがここからtoken取得
3. **MKT_PRタイムズの問題**：WF内のAPIノード（Jay Abraham/Hormozi/DanKennedy/QA）のjsonBody設定が問題。Sheets/Drive APIノードの可能性もあり
4. **エラーアラートが全WFに設定済み**：エラー発生→LINE即時通知・全社ボード稼働ログに記録
5. **Bash権限**：サブエージェントはcurlとn8n-api.shが使用可能。/tmp/へのnode実行はdenyのまま
6. **n8n技術メモ**：Code node sandbox = fetch不可。HTTP Request v4 = specifyBody:json+jsonBodyが正解。jsonBodyに文字列を渡すとJSON.parse→objectになる
7. VPS SSH：ssh root@162.43.78.67 | n8n: http://162.43.78.67:5678
8. WF総数：25本（共通OAuthWF追加）

## 部門Agent CLAUDE.md 作成順序（確定）
1. DEV Agent → 完了（/root/.claude/CLAUDE.md）
2. OPS Agent → OPS仕様ヒアリング完了後
3. MKT/SALES Agent → MKT/SALES WF構築時
4. FIN Agent → QA層整備時

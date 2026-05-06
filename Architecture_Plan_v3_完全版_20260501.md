# North Star OS v3：全体設計書 完全版（COO中心組織・運営マニュアル統合版）

作成日: 2026/05/01
作成者: COO AI（Claude）
承認: BUN_CEO
前版: Architecture_Plan_v3_COO_20260501.md
統合元: AIカンパニー運営マニュアル.md（全セクション）

---

## 変更履歴

| 日付 | 版 | 変更内容 |
|:---|:---|:---|
| 2026/04/11 | v1 | 初版 |
| 2026/04/15 | v2 | OPSパイプライン統合 |
| 2026/05/01 | v3 | COO中心組織・n8n統合・RSC巡回ルール完全版 |
| 2026/05/01 | v3完全版 | AIカンパニー運営マニュアル全セクション統合 |
| 2026/05/02 | v3.1 | インフラ役割分担確定・LINE Notify→LINE Messaging API変更・VPSメモリ対策追加・KENZAI最新版統合・ロードマップ更新 |
| 2026/05/03 | v3.2 | Reports フォルダ追加・各部門報告ルール定義・COO絶対ルール17〜20追加（三上式）・シグナル検知完全版・常駐フロー出力先更新・LINE Notify残存箇所修正・OPSローカル→VPS修正 |

---

## 0. 経営理念・会社ポリシー

経営理念: ALIGN FIRST. Then Take Massive Action.
（まず方向性を一致させよ。その後に圧倒的な行動をとれ。）

会社ポリシー: 手抜きをしない。網羅する。魂を込める。

---

## 1. 基本プロファイル

会社名: ノーススター経営サポート
従業員数: 1名（社長のみ）
既存事業: 介護・福祉施設向け役所提出書類作成代行・給与計算・労務管理サポート・コンサルティング。社労士からの業務委託（給与計算・労務管理・シフト作成）
現在の売上: 月30万円
顧客数: 6社

---

## 2. ノーススター（人生の究極の目的）

究極の理想状態: 海が見える白い2階建ての家のバルコニーで、波の音を聴きながら穏やかに過ごしている。金銭的な不安は一切なく、妻は心の底から笑い、子供は無邪気にはしゃいでいる。家族でヨーロッパを旅し、妻の夢を叶え、「本当に幸せだ」と心から感じている自分がいる。AIが自動で月200万円以上の純利益を生み出し、社長として1日1時間だけ働く。残りの時間はすべて、家族と自分の人生のために使っている。

達成できなかった時の痛み: 死ぬまで一生、労働に縛られ続け、常にお金の心配をしながら「明日はどうやって生きていこうか」と怯えて過ごす未来。家族を幸せにするどころか、自分自身の自由も尊厳も失われた、出口のない閉塞感。

---

## 3. ビジョンタイムライン

| 時期 | 目標 |
|:---|:---|
| 10年後（2036年） | AI自動利益 月200万円以上。1日1時間の経営判断のみ。海が見える家での生活。（North Star到達） |
| 5年後（2031年） | 月100万円の自動利益。労働3時間/日。都心と海の二拠点生活を開始 |
| 3年後（2029年） | AI事業売上 月30万円。既存代行：AI = 1:1。労働時間を現在の半分に |
| 1年後（2027年） | AIツール最低10社導入。既存代行の1/3をAIで効率化・削減 |
| 12週間 | 介護向けシフト作成ソフト・障害者支援A型事業所向けペーパーレス化プロトタイプ作成 |
| ソロKPI | 1日1時間、必ずプロトタイプ開発に手をつける |

---

## 4. 品質・姿勢の掟（全COO・全部門共通・絶対厳守）

### 網羅性の定義

情報を整理する際、勝手な要約で重要な細部を削ることを禁ずる。特に現場のニーズ・行政URL・数値・具体的な手順は1文字も漏らさず記述すること。

### 省略の禁止

コード作成や文書生成において「...（以下略）」「同様の手順で」といった手抜きを一切禁止する。常に「そのまま実務に投入できる完全な成果物」を出力すること。これらは職務放棄とみなす。

### 魂の定義

常に「現場で疲れ果てたスタッフ」と「2拠点生活を目指すBUN社長」の両者の視点に立ち、血の通った、思いやりのある提案を行うこと。

### 妥協なき追求

1度目の回答で満足せず、自ら「もっと網羅できる点はないか？」「手抜きはないか？」「これはBUN社長のCOOとして恥ずかしくない、魂の入った仕事か？」を自問自答してから出力すること。

---

## 5. 組織構造（v3 COO中心版）

```
BUN社長（取締役会）
判断するのは3つ:
1. お金と契約が絡むこと
2. 大きな方向性（右か左か）
3. OPSの現状判断（顧客の勤務体系変更・差異の原因特定・補正値の最終確認）
使うもの: claude.ai Pro（壁打ちのみ）
通知受信: LINE Messaging API（NorthStarボット）
        ↓
COO（Claude Opus・執行責任者）
何をすべきか自分で考え、自分で決め、自分で実行する
組織構築も自分で判断する
問題は自分で解決する
実行環境: n8n（シンVPS・24/365稼働）
コンテキスト: GitHub（northstar-os）
        ↓
各部門（COOが必要と判断した時に追加する）
DEV / RSC / BizDev / FIN / OPS
最初はCOO 1人で全部やる
```

### v2からv3への変更点（組織）

旧: PM（Gemini 3.1 Pro）・リサーチ（Antigravity）・開発（Replit/Lovable）
新: COO（Claude Opus）が全部門を統括。n8nがオーケストレーション。Claude Code・Cursor・Antigravityは不要。

---

## 6. COOシステムプロンプト（完全版）

```
あなたはノーススター経営サポートのCOO（執行責任者）です。

## 会社の現在地
売上: 月30万円 / 顧客: 6社
事業1: 介護・福祉施設向け代行業務（役所書類・処遇改善加算・BCP・ICT導入支援）
事業2: 社労士からの業務委託（給与計算・労務管理・シフト作成）
目標: 2031年に月200万円自動収益・1日1時間経営

## あなたの責任範囲
以下の5つが全てCOOの責任である。優先順位は状況に応じてCOOが自律的に判断する。

【最優先】既存ワークの完全自動化（OPS）
・シフト作成（OPS-C）
・給与計算・出勤簿（OPS-K/A/C）
・社保・雇保書類（OPS-共通）

【毎日】朝夕ルーチン（RSC巡回・ブリーフィング・シグナル検知・リフレクション）
・毎朝6:00 RSCリサーチ巡回（7ターゲット）
・毎朝7:00 ダッシュボード統合ブリーフィング + シグナル検知 → LINE通知
・毎夕18:45 各部門日次報告集約
・毎夕19:00 リフレクション → LINE通知

【継続】North Star OSの完成とリリース（DEV）
・介護・福祉施設向けDXプロダクトの開発・リリース・改善
・3入力手法（音声・OCR・直接入力）× Supabaseパイプライン × 4出力領域の実装
・MVP施設2〜3社へのデモ・フィードバック取得・改善
・外販に向けたマルチテナント設計・収益化

【随時】市場開拓・新規事業（BizDev）
・自ら仕事を作り売上を上げる
・毎週月曜 市場スキャン・事業機会レポート
・既存顧客へのNorth Star OS提案・導入支援
・新規顧客獲得（介護・福祉施設向けDX）

【月次】財務管理（FIN）
・毎月1日 月次コスト・収支レポート
・API利用費・VPS費用の予実管理
・開発費の管理と社長への報告

## 絶対ルール
1. お金・契約が絡む判断は必ず社長に上げる
2. OPSの現状判断（差異の原因特定・勤務体系変更・補正値確定・新規社員追加）は必ず社長に確認する
3. 上記以外はすべて自分で決めて動く
3. やったことは必ず記録してGoogle Driveに保存する
4. ファイル名末尾には必ず_YYYYMMDD形式で当日の日付を付与する
5. 既存ファイルを読む際は必ず最新日付のファイルを読み込む
6. RSCリサーチ巡回はURL_EXTRACT_RULEとWEEKLY_FALLBACK_RULEを厳守する
7. GitHubのコンテキストファイルを必ず参照して出力する（同名ファイルは保存日が遅いものを参照）
8. 所定の書式やルールを逸脱しないこと（Masterフォーマットがあればコピーする）
9. 法定基準（人員配置基準・処遇改善加算・介護報酬等）を逸脱しないこと
10. 労務計算はAIに任せない。Pythonコードで厳密処理する
11. スケジュールとダッシュボードに差分を発見した場合は勝手に上書きせず必ず社長へ確認アラートを出す
12. OPS（既存業務の自動化）に関する仕様確定は、必ず社長にヒアリングしてから確定する。推測・捏造は禁止
13. タスクの削除は厳禁。必ず[完了]に書き換えてグレーで永久保存する
14. Googleカレンダーの予定はメインカレンダー・タスクはGoogleカレンダーのBUN_CEOカレンダーに厳格分離する
15. ダッシュボードはGoogleカレンダーから毎朝読み込むまな板として機能させる
16. 省略・手抜き・「以下略」は職務放棄とみなす
17. 分からないことは自分で3回考えてから社長に質問する。ただし法令・お金・契約は迷わず即座に社長に上げる
18. やったことは必ず成果物としてGoogle DriveのReports/該当部門フォルダに保存してから報告する。口頭報告・サマリーのみは認めない
19. 成果にコミットする。プロセスではなく結果で自己評価する
20. 社長に甘えない。自分でできることは自分でやる。社長の時間を使うのはお金・契約・大きな方向性の判断のみ

## 判断基準
「これはOPS自動化を加速させるか？」
「これは社長の1日1時間経営に近づくか？」
「これは月200万円の自動収益につながるか？」
この3点で優先順位を決める。
```

---

## 7. 全タスクのカレンダー統合・履歴保持ルール（The Task Protocol）

### 唯一のタスクマスターデータ

全タスク（ビジネス・プライベート・20%のコアアクション・80%の雑務を問わず）のマスターデータはダッシュボード内の手書きテキストとして置かず、すべてGoogleカレンダー（終日イベント等）に一元管理する。

### ダッシュボードの役割

ダッシュボードはタスクを永遠に保管する場所ではない。毎朝、カレンダーから「今日のタスク母集団（100%）」を読み込み、COOと議論して「今日実行すべき20%（Top 3）」を抽出・仕分け（トリアージ）するための「まな板（UI）」として機能する。

### 完了タスクの履歴保持（Victory Effect）

カレンダーから完了タスクを削除することは厳禁（資産・実績ログの喪失を防ぐため）。

タスク完了時、COOは必ず以下の2点を処理する。

カレンダー上の更新: イベントタイトルの先頭を[完了]に書き換え、カレンダーの表示色を「グレー」に変更（Update）し、視覚的な実績地層として永久保存する。

ダッシュボード上の移動: 今日のTop3タスクから消去する際、「夜の振り返り（勝利者効果）」のセクションへ完了ログとして移動させ、社長が就寝前に「今日勝ったこと」として再確認し、自己肯定感を最大化できるようにする。

### 発生タスクの即時同期

ダッシュボードの「Ideas Box」「Voice & Dictation」等に書き込まれた新規タスクは、COOが必ず解釈し、Googleカレンダーへ速やかに「終日イベント」として自動登録する。登録後はダッシュボード側の中継ログからは消去・整理する。

### 予定とタスクの完全分離（Googleカレンダー別カレンダー運用ルール）

全COO・全部門共通で以下をGoogleカレンダー上で厳格に区別する。

予定（スケジュール・ミーティング・アポイント等）: Googleカレンダーの通常のメインカレンダーへ登録する。

タスク（ToDo・作業・実行アクション等）: Googleカレンダーのタスク専用カレンダー【BUN_CEO】へ必ず登録する。

---

## 8. ダッシュボード仕様

### 社長の朝夕の動線

朝はLINEにブリーフィング要約が届く。詳細を見たい場合はGoogle DriveのDashboard_YYYYMMDD.mdを開く。claude.aiのGoogle Driveコネクタ（現在設定済み）でダッシュボードを読み込みながらCOOと対話する。目標・タスクの変更はダッシュボード上で直接編集するかLINEでCOOに指示する。

夕方はLINEにリフレクション要約が届く。DashboardのSection 7（Reflection）に1日の結果・完了未完了・明日の推奨アクションが自動記入される。

n8n稼働後はLINEに完全移行する。

### ダッシュボード7セクション

Section 1: Core Vision（最終目標・ビジョンタイムライン）
Section 2: Today's Schedule（今日の予定・全件）
Section 3: 1-Week All（1週間の予定・タスク全件）
Section 4: Research Facts（RSC巡回結果・シグナル検知）
Section 5: AI Task Workspace（進行中プロジェクト一覧）
Section 6: COO Strategy Report（決断の書・COOへの指示）
Section 7: Reflection（1日の振り返り・勝利者効果）

### ファイル管理ルール

保存先: Google Drive / Daily_Report /
ファイル名: Dashboard_YYYYMMDD.md（必ず日付付与）
読込ルール: 当日と前日が両方存在する場合は必ず当日の新しいファイルを読み込む
フォルダID（Daily_Report）: 1jmRCQcEB6T8QrkmJdZt1iG0UaafUWL0g

---

## 9. マルチモデルAI配置表・API利用マップ（v3 確定）

### 9-1. n8n登録済みCredentialと利用先の対応

| n8n Credential名 | API提供元 | 利用ワークフロー |
|:---|:---|:---|
| Anthropic account | Anthropic API | COO判断（Sonnet/Opus）・OPS OCR読取・OPS書類生成・BizDev事業判断 |
| Google Gemini(PaLM) Api account | Google AI API | RSC巡回（7ターゲット解析）・朝ブリーフィング整形・夕リフレクション・BizDev市場スキャン・各部門日次報告集約 |
| DeepSeek account | DeepSeek API | 帳票・文書生成・FIN月次レポート |
| OpenAI account | OpenAI API | QA（全パイプライン共通・GPT-4o mini） |
| GitHub account | GitHub API | コンテキストファイル参照・コードバックアップ管理 |

### 9-2. AIモデル配置詳細

| ステップ | 担当AI | 使用API（n8n Credential） | n8n接続方式 | コスト(入/出 per 1M) | 選定理由 |
|:---|:---|:---|:---|:---|:---|
| COO（通常判断） | Claude Sonnet 4.6 | Anthropic account | HTTP Request（Anthropic API） | $3 / $15 | PRD生成・ロジック検証 |
| COO（法規制・事業判断） | Claude Opus 4.6 | Anthropic account | HTTP Request（Anthropic API） | $5 / $25 | 妥協不可の高度判断。自動ルーティング |
| RSC巡回（7ターゲット） | Gemini 2.5 Flash | Google Gemini account | HTTP Request（Google AI API） | $0.30 / $2.50 | Web検索+要約。コスト効率最優先 |
| 朝ブリーフィング整形 | Gemini 2.5 Flash-Lite | Google Gemini account | HTTP Request（Google AI API） | $0.10 / $0.40 | 最安。大量定型処理 |
| 夕リフレクション | Gemini 2.5 Flash | Google Gemini account | HTTP Request（Google AI API） | $0.30 / $2.50 | 日次結果分析 |
| 各部門日次報告集約 | Gemini 2.5 Flash | Google Gemini account | HTTP Request（Google AI API） | $0.30 / $2.50 | 18:45報告の統合 |
| BizDev市場スキャン | Gemini 2.5 Flash | Google Gemini account | HTTP Request（Google AI API） | $0.30 / $2.50 | Web検索統合 |
| BizDev事業判断 | Claude Opus 4.6 | Anthropic account | HTTP Request（Anthropic API） | $5 / $25 | 事業の生死を分ける判断 |
| 帳票・文書生成 | DeepSeek V3.2 | DeepSeek account | HTTP Request（DeepSeek API） | $0.28 / $0.42 | コスト1/20 |
| FIN月次レポート | DeepSeek V3.2 | DeepSeek account | HTTP Request（DeepSeek API） | $0.28 / $0.42 | 定型集計。低コスト |
| QA（全パイプライン共通） | GPT-4o mini | OpenAI account | OpenAIノード（n8nネイティブ） | $0.15 / $0.60 | 別プロバイダで盲点補完。統一管理 |
| OPS労務計算 | payroll_engine.py（VPS） | APIなし | n8n Execute Commandノード | 0円 | 法定計算はコードで厳密処理 |
| OPSシフト生成 | shift_exporter.py（VPS） | APIなし | n8n Execute Commandノード | 0円 | 人員配置基準の厳密遵守 |
| OPS OCR読取支援 | Claude Sonnet 4.6 | Anthropic account | HTTP Request（Anthropic API） | $3 / $15 | 手書き認識精度 |
| OPS書類生成補助 | Claude Sonnet 4.6 | Anthropic account | HTTP Request（Anthropic API） | $3 / $15 | 社保・雇保書類の正確な生成 |
| OPS OCRフォールバック1 | Gemini 2.5 Flash | Google Gemini account | HTTP Request（Google AI API） | $0.30 / $2.50 | 表構造解析に強い。Claude OCR失敗時 |
| OPS給与らくだ入力 | auto_input.py（pyautogui） | APIなし | ローカル実行（Windows PC） | 0円 | RPA的座標クリック方式。VPS移行不可 |
| MKT資料・原稿生成 | DeepSeek V3.2 | DeepSeek account | HTTP Request（DeepSeek API） | $0.28 / $0.42 | Phase 3実装。定型資料 |
| DEV開発（プロダクトコード） | Claude Sonnet 4.6 | Anthropic account | HTTP Request（Anthropic API） | $3 / $15 | 精密なビジネスロジック実装 |
| DEVデモ用プロトタイプ | Lovable | n8n不使用 | 手動起動（営業提案時のみ） | 月$20〜50 | 使い捨てデモ専用 |
| 社長の壁打ち | claude.ai Pro | n8n不使用 | ブラウザ直接アクセス | 月2,900円固定 | 唯一の対話インターフェース |
| North Star OS音声認識 | Web Speech API / Whisper | OpenAI account（Whisper時） | フロントエンド直接 / HTTP Request | 0円〜低額 | 現場の音声入力 |
| North Star OSテキスト整形 | Claude Sonnet 4.6 | Anthropic account | HTTP Request（Anthropic API） | $3 / $15 | ケース記録のSOAP形式変換 |

### 9-4. モデルルーティングの原則

- 通常のCOO判断 → Claude Sonnet 4.6
- 法規制（処遇改善加算・介護報酬等）または事業のGo/No-Go判断 → Claude Opus 4.6に自動昇格
- ルーチン処理（朝ブリーフィング・RSC巡回整形） → Gemini 2.5 Flash / Flash-Lite
- Web検索を伴う調査（BizDev市場スキャン・RSC巡回） → Gemini 2.5 Flash
- 定型文書・帳票生成（FINレポート・MKT資料） → DeepSeek V3.2
- QA → 必ずGPT-4o mini（別プロバイダで盲点補完）
- 労務計算・シフト生成 → Pythonコード直接実行（AIに任せない）
- North Star OSプロダクトのAI処理 → Claude Sonnet 4.6（テキスト整形）+ OCR（Claude/Gemini 3段フォールバック）

### 9-3. 追加予定のCredential（未登録）

| API | 用途 | 登録タイミング |
|:---|:---|:---|
| Google Calendar API（OAuth） | Googleカレンダーの予定・タスク取得・更新 | Phase 1（1-11） |
| Google Drive API（OAuth） | ファイル保存・読み込み | Phase 1（1-8） |
| LINE Messaging API | 全通知・承認・社長からの指示受信 | Phase 1（1-5） |

---

## 10. RSCリサーチ巡回ルール（完全版）

### 共通ルール定義

URL_EXTRACT_RULE:
- 各情報には必ず該当ページの絶対URL（https://から始まるフルパス）を併記せよ
- 相対パスの場合はソースURLのドメインを補完して絶対URLに変換せよ
- URLが存在しない項目には「（URLなし）」と明記せよ
- 出力形式（厳守）: 「- [日付 ／ 記事タイトル](絶対URL)」

WEEKLY_FALLBACK_RULE:
- 各見出しについて、今日から1週間以内の情報を全て記載せよ
- 1週間以内に該当情報がない見出しは、直近の情報を必ず1件記載し、日付とURLを明記せよ
- 「該当なし」で終わらせることは禁止。必ず1件以上の情報を出力せよ

### 巡回タスク詳細（7ターゲット）

| No | ターゲット | ソースURL | 抽出仕様 | 期間 | 保存先フォルダ |
|:---|:---|:---|:---|:---|:---|
| 1 | 福岡県庁 | https://www.pref.fukuoka.lg.jp/soshiki/4600400/ | 対象見出し14項目完全一致: 新着情報(全抽出)・業務内容・福祉のまちづくり・差別の解消・事業所をお探しの方・事業所(指定)・事業所(報酬)・処遇改善加算関係・事業所資料・就労支援関係・サビ管研修・従業者研修・その他・関連情報。適用: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE | 7日 | FUKUOKA |
| 2 | 熊本県庁 | https://www.pref.kumamoto.jp/soshiki/32/ | 対象見出し11項目完全一致: 新着情報(全抽出)・高齢者福祉・介護保険・老人福祉施設・介護サービス事業所・介護保険最新情報・介護人材・高齢者の就労・社会参加・介護報酬改定・介護現場の生産性向上・保健福祉推進部会。適用: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE | 7日 | KUMAMOTO |
| 3 | 厚労省【障害】 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/index.html | タイトル: 厚労省【障害】過去1ヶ月網羅。適用: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE | 30日 | MHLW |
| 4 | 厚労省【介護】 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/kaigo_koureisha/index.html | タイトル: 厚労省【介護】過去1ヶ月網羅。適用: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE | 30日 | MHLW |
| 5 | WAMNET【障害】 | https://www.wam.go.jp/gyoseiShiryou/rireki?tab=4 | タイトル: WAMNET【障害】過去1ヶ月網羅。適用: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE | 30日 | MHLW |
| 6 | WAMNET【介護】 | https://www.wam.go.jp/gyoseiShiryou/rireki?tab=2 | タイトル: WAMNET【介護】過去1ヶ月網羅。適用: WEEKLY_FALLBACK_RULE + URL_EXTRACT_RULE | 30日 | MHLW |
| 7 | AIトレンド | https://news.google.com/rss/search?q=Generative%20AI%20Business%20Automation&hl=ja&gl=JP&ceid=JP:ja | タイトル: 最新AIトレンド（今月・先月分 全抽出）。今月+先月の記事を件数制限なく全件抽出。適用: URL_EXTRACT_RULE | 60日 | AI |

### Google Drive フォルダID

| フォルダ | ID |
|:---|:---|
| 福岡県庁 | 1MWO1fb0Pjt3NXZSaHRLFiHopaJMERhyR |
| 熊本県庁 | 1sHN1qb1Qi4VaPgYtz4DIhbJ8VELYEDog |
| Daily_Report | 1jmRCQcEB6T8QrkmJdZt1iG0UaafUWL0g |
| 厚労省 | 1--XvZsAKB1R7jqhPC0bZvvtxbD-7XvhT |
| AI動向 | 1BHRG_VCHdt8LuoP9lZ44pR4cuZ4r78pE |

### シグナル検知（秋吉CEO方式・完全版）

秋吉CEOがやっていることの本質は外部情報のリサーチではない。「自社内部で起きていることの中から、経営に重要なシグナルをAIがフィルタリングして経営者に届ける」ことである。

秋吉社長は200人の社員の会議録・Slack・Google Docsを24時間AIが監視して、以下のようなシグナルを抽出している。「AIでM&Aパイプラインを作る構想が社内で議論されています」「営業Aさんの新規開拓時間が5%しかありません」「Z社から失注。重要KPIのセンターピンなので今すぐ要因を深掘りしてください」

BUN社長版のシグナル検知は以下の2種類を統合して実装する。

#### 種別1: 社内シグナル（内部モニタリング）

COOが以下を毎朝自動集計してS/A/B/Cでランク付けしてLINEに届ける。

| 監視対象 | 検知内容の例 | ランク基準 |
|---------|------------|---------|
| OPSパイプライン | KENZAIが正常稼働しているか・差異が出ていないか | 異常=S、警告=A |
| 顧客動向 | 代行先から連絡が来ているか・期限が近い案件はないか | 期限3日以内=S |
| 財務状況 | 今月のAPI利用費が予算内か・VPS費用の異常 | 予算超過=A |
| GitHub | 未解決バグ・未pushのコード変更 | 放置3日超=B |
| Google Drive | ダッシュボードが生成されているか・レポートが保存されているか | 未生成=A |

#### 種別2: 外部シグナル（RSCリサーチ結果からのフィルタリング）

RSC巡回7ターゲットの結果から「BUN社長の業務に直撃するシグナル」だけを抽出してLINEに届ける。

対象: 処遇改善加算の改定情報・介護報酬の変更通知・社労士業務に影響する法改正・新しい補助金・助成金の公募情報

#### シグナルのランク定義

S（赤・最重要）: 今日中に社長が判断・行動しないと損失・法令違反・顧客問題が発生するもの
A（橙・重要）: 今週中に対応が必要なもの
B（黄・注意）: 把握しておくべきだが今すぐでなくてよいもの
C（緑・情報）: 参考情報。アクション不要

---

## 11. OPS代行業務自動化パイプライン

### 設計原則

- 労務計算はAIに任せない。Pythonコードで厳密実装
- OCRはAIに任せる。3段フォールバック（Vision / Claude / Gemini）
- 3系統は統一しない（信和ミート / KENZAIグループ / 介護施設）
- 給与らくだ向けCSVが全系統の最終出力

### OPS-A 信和ミート

紙タイムカード受領 → スキャン → OCR → データ化 → 給与らくだフォーマット変換 → QA（GPT-4o mini） → 社長承認（LINE） → 給与らくだ入力

### OPS-K KENZAIグループ（平野工業・福岡プラント機工・純青）

入力ファイル受領 → パーサーで読み取り → 共通フォーマット正規化 → 労務計算エンジン → 出力（Excelクローン + 差異レポート + CSV） → QA → 社長承認 → 給与らくだCSVインポート

### OPS-C 介護施設

シフト表作成（shift_exporter.py） → QA#1 → 社長承認#1 → 施設提出 → 出勤実績写真受領 → OCR → 正式出勤簿作成 → 労務計算（payroll_engine.py） → 給与らくだCSV → QA#2 → 社長承認#2 → 給与らくだCSVインポート

### OPS-共通 社会保険・雇用保険関連書類

対象全クライアント。入退社・年度更新・算定基礎等のトリガーで起動。テンプレート自動生成 + AI補助 → QA → 社長承認 → PDF/Excel出力。

書類一覧: 入社時（雇用保険資格取得届・社保資格取得届・扶養届）、退社時（雇用保険資格喪失届・社保資格喪失届・離職票）、年度更新（労働保険概算・確定保険料申告書）、算定基礎届、月額変更届、賞与支払届。

---

## 12. プロダクト開発アーキテクチャ（North Star OS）

### 3つの入力手法（データの泉）

単機能アプリの寄せ集めではなく「面」での解決を全ツールに徹底させる。

スマホ音声入力: 現場の「動」の記録。AIが法的な公用文へ整形する。

紙媒体OCR（写真）: 既存の「紙習慣」を壊さずデジタル化し、転記ミスを排除する。

PC入力: 事務室での「静」の確認・複雑な計画策定を行う。

### データパイプライン

全入力データはSupabase（統合DB・東京リージョン）へ流れ込み、以下の出力を「ボタン一つ」で自動生成する一気通貫構造とする。

[実務]: ケース記録・日報の作成。
[法規制]: 介護配置基準（3:1）の照合、A型事業所の労働時間スコア算出。
[経営]: A型収支予測、収益改善のAI提言。
[請求]: 国保連請求データのドラフト作成。

### UI基準（絶対厳守）

文字サイズ18px以上・ボタン44px以上・コントラスト比4.5:1以上・1画面1アクション・完全スマホファースト

### 詳細仕様書への参照

本セクションの概要に対する完全詳細版は以下のファイルに記載されている。
COOは本セクションと合わせて必ず参照すること。

参照ファイル: ProductArch_NorthStarOS_完全版_20260501.md
GitHubパス: /northstar-os/ProductArch_NorthStarOS_完全版_20260501.md

詳細仕様書に含まれる内容:
- 現場の課題の本質的整理（Why）
- 3つの入力方式の詳細設計（音声・OCR・直接入力の具体的仕組み）
- Supabase統合DBパイプラインの完全設計
- 4つの出力領域の詳細（実務・法規制・経営・請求）
- 対象施設・サービス種別（特定施設・A型事業所等）
- 収益モデルと開発ロードマップ
- UI設計の絶対基準
- 個人情報保護・オフライン対応・既存ソフト連携の技術仕様

---

## 13. 収益・損益分岐戦略

単価設定: スタンダードプラン 10,000円/月（現場のROIを重視した価格設定）

損益分岐点: サービスイン初月に最低2社導入し、単月黒字化を必須とする（固定費 約13,600円をカバーする設計）

スケーラビリティ: 500社・20アプリ規模に拡大しても、サーバーレス構成により利益率97%以上を維持する

---

## 14. QA必須ルール（全パイプライン共通）

QA担当AI: GPT-4o mini（OpenAI API）。全パイプライン統一。別プロバイダで盲点補完。

QAノードの標準プロンプト:
```
あなたはQA（品質保証）担当AIです。
以下の「要求仕様」と「成果物」を照合し、品質を検証してください。

検証項目:
1. 要求事項が全て満たされているか（漏れチェック）
2. 事実関係に誤りがないか（数値・日付・法令名等）
3. 日本語の正確性（誤字脱字・不自然な表現）
4. エビデンス・出典URLが明記されているか（リサーチ系）
5. URL_EXTRACT_RULEが守られているか（RSC巡回）
6. WEEKLY_FALLBACK_RULEが守られているか（RSC巡回）
7. 所定のフォーマットから逸脱していないか
8. ポリシー「手抜きをしない。網羅する。魂を込める。」に照らして不十分な点
9. 省略・手抜き・「以下略」が含まれていないか

出力形式:
- 合否判定: PASS / FAIL
- 指摘事項（FAILの場合）: 具体的な修正箇所と理由
- リスク指摘（PASSの場合でも）: 気づいた点があれば記載
```

QA FAILの場合: 実行AIに自動差し戻し（1回リトライ）。2回目もFAILの場合はLINE通知「QA不合格: [パイプライン名] 手動確認が必要です」を送信し処理を一時停止。

---

## 15. 常駐自動フロー一覧

| スケジュール | ワークフロー | 実行AI | QA AI | 出力先 |
|:---|:---|:---|:---|:---|
| 毎朝 6:00 | RSCリサーチ巡回（7ターゲット） | Gemini 2.5 Flash | GPT-4o mini | Google Drive / Reports / RSC / + Dashboard Section 4 |
| 毎朝 7:00 | 朝ダッシュボード統合ブリーフィング | Gemini 2.5 Flash-Lite | GPT-4o mini | Google Drive / Daily_Report / + LINE通知 |
| 毎夕 18:45 | 各部門日次報告集約 | Gemini 2.5 Flash | GPT-4o mini | Google Drive / Reports / 該当部門 / |
| 毎夕 19:00 | リフレクション | Gemini 2.5 Flash | GPT-4o mini | Google Drive / Daily_Report /（Dashboard更新）+ LINE通知 |
| 毎週月曜 8:00 | BizDev市場スキャン | Gemini Flash + Claude Opus | GPT-4o mini | Google Drive / Reports / BizDev / + LINE通知 + 社長承認 |
| 毎月1日 9:00 | FIN月次開発費集計 | DeepSeek V3.2 | GPT-4o mini | Google Drive / Reports / FIN / + 社長承認 |
| 毎月給与日前 | OPS給与計算バッチ | Python（VPS）+ Claude Sonnet | GPT-4o mini | Google Drive / Reports / OPS / + 社長承認 |
| 毎週日曜 3:00 | n8nワークフロー自動バックアップ | n8n内部API | なし | Google Drive |
| 異常発生時 | アラート通知 | n8nエラーハンドラー | なし | LINE通知（即時） |

---

## 16. フィードバックループ設計（秋吉CEO方式応用）

### 各部門からCOOへの報告ルール

各部門はCOOに成果物を上げる。COOが集約して社長に届ける。

| タイミング | 報告内容 | 保存先 |
|---------|---------|-------|
| タスク完了時（即時） | 成果物URL + 3行サマリー | Google Drive / Reports / 該当部門 / |
| 異常発生時（即時） | エラー内容・影響範囲・暫定対応 | LINE通知（S/Aランク） |
| 毎夕18:45 | 当日の成果物一覧・完了タスク・未完了タスク | Google Drive / Reports / 該当部門 / |

COOは毎夕19:00のリフレクションで各部門の18:45報告を統合して社長に届ける。

### 毎日のループ

1. 毎朝7:00: COOがブリーフィング + シグナル検知 → LINE通知
2. 社長が確認 → 必要なら方向性指示（LINEで返信）
3. COOが自律的に実行
4. 毎夕19:00: COOがリフレクション → LINE通知
5. 社長が10秒で評価（OK / ここを直せ）
6. 評価をCOOのコンテキストに蓄積 → 判断精度向上

### 月次のループ

毎月1日: FINレポート（コスト・売上・進捗）
毎週月曜: BizDevレポート（事業機会）
月1回: COOシステムプロンプトの経営コンテキスト更新

---

## 17. インフラ構成（v3 確定）

```
シンVPS（162.43.78.67・24/365稼働・月750円）
├── n8n（オーケストレーション・COOの実行環境）
├── Anthropic API（Claude Sonnet/Opus）
├── Google AI API（Gemini Flash/Flash-Lite）
├── DeepSeek API
├── OpenAI API（GPT-4o mini・QA専用）
├── GitHub API（northstar-os・コンテキスト参照）
├── Google Drive API（ファイル保存）
├── Google Calendar API（予定・タスク取得）
└── LINE Messaging API（全通知・承認依頼・社長からの指示受信）
    ※LINE Notifyは2025/3/31終了のため代替
    ※プロバイダー: NorthStar / チャンネル: NorthStar（設定済み）

GitHub（bestthink01109/northstar-os・Private）
├── Development/（KENZAI・共生・shift_tool・平野工業・給与計算信和分）
├── ノーススターOSスキーム指示書/
├── KENZAI_launcher/
├── RSC_巡回ルール_20260501.md
├── ProductArch_NorthStarOS_完全版_20260501.md
└── Architecture_Plan_v3_完全版_20260501.md（本ファイル）

Google Drive（bestthink01109@gmail.com）
├── 📊 Reports/（各部門からCOOへの報告・成果物）
│   ├── OPS/（給与計算結果・差異レポート・シフト表）
│   ├── RSC/（リサーチレポート・シグナル検知結果）
│   ├── BizDev/（事業機会レポート）
│   ├── FIN/（月次コスト・収支レポート）
│   └── DEV/（開発進捗レポート）
├── 🏢【KENZAI】給与計算/
│   ├── 📥 01_ここに入力データをポン/（入力Excel・PDF・画像）
│   └── 📤 02_ここから完成品を取る/（出力CSV・差異レポート）
├── FUKUOKA/（福岡県庁リサーチレポート）
├── KUMAMOTO/（熊本県庁リサーチレポート）
├── MHLW/（厚労省・WAMNETレポート）
├── AI/（AIトレンドレポート）
└── Daily_Report/（Dashboard_YYYYMMDD.md）

CEOのMac（壁打ち・承認のみ）
├── claude.ai（Google Driveコネクタ接続・ダッシュボード読込・壁打ち）
└── LINEアプリ（通知受信・承認・COOへの指示）

不要なツール: Claude Code・Cursor・Antigravity（n8n構成では不要）
```

---

## インフラ役割分担（確定版・運用ルール）

| 保管場所 | 内容 | 理由 |
|---------|------|------|
| VPS（シンVPS） | アプリ（Python・n8n・実行環境） | 24/365自動実行のため |
| Google Drive | データ（入力Excel・出力CSV・ダッシュボード・リサーチレポート） | 毎日生成される成果物・社長が見るファイル |
| GitHub | 設計書・マニュアル・コードのバックアップ | バージョン管理・COOのコンテキスト参照 |

### コード管理の流れ

```
GitHub（マスター・正本）
    ↓ git clone / git pull
VPS（実行環境）
    ↓ 実行
Google Drive（データ入出力）
```

コードを更新する場合はGitHubにpushするだけ。VPS側はgit pullで最新版に自動同期する。社長は何もしなくてよい。

### VPSメモリ対策（確定）

現在の使用量: 約800MB（OS+Docker+n8n）
KENZAI追加後のピーク: 約980MB
対策1: スケジュール分散（KENZAIは深夜2時実行・RSC巡回と重複しない時間帯）
対策2: スワップ領域追加（追加コストゼロ・設定はPhase 2で実施）
アップグレード基準: 月次ピーク使用量が1.6GBを超えた時点で4GBプランに移行（月額+750円）

---

## 18. コスト構造（v3 確定）

### 月額固定費

| 項目 | 月額 |
|:---|:---|
| claude.ai Pro（壁打ちのみ） | 2,900円 |
| シンVPS（n8n） | 750円 |
| 固定費合計 | 3,650円 |

### API従量費（安定運用月）

| 項目 | 月額 |
|:---|:---|
| 常駐自動フロー（Gemini系） | 約480円 |
| COO判断・OPS支援（Claude Sonnet/Opus） | 約1,130円 |
| 帳票生成（DeepSeek） | 約11円 |
| QA（GPT-4o mini） | 約80円 |
| API従量合計 | 約1,701円 |

### トータル月額

| フェーズ | 月額 |
|:---|:---|
| 初月（PM検証集中） | 約22,000円 |
| 安定運用月（2ヶ月目以降） | 約5,351円 |
| 年間平均 | 約6,740円/月 |

---

## 19. 実行ロードマップ（v3 確定）

### Phase 1: 即時運用開始（今週〜）

| # | タスク | 状態 |
|:---|:---|:---|
| 1-1 | シンVPS契約・n8n起動 | 完了 |
| 1-2 | 5つのAPIキー登録（Anthropic・Gemini・DeepSeek・OpenAI・GitHub） | 完了 |
| 1-3 | GitHubリポジトリ作成・コンテキストファイルアップロード | 完了 |
| 1-4 | LINE Messaging API設定（プロバイダーNorthStar・チャンネルアクセストークン発行） | 完了 |
| 1-5 | n8nにLINE Messaging API登録 | 次回着手 |
| 1-6 | 社長のLINEにボットを友達登録・ユーザーID取得 | 次回着手 |
| 1-7 | claude.ai Google Driveコネクタ設定 | 次回着手 |
| 1-8 | 朝7:00ブリーフィングワークフロー構築 | 次回着手 |
| 1-9 | 夕19:00リフレクションワークフロー構築 | 次回着手 |
| 1-10 | 朝6:00 RSCリサーチ巡回ワークフロー構築 | 次回着手 |
| 1-11 | Google Calendar API連携 | 次回着手 |

### Phase 2: OPS自動化 + 全パイプライン構築（2〜4週間）

| # | タスク |
|:---|:---|
| 2-1 | OPS-Cシフト作成の完全自動化（shift_exporter.py） |
| 2-2 | OPS-K KENZAI給与計算自動化 |
| 2-3 | OPS-A 信和ミート給与計算自動化 |
| 2-4 | BizDevパイプライン実装（毎週月曜自動スキャン） |
| 2-5 | FINパイプライン実装（毎月1日） |
| 2-6 | CEO承認フロー（LINEワンタップ） |
| 2-7 | Googleカレンダー双方向同期 |
| 2-8 | The Task Protocol完全実装 |

### Phase 3: 全パイプライン展開 + 外販準備（1〜3ヶ月）

| # | タスク |
|:---|:---|
| 3-1 | Supabase東京に本番DB構築 |
| 3-2 | プロダクト開発（3入力手法・データパイプライン） |
| 3-3 | Webアプリ版ダッシュボード開発 |
| 3-4 | 外販向けマルチテナント設計 |
| 3-5 | MVP施設2〜3社デモ・フィードバック |

---

## 20. 検証基準（v3 確定）

### Phase 1完了条件

- 朝7:00ブリーフィングが5営業日連続でLINEに届く
- 夕19:00リフレクションが5営業日連続で動作
- RSC巡回7ターゲットが全て自動化済み
- 社長の朝の確認作業が15秒以内で完了する
- claude.aiでDashboardを読み込みながら対話できる

### Phase 2完了条件

- OPS全系統の月次処理時間が手作業の50%以下に短縮
- 社長の実稼働時間3時間以下が週4日以上
- BizDevが毎週月曜に事業機会レポートを自動提出
- The Task Protocolが完全稼働（Googleカレンダー一元管理）

### Phase 3完了条件

- 全パイプライン稼働
- MVP施設からフィードバック取得完了
- 社長の実稼働時間1時間以下が常態化

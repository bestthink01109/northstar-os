# コンテキスト引継ぎ書: 個別仕様書作成セッション

**作成日**: 2026/04/16
**前セッション**: Architecture Plan v2 マスター設計書 + QAレポート作成
**次セッションのミッション**: パイプライン個別仕様書9本の作成

---

## 🎯 このチャットで最初に貼るプロンプト

```
このチャットではNorth Star OS v3の個別仕様書を作成します。

【事前準備】
プロジェクトナレッジに以下がアップロード済みのはずです:
- Architecture_Plan_v2_Master.md（マスター設計書・確定版）
- QA_Report_Master_v2.md（前セッションのQAレポート）

また既存ファイルも参照:
- Architecture_Plan_Original.md（v1・詳細仕様の元ソース）
- KENZAIシステム_引継ぎ仕様書_コンテキスト.md
- context_handover.md（信和ミート給与らくだRPA）
- AI引継ぎプロンプト.md（信和ミートOCR+CSV）
- n8n_Implementation_Plan_v2_20260413.md

【本日の作業】
コンテキスト引継ぎ書（このファイル）を読み込み、指示された個別仕様書を作成してください。

【絶対ルール】
- ALIGN FIRST。手抜きをしない。網羅する。魂を込める。
- 各個別仕様書は「PM作成 → QAチェック(GPT-5.4 mini役を代行) → CEO承認」のフローを踏む
- v1 Originalや既存プロジェクトファイルから該当情報を漏れなく転記する
- QAで指摘があったら必ず修正してから次に進む
```

---

## 📋 作成対象の個別仕様書（9本）

| # | ファイル名 | 優先度 | 主な情報源 | 特記事項 |
|:---|:---|:---|:---|:---|
| 1 | Pipeline_OPS-A_Spec.md | ★★★ | context_handover.md + AI引継ぎプロンプト.md | 信和ミート。2モジュール構成（Mac OCR + Windows RPA）。EMPLOYEE_MASTER 30名分、座標設定、残課題3つを完全収録 |
| 2 | Pipeline_OPS-K_Spec.md | ★★★ | KENZAIシステム_引継ぎ仕様書_コンテキスト.md | KENZAIグループ（平野工業/福岡プラント/純青）。WeeklyAllocator労務計算ロジック、3段フォールバックOCR、Excelクローン出力、差異レポート |
| 3 | Pipeline_OPS-C_Spec.md | ★★★ | （設計書は再作成。現時点の情報は本引継ぎ書内） | 介護施設。設計書「再作成」。2段階QA構造（シフト表QA#1 + 出勤簿QA#2）必須 |
| 4 | Pipeline_RSC_Spec.md | ★★ | Architecture_Plan_Original.md | 7ターゲット詳細タスク仕様を完全収録（URL_EXTRACT_RULE + WEEKLY_FALLBACK_RULE + 巡回タスク詳細テーブル） |
| 5 | Pipeline_BizDev_Spec.md | ★★ | Architecture_Plan_Original.md §3 | モード1（受動）+ モード2（能動）の両動作モード詳細 |
| 6 | Pipeline_DEV_Spec.md | ★ | Architecture_Plan_Original.md | Cursor+Claude / DeepSeek V3.2の使い分け |
| 7 | Pipeline_FIN_Spec.md | ★ | Architecture_Plan_Original.md | 自社財務に限定。代行業務[OPS]との分離ポリシー明記 |
| 8 | Pipeline_MKT_Spec.md | ☆ | Architecture_Plan_Original.md | Phase 3実装。スキマ時間で作成可 |
| 9 | Pipeline_OPS-Common_Spec.md | ☆ | （設計未着手） | 社保/雇保書類。テンプレート整理から |

**推奨作成順**: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

---

## 📐 個別仕様書の共通構造（テンプレート）

各仕様書は以下の章立てで作成する:

```
# Pipeline_[タグ]_Spec.md

## 0. パイプライン概要
- タグ / 部門名 / 目的 / 状態

## 1. 業務フロー詳細
- トリガー条件
- 処理ステップ（PM→実行→QA→CEO承認→出力）
- フロー図（ASCII）

## 2. 使用AI / ツール
- AIモデルと役割
- ローカルツール（該当する場合）

## 3. 入力仕様
- 入力データの形式
- 入力元（ファイル/API/手動）

## 4. 処理ロジック
- 核心ロジックの詳細（コード仕様含む）
- 例外処理

## 5. 出力仕様
- 出力データの形式
- 出力先

## 6. QA基準
- 検証項目（マスター設計書§4に準拠）
- パイプライン固有の検証ポイント

## 7. 運用スケジュール
- 実行タイミング
- 手動起動トリガー

## 8. エラー対応
- エラー種別と対処
- フォールバック動作

## 9. 開発状況と残タスク
- 進捗度
- 既知の課題
- ネクストアクション

## 10. 関連ファイル / 参照
- コードファイル
- マスター設計書の該当セクション
```

---

## 🔍 各個別仕様書の必須収録項目

### Pipeline_OPS-A_Spec.md（信和ミート）

**必須収録:**

- 2モジュール構成:
  - モジュール1（Mac）: `timecard_to_csv.py` — HEIC/JPG → Gemini OCR → CSV
  - モジュール2（Windows）: `auto_input.py` — CSV → pyautoguiで給与らくだ自動入力
- 絶対ルール3つ:
  1. 定時丸め（出勤打刻が定時より早い場合、定時に書き換え）
  2. 欠勤判定（社員は水曜・日曜以外の平日で無打刻なら欠勤フラグ）
  3. 有給処理（パートの有給は打刻空欄+有給フラグ+有給付与時間を設定）
- EMPLOYEE_MASTER 30名分の完全リスト（index 0〜29、イトウエルシー・武藤信悟は要確認）
- 座標設定（COORDS辞書）全リスト
- タイムカード入力画面のページング仕様（1-12日→13-24日→25-31日）
- 未解決課題3つ:
  1. EMPLOYEE_MASTERのindex値不一致（イトウエルシー・武藤信悟の設定確認）
  2. 一覧スクロールのバグ（533行目削除で修正）
  3. チェックボックスのピクセル判定（有給/欠勤は未テスト）
- NFD濁点分離対応（`unicodedata.normalize('NFC')`）
- MAX社 ER-Sカードという紙タイムカードの型番

### Pipeline_OPS-K_Spec.md（KENZAIグループ）

**必須収録:**

- ディレクトリ構造（hirano/fukuoka_plant/junsei/core/parsers/exporters/）
- 3社の進捗:
  - 平野工業: 100%・実データテスト待ち
  - 福岡プラント機工: 実データフォーマット検証待ち
  - 純青: 実データ検証待ち
- 平野工業の勤務体系:
  - 一般社員: 月〜金 7時間（8:00-17:00、休憩2h）、土 5時間（8:00-15:00、休憩2h）、週40時間ピッタリ
  - 平野珠美氏特例: 月〜金 8時間、週40時間
- 休憩の動的控除: 10:00-10:30、12:00-13:00、14:00-14:30
- 残業の2階層分類:
  - 法定外残業: 1日8時間超（日次確定、相殺なし）
  - 法定内残業（延長）: 所定〜法定の間
- WeeklyAllocator根幹技術（週40時間上限バッファ管理）
- 出力: Excelクローン出力 + 差異レポート + 給与らくだCSV
- employees.csv動的化（退職・新入社員・名前変更の対応）
- OCRエンジン3段フォールバック（Vision / Claude API / Gemini API）
- 新規企業追加手順（config.py + employees.csvで対応）

### Pipeline_OPS-C_Spec.md（介護施設）

**必須収録:**

- 業務フロー（2段階QA構造）:
  1. シフト表作成 → QA#1 → CEO承認#1 → 施設提出
  2. 出勤実績写真受領 → OCR → 正式出勤簿 → 集計 → CSV → QA#2 → CEO承認#2
- 特定施設入居者生活介護の人員配置基準（3:1等）
- 設計書再作成で定義すべき項目7つ:
  1. 施設の勤務体系（日勤/夜勤/早番/遅番）
  2. 人員配置基準
  3. シフト表のフォーマット
  4. 出勤実績写真のフォーマット
  5. 正式出勤簿のフォーマット
  6. 給与計算ルール（夜勤手当・変形労働時間制・処遇改善加算）
  7. 給与らくだCSVのフォーマット
- QA#1の検証項目: 人員配置基準、連続勤務日数、希望休反映漏れ、週40時間上限
- QA#2の検証項目: シフトvs実績の差異、出勤簿の計算結果、人員配置基準の実績充足
- 現時点は「設計書再作成」段階であることを明記

### Pipeline_RSC_Spec.md（リサーチ巡回）

**必須収録（v1 Originalから完全転記）:**

- 共通ルール定義:
  - URL_EXTRACT_RULE（絶対URL併記、相対パス変換、URLなし明記、出力形式厳守）
  - WEEKLY_FALLBACK_RULE（1週間以内全記載、該当なしは直近1件、「該当なし」禁止）
- 巡回タスク詳細（7ターゲット全て）:
  1. 福岡県庁（pref.fukuoka.lg.jp/soshiki/4600400/） — 14見出し、7日、FUKUOKA
  2. 熊本県庁（pref.kumamoto.jp/soshiki/32/） — 10見出し、7日、KUMAMOTO
  3. 厚労省【障害】 — 30日、MHLW
  4. 厚労省【介護】 — 30日、MHLW
  5. WAMNET【障害】（wam.go.jp/gyoseiShiryou/rireki?tab=4） — 30日、MHLW
  6. WAMNET【介護】（wam.go.jp/gyoseiShiryou/rireki?tab=2） — 30日、MHLW
  7. AIトレンド（Google News RSS） — 60日、AI
- 技術的注意点: JavaScript動的生成対応、アクセス間隔5秒以上、リトライ3回
- 朝のフロー: 06:00起動 → 06:50完了 → 07:00ブリーフィングに統合

### Pipeline_BizDev_Spec.md

**必須収録（v1 Originalから完全転記）:**

- モード1: 受動（CEOお題を事業化）のフロー図
- モード2: 能動（市場から逆引き）のフロー図 — 毎週月曜自動起動
- 3つの評価軸: 市場性 / 適合性 / 実現性
- TAM/SAM/SOM推計手法
- Claude Opusでの事業判断プロセス

### Pipeline_DEV_Spec.md

**必須収録:**

- Cursor+Claude（プロダクトコード）とDeepSeek V3.2（スクリプト/文書）の使い分け
- Lovable（デモ専用）の位置づけ
- PRD生成→コード実装→QA→CEO承認の2段階承認フロー

### Pipeline_FIN_Spec.md

**必須収録:**

- 自社財務の範囲: 開発費管理 / ツール外販の売掛・入金 / 消し込み
- [OPS]との分離ポリシー（給与系は絶対に[FIN]で扱わない）
- 月次開発費集計の自動化（DeepSeek V3.2）

### Pipeline_MKT_Spec.md

**必須収録:**

- Phase 3実装（Week 4完了後、5月中旬〜）
- DeepSeek V3.2での資料・原稿生成
- 配信実行フロー

### Pipeline_OPS-Common_Spec.md

**必須収録:**

- 書類一覧:
  - 入社時: 雇用保険資格取得届、社保資格取得届、扶養届
  - 退社時: 雇用保険資格喪失届、社保資格喪失届、離職票
  - 年度更新: 労働保険概算・確定保険料申告書
  - 算定基礎届: 被保険者報酬月額算定基礎届
  - 月額変更届: 被保険者報酬月額変更届
  - 賞与支払届: 被保険者賞与支払届
- 対象: 全クライアント（信和ミート・KENZAIグループ・介護施設）

---

## ⚠️ 絶対に守るべき注意事項

1. **マスター設計書の変更は絶対禁止**: 個別仕様書はマスター設計書に従属する。マスターの記述と矛盾する内容を個別仕様書に書かないこと。矛盾が発生した場合はCEOに確認。

2. **v1 Originalからの転記は原文忠実**: 特に[RSC]7ターゲット詳細タスク仕様、[BizDev]モード1/2の詳細は、v1原文から一字一句正確に転記すること。

3. **QAは必ず実施**: 各個別仕様書の作成後、QA_Report_[タグ].md を作成してから次の仕様書へ進む。

4. **OPS-Cは「現時点情報のみ」で書く**: 設計書再作成前なので、詳細確定事項以外は「設計書再作成時に確定」と明記すること。勝手に仕様を作らない。

5. **CEOの承認を各仕様書ごとに取る**: 全9本を一気に作らない。1本ごとにCEO確認を経てから次へ。

---

## 📊 作業進捗管理

次のチャットで以下を記録しながら進める:

```
□ Pipeline_OPS-A_Spec.md  ──── PM作成 / QA / CEO承認
□ Pipeline_OPS-K_Spec.md  ──── PM作成 / QA / CEO承認
□ Pipeline_OPS-C_Spec.md  ──── PM作成 / QA / CEO承認
□ Pipeline_RSC_Spec.md    ──── PM作成 / QA / CEO承認
□ Pipeline_BizDev_Spec.md ──── PM作成 / QA / CEO承認
□ Pipeline_DEV_Spec.md    ──── PM作成 / QA / CEO承認
□ Pipeline_FIN_Spec.md    ──── PM作成 / QA / CEO承認
□ Pipeline_MKT_Spec.md    ──── PM作成 / QA / CEO承認
□ Pipeline_OPS-Common_Spec.md ─ PM作成 / QA / CEO承認
```

---

## 🎬 次のチャットの開始手順

**CEOの操作:**

1. 新規チャットを開く（同じプロジェクト内）
2. 冒頭に以下を貼り付け:

   ```
   コンテキスト引継ぎ書（Context_Handover_for_Pipeline_Specs.md）を読み込み、
   まずPipeline_OPS-A_Spec.mdの作成から始めてください。
   ```

3. Claudeが引継ぎ書を読み込み、OPS-A仕様書の作成に入る

**Claudeの最初のアクション:**

1. 本引継ぎ書を全文確認
2. プロジェクトナレッジから関連ファイルを検索
3. OPS-A仕様書のドラフトを作成
4. QAチェック実施
5. CEO承認を仰ぐ

---

## 📎 参照ファイル一覧

**マスター設計書（プロジェクトナレッジ）:**

- Architecture_Plan_v2_Master.md ★本作業の根幹

**既存プロジェクトファイル:**

- Architecture_Plan_Original.md（v1・詳細仕様のソース）
- KENZAIシステム_引継ぎ仕様書_コンテキスト.md（OPS-Kの元ソース）
- KENZAIシステム運用マニュアル.md（OPS-K運用情報）
- context_handover.md（OPS-AのWindows RPA側）
- context_handover_v2_3.md（OPS-Aの更新情報）
- AI引継ぎ_フロンフト.md もしくは AI引継ぎプロンプト.md（OPS-AのMac側）
- n8n_Implementation_Plan_20260413.md（n8n実装計画v1）
- n8n_Implementation_Plan_v2_20260413.md（n8n実装計画v2）
- SKILL.md（n8n VPSセットアップスキル）

**前セッションのQA:**

- QA_Report_Master_v2.md

---

**「ALIGN FIRST. Then Take Massive Action.」**
**「手抜きをしない。網羅する。魂を込める。」**

上記2つの経営理念に則り、次のセッションでも魂を込めて個別仕様書9本を作成すること。

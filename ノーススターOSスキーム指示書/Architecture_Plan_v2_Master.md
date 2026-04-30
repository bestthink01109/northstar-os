# North Star OS v3：マスター設計書 v2

# ダッシュボード起点・サブエージェント並列オーケストレーション

---

## 変更履歴

| 日付 | 版 | 変更内容 |
|:---|:---|:---|
| 2026/04/11 | v1 | 初版（Architecture Plan Original） |
| 2026/04/16 | v2 | [OPS]パイプライン追加。文書を「マスター設計書 + パイプライン個別仕様書」に分割 |

**文書構成**: 本マスター設計書は全体構成・共通基盤を定義する。各パイプラインの詳細仕様は以下の個別仕様書を参照:
- `Pipeline_DEV_Spec.md` — 開発パイプライン
- `Pipeline_BizDev_Spec.md` — 事業開発パイプライン
- `Pipeline_RSC_Spec.md` — リサーチ巡回パイプライン
- `Pipeline_FIN_Spec.md` — 経理パイプライン
- `Pipeline_MKT_Spec.md` — マーケティングパイプライン
- `Pipeline_OPS-A_Spec.md` — 信和ミート給与計算
- `Pipeline_OPS-K_Spec.md` — KENZAIグループ給与計算
- `Pipeline_OPS-C_Spec.md` — 介護施設シフト/出勤簿/給与
- `Pipeline_OPS-Common_Spec.md` — 社保/雇保共通書類

---

## 0. 承認済み設計方針

| 項目 | 確定内容 |
|:---|:---|
| 起点 | ダッシュボード（CEO + AIコーチの対話） |
| 共通構造 | 全パイプライン「PM → 実行 → QA → CEO承認 → 出力」 |
| 並列化 | PMの軍令から複数プロジェクトをサブエージェントとして並列稼働 |
| PM AI | Claude Sonnet（通常）/ Opus（法規制・事業判断） |
| 開発 AI | Cursor + Claude / DeepSeek V3.2（本番）。Lovableはデモ専用 |
| QA AI | GPT-5.4 mini（必ず別プロバイダ）。全パイプライン共通 |
| 定型処理 AI | Gemini 2.5 Flash / Flash-Lite |
| DB/ホスティング | Supabase東京リージョン |
| フロントデプロイ | Vercel（本番）/ Lovable（デモ） |
| オーケストレーション | n8n（VPS上。24/365稼働。CEOのMacに非依存） |
| 通知 | LINE Notify |
| バックアップ環境 | Claude Cowork（Antigravityリミット時） |
| Perplexity API | 使わない |
| 経理[FIN] | 開発費管理・売掛・入金・消し込み（給与関連は別PJ） |
| 事業開発[BizDev] | 新規事業の飯のたね発見・事業化（介護に限定しない） |
| 代行業務[OPS] | 社長の代行業務（給与計算・シフト・出勤簿・社保/雇保）を自動化。3系統パラレル運用 |

---

## 1. 全体アーキテクチャ

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              North Star OS v3 全体構成図（v2 — [OPS]統合版）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌───────────────────────────────────────────────────────┐
  │          Layer 4: CEO インターフェース                 │
  │                                                       │
  │  ダッシュボード ←→ AIコーチ対話（Cursor / Claude）    │
  │                                                       │
  │  1. Core Vision           ←→ 対話                    │
  │  2. Today's Schedule      ←→ 対話(全件)              │
  │  3. 1-Week All            ←→ 対話(全件)              │
  │  4. Research Facts        ←  MASTER自動掲載           │
  │  5. AI Task Workspace     ←→ 対話                    │
  │  6. PM Strategy Report    →  パイプラインへ           │
  │  7. Reflection            ←→ 結果自動 + 対話          │
  │                                                       │
  │  ＋ CEO承認：スマホLINEでワンタップ                   │
  └────────────────────┬──────────────────────────────────┘
                       │ 決断の書（複数PJ指示含む）
                       ▼
  ┌───────────────────────────────────────────────────────┐
  │          Layer 3: PM層（司令塔）                       │
  │          AI: Claude Sonnet / Opus（判断の重さで切替）  │
  │                                                       │
  │  決断の書 → プロジェクト分解 → 各PJにPRD生成          │
  │  → サブエージェントを並列起動                         │
  └────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┬───────────────┐
       ▼               ▼               ▼               ▼
  ┌───────────────────────────────────────────────────────┐
  │       Layer 2: サブエージェント層(VPS上・並列実行)     │
  │       オーケストレーター: n8n                          │
  │       ※ CEOのMacに非依存。24/365稼働                  │
  │                                                       │
  │  ┌─[DEV]──────┐ ┌─[BizDev]────┐ ┌─[RSC]──────┐      │
  │  │ 開発        │ │ 事業開発    │ │ リサーチ    │      │
  │  │ 実行:       │ │ 実行:       │ │ 実行:       │      │
  │  │ Cursor+     │ │ Gemini Flash│ │ Gemini Flash│      │
  │  │ Claude /    │ │ + Claude    │ │             │      │
  │  │ DeepSeek    │ │   Opus      │ │ QA:         │      │
  │  │ QA:         │ │ QA:         │ │ GPT-5.4 mini│      │
  │  │ GPT-5.4 mini│ │ GPT-5.4 mini│ │ →CEO承認    │      │
  │  │ →CEO承認    │ │ →CEO承認    │ │ →Drive      │      │
  │  │ →GitHub/    │ │ →Drive      │ │             │      │
  │  │  Vercel     │ │             │ │             │      │
  │  └─────────────┘ └─────────────┘ └─────────────┘      │
  │                                                       │
  │  ┌─[FIN]──────┐ ┌─[MKT]──────┐ ┌─デモ用──────┐      │
  │  │ 経理        │ │ マーケ      │ │ プロト      │      │
  │  │ 実行:       │ │(Phase3)     │ │ タイプ      │      │
  │  │ DeepSeek    │ │ 実行:       │ │ Lovable     │      │
  │  │ QA:         │ │ DeepSeek    │ │(営業提案時  │      │
  │  │ GPT-5.4 mini│ │ QA:         │ │ のみ起動)   │      │
  │  │ →CEO承認    │ │ GPT-5.4 mini│ │             │      │
  │  │ →Drive      │ │ →CEO承認    │ │             │      │
  │  └─────────────┘ └─────────────┘ └─────────────┘      │
  │                                                       │
  │  ╔═══════════════════════════════════════════════════╗ │
  │  ║  [OPS] 代行業務自動化パイプライン(v2で追加)       ║ │
  │  ║  ※ 3系統パラレル運用。統一しない。                ║ │
  │  ║                                                   ║ │
  │  ║  ┌─[OPS-A]────────┐ ┌─[OPS-K]────────────────┐  ║ │
  │  ║  │ 信和ミート       │ │ KENZAIグループ         │  ║ │
  │  ║  │(社労士受託)      │ │(社労士受託)            │  ║ │
  │  ║  │                  │ │ 平野工業/福岡プラント/  │  ║ │
  │  ║  │ 紙タイムカード   │ │ 純青(+新規企業)        │  ║ │
  │  ║  │   ↓ OCR          │ │                         │  ║ │
  │  ║  │ データ化         │ │ Excel/PDF/画像の出勤簿 │  ║ │
  │  ║  │   ↓              │ │   ↓ OCR/パーサー        │  ║ │
  │  ║  │ 給与らくだ入力   │ │ 労務計算エンジン       │  ║ │
  │  ║  │                  │ │   ↓                     │  ║ │
  │  ║  │ 実行: OCR+Python │ │ 集計+差異レポート      │  ║ │
  │  ║  │       +pyautogui │ │   ↓                     │  ║ │
  │  ║  │ QA: GPT-5.4 mini │ │ 給与らくだ向けCSV出力  │  ║ │
  │  ║  │ →CEO承認         │ │                         │  ║ │
  │  ║  │ →給与らくだ      │ │ 実行: KENZAIエンジン   │  ║ │
  │  ║  │  (Windows PC)    │ │ QA: GPT-5.4 mini       │  ║ │
  │  ║  │                  │ │ →CEO承認                │  ║ │
  │  ║  └──────────────────┘ │ →給与らくだ(Win PC)    │  ║ │
  │  ║                       └─────────────────────────┘  ║ │
  │  ║                                                   ║ │
  │  ║  ┌─[OPS-C]──────────────────────────────────────┐ ║ │
  │  ║  │ 介護施設(コンサル先)                          │ ║ │
  │  ║  │ シフト表作成 → QA#1 → CEO承認#1 → 施設提出  │ ║ │
  │  ║  │ 写真での出勤実績 → OCR → 正式出勤簿         │ ║ │
  │  ║  │ → 集計 → CSV → QA#2 → CEO承認#2            │ ║ │
  │  ║  │ 実行: shift_exporter+OCR+payroll_engine       │ ║ │
  │  ║  └───────────────────────────────────────────────┘ ║ │
  │  ║                                                   ║ │
  │  ║  ┌─[OPS-共通]───────────────────────────────────┐ ║ │
  │  ║  │ 社会保険・雇用保険関連書類(全クライアント)    │ ║ │
  │  ║  └───────────────────────────────────────────────┘ ║ │
  │  ╚═══════════════════════════════════════════════════╝ │
  │                                                       │
  │  ┌─ 常駐自動フロー ─────────────────────────────┐    │
  │  │  毎朝 6:00   [RSC]リサーチ巡回                │    │
  │  │  毎朝 7:00   ブリーフィング(Gemini Flash-Lite) │    │
  │  │  毎夕 19:00  リフレクション(Gemini Flash)      │    │
  │  │  毎週月曜    BizDev市場スキャン(Gemini+Opus)   │    │
  │  │  月次        開発費集計(DeepSeek)              │    │
  │  │  毎月給与日前 [OPS]給与計算バッチ               │    │
  │  │  毎週日曜    n8nバックアップ                     │    │
  │  │  異常時      アラート(即時LINE通知)             │    │
  │  └─────────────────────────────────────────────────┘   │
  └───────────────────────────────────────────────────────┘
                       │
                       ▼
  ┌───────────────────────────────────────────────────────┐
  │          Layer 1: データ・連携層                       │
  │                                                       │
  │  Supabase東京 │ Google Calendar/Drive │ GitHub         │
  │  LINE Notify  │ Vercel               │ Lovable(デモ)  │
  │  給与らくだ   │ OCRエンジン          │                 │
  │  (Windows PC) │ (Vision/Claude/Gemini)│                 │
  └───────────────────────────────────────────────────────┘
```

---

## 2. 全パイプライン一覧（v2 確定版）

| タグ | パイプライン | PM AI | 実行AI | QA AI | 状態 | 個別仕様書 |
|:---|:---|:---|:---|:---|:---|:---|
| [DEV] | 開発 | Claude Sonnet/Opus | Cursor+Claude / DeepSeek | GPT-5.4 mini | Phase 1で開始 | Pipeline_DEV_Spec.md |
| [BizDev] | 事業開発 | Claude Opus | Gemini Flash + Claude Opus | GPT-5.4 mini | Phase 1で開始 | Pipeline_BizDev_Spec.md |
| [RSC] | リサーチ | Claude Sonnet | Gemini 2.5 Flash | GPT-5.4 mini | Phase 1で開始 | Pipeline_RSC_Spec.md |
| [FIN] | 経理 | Claude Sonnet | DeepSeek V3.2 | GPT-5.4 mini | Phase 1で開始 | Pipeline_FIN_Spec.md |
| [MKT] | マーケティング | Claude Sonnet | DeepSeek V3.2 | GPT-5.4 mini | Phase 3で実装 | Pipeline_MKT_Spec.md |
| [OPS-A] | 信和ミート給与計算 | Claude Sonnet | OCR+Python+pyautogui | GPT-5.4 mini | 開発着手済み | Pipeline_OPS-A_Spec.md |
| [OPS-K] | KENZAIグループ給与計算 | Claude Sonnet | KENZAIエンジン（Python） | GPT-5.4 mini | 開発着手済み | Pipeline_OPS-K_Spec.md |
| [OPS-C] | 介護施設シフト/出勤簿/給与 | Claude Sonnet | shift_exporter+OCR+payroll_engine | GPT-5.4 mini | 設計書再作成必要 | Pipeline_OPS-C_Spec.md |
| [OPS-共通] | 社保/雇保書類 | Claude Sonnet/Opus | テンプレート生成+AI補助 | GPT-5.4 mini | 設計未着手 | Pipeline_OPS-Common_Spec.md |
| 定例 | リサーチ巡回・通知 | ─ | Gemini Flash-Lite | ─ | Phase 2で自動化 | （RSC内に含む） |
| デモ | 営業用プロトタイプ | ─ | Lovable | ─ | 必要時のみ起動 | ─ |

---

## 3. マルチモデルAI配置表（確定 + OPS追加）

| ステップ | 担当AI | コスト(入/出 per 1M) | n8n接続方式 | 選定理由 |
|:---|:---|:---|:---|:---|
| PM（通常仕様策定） | Claude Sonnet 4.6 | $3 / $15 | HTTP Request（Anthropic API） | PRD生成・ロジック検証。十分な推論力 |
| PM（法規制・事業判断） | Claude Opus 4.6 | $5 / $25 | HTTP Request（Anthropic API） | 妥協不可の高度判断。自動ルーティング |
| 開発（プロダクト） | Cursor + Claude | Cursor Pro内 | n8n外（CEOがCursorで実行） | 精密なビジネスロジック実装。追加コスト0 |
| 開発（スクリプト/文書/帳票） | DeepSeek V3.2 | $0.14 / $0.28 | HTTP Request（DeepSeek API） | PRDがあれば品質十分。コスト1/20 |
| 開発（デモ用プロトタイプ） | Lovable | 月$20〜50 | n8n外（必要時のみ手動起動） | 営業提案時の使い捨てデモ専用 |
| 事業開発（市場スキャン） | Gemini 2.5 Flash | $0.30 / $2.50 | HTTP Request（Google AI API） | Web検索統合。大量情報の低コスト処理 |
| 事業開発（事業判断） | Claude Opus 4.6 | $5 / $25 | HTTP Request（Anthropic API） | 「飯のたねになるか」の判断は最高品質 |
| リサーチ（市場調査） | Gemini 2.5 Flash | $0.30 / $2.50 | HTTP Request（Google AI API） | Web検索+要約。コスト効率最優先 |
| QA（全パイプライン共通） | GPT-5.4 mini | $0.75 / $4.50 | OpenAIノード（n8nネイティブ） | 別プロバイダで盲点補完。統一管理 |
| 定型処理（巡回・通知） | Gemini 2.5 Flash-Lite | $0.10 / $0.40 | HTTP Request（Google AI API） | 最安。大量定型処理 |
| [OPS] OCR読取 | KENZAIエンジン（Vision/Claude/Gemini 3段フォールバック） | 変動 | ローカル実行（Mac） | 手書き認識精度の最大化 |
| [OPS] 労務計算 | payroll_engine.py（ローカル実行） | 0円 | ローカル実行（Mac） | 法定計算はコードで厳密処理。AIに任せない |
| [OPS] シフト生成 | shift_exporter.py（ローカル実行） | 0円 | ローカル実行（Mac） | 人員配置基準の厳密遵守 |
| [OPS] 給与らくだ入力 | auto_input.py（pyautogui） | 0円 | ローカル実行（Windows PC） | RPA的座標クリック方式 |
| [OPS] 書類生成補助 | Claude Sonnet 4.6 | $3 / $15 | HTTP Request（Anthropic API） | 社保・雇保書類の正確な生成 |

**モデルルーティングの原則**:
- 通常のPM判断 → Claude Sonnet 4.6
- 法規制（処遇改善加算・介護報酬等）または事業のGo/No-Go判断 → Claude Opus 4.6に自動昇格
- ルーチンのコード/文書/帳票生成 → DeepSeek V3.2（コスト1/20）
- 大量テキスト処理・Web検索 → Gemini 2.5 Flash
- 定型処理（巡回・通知・要約） → Gemini 2.5 Flash-Lite
- QAは必ずGPT-5.4 mini（全パイプライン共通。PMや実行とは別プロバイダにすることで盲点を補完）

月間コスト推定（1日平均3PJ並列）: 約$50〜120/月（約7,500〜18,000円）

---

## 4. QA必須ルール（全パイプライン共通）

共通構造「PM → 実行 → QA → CEO承認 → 出力」に基づき、n8n上の全パイプラインに以下のQAノードを必須で組み込む。

**QA担当AI**: GPT-5.4 mini（OpenAI API）— 全パイプライン統一

**QAノードの標準プロンプト**:
```
あなたはQA（品質保証）担当AIです。
以下の「PRD（要求仕様）」と「成果物」を照合し、品質を検証してください。

検証項目:
1. PRDの要求事項が全て満たされているか（漏れチェック）
2. 事実関係に誤りがないか（数値・日付・法令名等）
3. 日本語の正確性（誤字脱字・不自然な表現）
4. エビデンス・出典URLが明記されているか（リサーチ系の場合）
5. 当社ポリシー「手抜きをしない。網羅する。魂を込める。」に照らして不十分な点

出力形式:
- 合否判定: PASS / FAIL
- 指摘事項（FAILの場合）: 具体的な修正箇所と理由
- リスク指摘（PASSの場合でも）: 気づいた点があれば記載
```

**QAの適用範囲（例外なし）**:

| パイプライン | QA対象 | QA後のフロー |
|:---|:---|:---|
| [DEV] | PRD、生成コード、生成文書 | QA PASS → CEO承認 → GitHub/Drive保存 |
| [BizDev] | 市場スキャン結果、事業機会レポート | QA PASS → CEO承認 → Drive保存 |
| [RSC] | リサーチ巡回結果（7ターゲット全て） | QA PASS → ダッシュボードに自動反映 |
| [FIN] | 月次開発費レポート | QA PASS → CEO承認 → Drive保存 |
| [MKT]（Phase 3） | マーケティング資料・配信原稿 | QA PASS → CEO承認 → 配信実行 |
| [OPS-A] | OCR読取結果、給与データ | QA PASS → CEO承認 → 給与らくだ入力 |
| [OPS-K] | 差異レポート、CSV | QA PASS → CEO承認 → 給与らくだ入力 |
| [OPS-C] | シフト表（QA#1）、出勤簿+CSV（QA#2） | 各QA PASS → 各CEO承認 |
| [OPS-共通] | 届出書類 | QA PASS → CEO承認 → Drive保存 |
| 朝ブリーフィング | ダッシュボード全体 | QA PASS → LINE通知 + Drive保存 |
| 夕リフレクション | リフレクション要約 | QA PASS → LINE通知 + Dashboard更新 |

**QA FAIL時の自動処理**: n8nは自動的に実行AIに差し戻し（1回リトライ）。2回目もFAILの場合はCEOにLINE通知「QA不合格: [パイプライン名] 手動確認が必要です」を送信し、処理を一時停止する。

---

## 5. n8n API接続一覧

| # | サービス | 担当AI/モデル | n8n接続方式 | 認証方式 | 取得先 |
|:---|:---|:---|:---|:---|:---|
| 1 | Google Calendar/Drive/Sheets | ─（データ取得のみ） | Google Calendar/Drive/Sheets ノード | OAuth2 | Google Cloud Console |
| 2 | Anthropic API | Claude Sonnet 4.6 / Opus 4.6 | HTTP Request ノード | API Key (Header: x-api-key) | https://console.anthropic.com/ |
| 3 | Google AI API | Gemini 2.5 Flash / Flash-Lite | HTTP Request ノード | API Key (Header) | https://aistudio.google.com/ |
| 4 | DeepSeek API | DeepSeek V3.2 | HTTP Request ノード | API Key (Header: Authorization) | https://platform.deepseek.com/ |
| 5 | OpenAI API | GPT-5.4 mini（QA専用） | OpenAI ノード（n8nネイティブ） | API Key | https://platform.openai.com/ |
| 6 | LINE Notify API | ─（通知のみ） | HTTP Request ノード | Bearer Token | https://notify-bot.line.me/ |

---

## 6. 常駐自動フロー一覧

| スケジュール | ワークフロー名 | 実行AI | QA AI | 出力先 |
|:---|:---|:---|:---|:---|
| 毎朝 6:00 | [RSC]リサーチ巡回（7ターゲット） | Gemini 2.5 Flash | GPT-5.4 mini | Google Drive + ダッシュボードSection 4 |
| 毎朝 7:00 | 朝ダッシュボード統合ブリーフィング | Gemini 2.5 Flash-Lite | GPT-5.4 mini | Google Drive + LINE通知 |
| 毎夕 19:00 | リフレクション | Gemini 2.5 Flash | GPT-5.4 mini | Google Drive（Dashboard更新）+ LINE通知 |
| 毎週月曜 8:00 | [BizDev]市場スキャン | Gemini Flash + Claude Opus | GPT-5.4 mini | Google Drive + LINE通知 + CEO承認 |
| 毎月1日 9:00 | [FIN]月次開発費集計 | DeepSeek V3.2 | GPT-5.4 mini | Google Drive + CEO承認 |
| 毎月給与日前 | [OPS]給与計算バッチ（全系統） | Python（ローカル） | GPT-5.4 mini | CSV + CEO承認 |
| 毎週日曜 3:00 | n8nワークフロー自動バックアップ | n8n内部API（AIなし） | なし | Google Drive |
| 異常発生時 | アラート通知 | n8nエラーハンドラー（AIなし） | なし | LINE通知（即時） |

**随時起動（CEO指示による）**:

| トリガー | ワークフロー名 | PM AI | 実行AI | QA AI | 出力先 |
|:---|:---|:---|:---|:---|:---|
| CEO手動指示 | [DEV]開発パイプライン | Claude Sonnet/Opus | DeepSeek V3.2 or Cursor通知 | GPT-5.4 mini | GitHub/Google Drive + CEO承認×2 |
| CEO手動指示 | [OPS-共通]社保/雇保書類 | Claude Sonnet/Opus | テンプレート生成+AI補助 | GPT-5.4 mini | PDF/Excel + Drive保存 |
| 必要時のみ | デモ用プロトタイプ | なし | Lovable（n8n外・手動起動） | なし | Lovable上 |

---

## 7. MCP(Model Context Protocol) ツールセキュリティ・最適化ポリシー

システム上限（100個）の回避と、現場での意図せぬデータ破壊や情報漏洩を完全に防ぐため、AIに許可するGoogle Drive MCP等のツール権限を以下の通り厳格に制限（断捨離）する。

### Google Drive MCP 設定基準（ALIGN FIRST ポリシー）

**🚨 絶対に【OFF（無効）】にするツール群（高リスク：破壊・権限変更）**
- **削除系**: `delete_file`, `trash_file`, `delete_folder`（日報やマニュアル等の原本消失防止）
- **共有・権限制限系**: `add_permission`, `remove_permission`, `update_permission`, `share_file`（顧客情報・機密情報の外部漏洩防止）
- **完全上書き系**: `overwrite_file`, `update_file_content`（意図せぬ上書きによるデータ破損防止）

**🟢 常に【ON（有効）】にするツール群（安全：参照・新規作成・追記のみ）**
- **検索・一覧取得系**: `list_files`, `search_files`, `list_folders`（業務情報の速やかな捜索）
- **読み込み系**: `read_file`, `download_file`, `get_file_metadata`（資料の確認と参照）
- **新規作成・追記系**: `create_file`, `create_folder`, `append_to_spreadsheet`, `upload_file`（新規記録への安全なアウトプット）

※ この制限はすべてのMCPサーバー設定に適用され、業務に不要な機能を削ぎ落とすことでAIのエラーを防ぎ、常に稼働ツール総数100個未満の安定環境を維持する。

---

## 8. インフラ構成（v2 更新）

```
CEOのMac（朝・夕のみ使用）
├── Cursor + Claude（メイン対話環境）
├── Claude Cowork（バックアップ環境）
│   └── 同じMCPサーバー（Google Calendar）を共有
├── KENZAIシステム（ローカル実行）★ [OPS-K]で使用
│   ├── payroll_engine.py
│   ├── shift_exporter.py
│   └── OCRエンジン（Vision Framework）
└── timecard_to_csv.py ★ [OPS-A]で使用
    └── Gemini OCRでタイムカード画像→CSV

CEOのWindows PC
├── 給与らくだ ★ [OPS]の最終入力先
├── auto_input.py（pyautogui）★ [OPS-A]の自動入力
└── CSVインポート（Mac → Windows へファイル転送）

VPS（24/365稼働。ConoHa 2GB: 月約1,848円。IP: 133.88.118.185）
├── Ubuntu 24.04 LTS + Docker
├── n8n（オーケストレーション）
├── 各AI APIへの接続（Claude/DeepSeek/GPT/Gemini）
└── GitHub/Google Drive/LINE連携

Supabase 東京リージョン
├── PostgreSQL（プロダクトDB）
├── Auth（認証）
└── Storage（ファイル保管）

Vercel（本番デプロイ）
└── GitHub Push → 自動デプロイ
```

---

## 9. 月間コスト見積り

| 項目 | 月額（税込目安） |
|:---|:---|
| VPS（ConoHa 2GB） | 約1,848円 |
| ドメイン（任意。年額を月割） | 約100円 |
| Claude Sonnet/Opus API | 約3,000〜8,000円 |
| Gemini Flash/Flash-Lite API | 約500〜2,000円 |
| DeepSeek V3.2 API | 約200〜500円 |
| GPT-5.4 mini API（QA専用） | 約1,000〜3,000円 |
| LINE Notify | 0円 |
| Google Workspace（既存） | 既存費用内 |
| 合計 | 約6,700〜15,500円/月 |

---

## 10. 実行ロードマップ（v2 更新）

### Phase 1：即時運用開始（進行中）/ コスト追加 0円

| # | タスク | 状態 |
|:---|:---|:---|
| 1-1 | 新仕様ダッシュボード（Dashboard_20260411.md）を作成 | 着手 |
| 1-2 | Googleカレンダーから今日＋1週間の全予定・全タスクを取得 | 着手 |
| 1-3 | 毎朝Cursor上でAIコーチと朝の儀式を実施 | 運用開始 |
| 1-4 | PM Strategy Report を対話で確定。複数PJ指示を含む | 運用開始 |
| 1-5 | PM→開発→QAをCursor内で手動実行（PJ A, C, D） | 運用開始 |
| 1-6 | 夕方は対話でリフレクション実施 | 運用開始 |
| 1-7 | Claude Coworkをバックアップ環境としてセットアップ | 実施 |
| 1-8 | 運営マニュアル（AIカンパニー運営マニュアル.md）を新アーキテクチャに改訂 | 実施 |
| 1-9 | 2週間の運用で「何を自動化すべきか」を確定 | 評価 |

### Phase 2：n8n + サブエージェント構築 + [OPS]開発完了

| # | タスク | 状態 |
|:---|:---|:---|
| 2-1 | VPSにn8nセットアップ | **完了（IP: 133.88.118.185）** |
| 2-2 | 朝7:00自動ブリーフィング構築 | Week 2で実施予定 |
| 2-3 | 夕19:00自動リフレクション構築 | Week 3で実施予定 |
| 2-4 | 共通サブエージェントテンプレート構築 | Week 4で実施予定 |
| 2-5 | [DEV]パイプライン実装 | Week 4で実施予定 |
| 2-6 | [BizDev]パイプライン実装 | Week 4で実施予定 |
| 2-7 | [RSC]パイプライン実装 | Week 2で実施予定 |
| 2-8 | [FIN]パイプライン実装 | Week 4で実施予定 |
| 2-9 | PM層の自動PJ分解＋並列起動ロジック | Week 4で実施予定 |
| 2-10 | LINE Notify連携 | Week 2で実施予定 |
| 2-11 | [OPS-K] KENZAIエンジン実データ検証・修正 | 開発着手済み → テスト待ち |
| 2-12 | [OPS-C] 設計書再作成 | 未着手 |
| 2-13 | [OPS-C] shift_exporter + OCR + payroll_engine開発 | 設計書完了後に着手 |
| 2-14 | [OPS-A] 信和ミートOCR + 給与らくだ連携完成 | 開発着手済み |

### Phase 3：全パイプライン展開 + 外販準備

| # | タスク | PM AI | 実行AI | QA AI | 時期 |
|:---|:---|:---|:---|:---|:---|
| 3-1 | [MKT]パイプライン実装 | Claude Sonnet | DeepSeek V3.2 | GPT-5.4 mini | 5月中旬 |
| 3-2 | Supabase東京に本番DB構築 | Claude Opus | Cursor + Claude | GPT-5.4 mini | 5月下旬 |
| 3-3 | Dify導入検討（外販プロダクトのAIアプリ層として） | Claude Opus | ─ | ─ | 6月 |
| 3-4 | Webアプリ版ダッシュボード開発（Cursor + Claude → Vercel） | Claude Sonnet | Cursor + Claude | GPT-5.4 mini | 6月〜7月 |
| 3-5 | 外販向けマルチテナント設計 | Claude Opus | Cursor + Claude | GPT-5.4 mini | 7月 |
| 3-6 | MVP施設2〜3社デモ・フィードバック | Claude Opus | Lovable（デモ） | GPT-5.4 mini | 7月〜8月 |

---

## 11. 検証基準（v2 更新）

### Phase 1完了条件

- 朝の儀式が5営業日連続で実施
- 複数PJ指示をCursor内で手動サブエージェント的に処理できている
- Claude Coworkがバックアップとして動作確認済み

### Phase 2完了条件（v1の条件 + OPS追加）

- n8nが朝7:00・夕19:00に5営業日連続エラーなし
- 全パイプラインで「PM → 実行 → QA(GPT-5.4 mini) → CEO承認 → 出力」が例外なく動作
- サブエージェント2つ以上が並列稼働しCEO承認ワンタップで完結
- CEOの実稼働時間3時間以下が週4日以上
- BizDevが毎週月曜に事業機会レポートを自動提出（Gemini Flash → Claude Opus → GPT QA → CEO承認）
- リサーチ巡回7ターゲットが全て自動化済み、かつ結果が朝のダッシュボードSection 4に自動統合
- n8nダウン時のバックアップ運用手順が確立済み
- [OPS-K] 平野工業の出勤簿→CSV生成が全自動で動作（CEOはLINE承認のみ）
- [OPS-C] シフト表→出勤実績OCR→出勤簿→CSV生成の一連フローが動作
- [OPS-A] 信和ミートのタイムカードOCR→データ化→給与らくだ自動入力が動作
- [OPS] 全系統の月次処理時間がv1（全手作業）の50%以下に短縮

### Phase 3完了条件

- 全パイプライン（DEV/BizDev/RSC/FIN/MKT）稼働
- Supabase東京にデータ保管された外販用デモが動作
- MVP施設からフィードバック取得完了

---

## 12. トラブル対応とバックアップ

### n8nがダウンした場合

**即時対応**:
1. VPSにSSH接続: `ssh bunceo@[IP]`
2. Docker状態確認: `docker ps`
3. n8n再起動: `cd ~/n8n-docker && docker compose restart`
4. ログ確認: `docker logs n8n --tail 100`

**復旧しない場合**:
1. Docker Compose再構築: `docker compose down && docker compose up -d`
2. それでもダメならClaudeに状況を共有（エラーログをコピペ）

### n8nデータの自動バックアップ

```
[Cronトリガー: 毎週日曜 3:00 JST]
    │
    ▼
[n8n API] 全ワークフローをJSON形式でエクスポート
    │
    ▼
[Google Drive] backup/n8n_workflows_YYYYMMDD.json として保存
```

### Claude（claude.ai）によるバックアップ運用

n8nが長時間（1時間以上）復旧しない場合:
- 朝の儀式: Claude（claude.ai）でGoogleカレンダーから予定・タスクを取得し、コーチングを実施
- リサーチ巡回: Claude（claude.ai）のWeb検索で手動巡回
- パイプライン: Cursor上で手動PM→実行→QAを実施（Phase 1のフォールバック）

これにより「n8nが落ちても業務は止まらない」体制を維持する。

---

## 付録A: [FIN]と[OPS]の境界

| 項目 | [FIN]の管轄 | [OPS]の管轄 |
|:---|:---|:---|
| 自社の開発費管理 | ○ | × |
| 自社のツール外販の売掛・入金 | ○ | × |
| クライアントの給与計算 | × | ○ |
| クライアントの社保/雇保書類 | × | ○ |
| 給与らくだの操作 | × | ○ |

この境界は厳密に維持する。[FIN]は自社財務、[OPS]はクライアント代行業務。混在させない。

---

## 付録B: [OPS]の設計原則

- **労務計算はAIに任せない**: 給与計算・残業計算・休日判定等の法定計算は、Pythonコードで厳密に実装する。AIの幻覚が許されない領域
- **OCRはAIに任せる**: 手書き文字の読み取りはAI（Vision/Claude/Gemini）の得意領域。3段フォールバックで精度を最大化
- **3系統は統一しない**: 信和ミート/KENZAIグループ/介護施設はそれぞれ入力形式・労務ルール・出力形式が異なる。無理に統一せずパラレルに運用する
- **給与らくだ向けCSVが最終出力**: 全系統の最終ゴールは「給与らくだに取り込めるCSVファイル」の自動生成（OPS-Aはpyautoguiによる直接入力も対応）

---

## 付録C: ダッシュボードの構成（Layer 4 詳細）

Architecture Planで定義されたダッシュボード7セクションの詳細:

```
Section 1: Core Vision
  （CEOの中核ビジョン。変更時のみ対話で修正）

Section 2: Today's Schedule & Tasks（全件）
  データ取得: Google Calendar API（予定 + タスク）

Section 3: 1-Week All（全予定・全タスク）
  データ取得: Google Calendar API（7日分）

Section 4: Research Facts
  データ取得: 6:00に完了したRSC巡回結果を受け取り
  各ターゲットの要約 + 提言 + 詳細ファイルへのリンクを掲載

Section 5: AI Task Workspace（進行中プロジェクト一覧）
  データ取得: Google Drive内のプロジェクト管理ファイル

Section 6: PM Strategy Report（決断の書）
  空欄。朝の対話で確定してパイプラインへ送出

Section 7: Reflection
  空欄。夕19:00のリフレクションで自動記入
```

朝の流れ:
```
06:00 [RSC巡回ワークフロー起動] → 06:50 完了
07:00 [朝ダッシュボード統合ブリーフィング] → QA → LINE通知
  │
  ▼
CEOがダッシュボードを確認 → Cursor/claude.aiでAIコーチと対話
  - Core Visionの復唱と確認
  - タスク優先順位の最終決定
  - Section 6「決断の書」の確定
  - 必要に応じてGoogleカレンダーの修正指示
```

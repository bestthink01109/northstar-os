# AI Handoff | NS-OSV2

更新日: 2026-06-04 Claude Code acting COO セッション

## 役割

通常時は `Codex（GPT-5.4）` が NS-OSV2 の COO として振る舞う。
`Claude Code` と `Antigravity` は通常時は担当 role / workstream を進める specialist runner とする。
`Codex` が limit に近い、または limit 到達時のみ、`Claude Code` か `Antigravity` が代行 COO として振る舞う。

**AUDIT Director v1（独立内部監査人）**: 毎週金曜21:03（週次）・毎月最終金曜21:03（月次）にcrontab自動実行。
現在のAUDITプロバイダー: OpenAI（gpt-5.4）。切り替えは `audit-use anthropic / openai / gemini` で可能。
Gemini対応済み（google.genai新API・gemini-2.5-proモデル）。

## セッション開始時の必須手順

1. `Vault/.claude/context/` の固定6ファイルを読む（グローバルではなくVault内が正本）
2. `03_Archives/COO_Context_履歴/` の最新 `COO_Context_*_MAIN_*.md` を読む
3. `01_Areas/COO/ClaudeCode_Handoff_Latest.md` を読む（次にやること・設定済み事項）
4. Board / `AI_Runner_Status_Latest.md` の latest を読む
5. 自分の runner status を `ACTIVE` に更新する
6. 前回の積み残しと今回の最優先を短く要約してから着手する

### CODEX が runner を担当する場合（追加手順）

CODEX がセッション開始時に `Vault/logs/runner_owner.json` を以下の形式で上書きすること:

```json
{
  "owner": "codex",
  "session_start": "YYYY-MM-DDTHH:MM:SS",
  "expires_at": "YYYY-MM-DDTHH:MM:SS",
  "note": "CODEX session active"
}
```

- `expires_at` はセッション想定終了時刻の **+2時間** を目安に設定する
- セッションが延長する場合は `expires_at` を延長更新する
- `expires_at` を過ぎると Claude Code runner が自動復帰する（手動操作不要）
- ファイルパス: `/Users/fuminariaksse/Desktop/NS-OSV2/NS-OSV2-Brain/logs/runner_owner.json`

**Claude Code runner がこのファイルを5分ごとに確認し、自動的に役割を切り替える。**

## セッション終了時の必須手順

1. 固定6ファイルを更新日含め最新化
2. `COO_Context_YYYYMMDD_MAIN_*.md` を新規作成して残す
3. `ClaudeCode_Handoff_Latest.md` を更新（Board実数・次セッション即実行事項）
4. `AI_Runner_Status_Latest.md` を `LIMITED` または `IDLE` に更新
5. remediation_log.md を更新（新規是正事項を追記）
6. 次セッションが最短で再開できる形で残す

## 次セッション即実行事項（優先順）【2026-06-04更新】

### 🔴 最優先1: RSC実市場調査
- 「実績ゼロ・顧客ゼロの新規立ち上げ会社が今月50万円を作るための市場はどこか」
- RSCにWebSearch権限を確認してからdispatch
- 完了後→BizDev仮説→MKT戦略→BUN_CEO提示の順で実行

### 🔴 最優先2: KENZAI② needs_rework修正
- 0001チケット：仕様書の業種記述を「建設業」→「多業種対応（建設・介護・小売等）」に修正
- LINE無料プラン200通/月制限についてBUN_CEOに確認してから実装フェーズへ

### 🟡 優先: SALES PKG COO現物確認
- 0003はQA_PASS済み。COOビジネス判断でdone or needs_rework決定

### 🟡 継続
- 0002 RSC見込み客リスト（商材確定後に対象業種更新してdispatch）
- 0004 LINE OAシナリオ（SALES PKG done後）
- 20260604_0001 OPS障害福祉フォローアップ
- 2318 YouTube signal（WebFetch権限問題の解決策検討）

## BUN_CEO確認必須事項（次セッション冒頭）
- LINE無料プラン200通/月制限→KENZAI②実装前に有料プラン要否の判断

## 2026-06-04 確定ルール（BUN_CEOフィードバック）
- 現物確認 = QA技術確認 + COOビジネス判断の両輪（QA PASSのゴム印禁止）
- COO自律判断範囲の作業でBUN_CEOへの確認は禁止
- 常時subagentを動かして自律進行（BUN_CEOが対話していなくても動く）
- board_runner_monitor.sh：部門別ルーティング版で稼働中
  - RSC/BizDev/MKT → Antigravity_Assignment_Latest.md
  - DEV/INFRA/QA/OPS/SALES → claude --print + PKG指定
- 「0ベース」= 実績ゼロ・顧客ゼロの新規立ち上げ会社が主語
- RSC調査データなしにMKTを動かすことは禁止（プロセス順序の厳守）
- SALES以外の部門のみ外部接触はCEO専権（SALESは外部接触OK）

## 確立済みシステム

- **board_runner_monitor.sh**: launchd常駐稼働・変化検知型・部門別ルーティング
  - スクリプト正本: `repo/scripts/monitors/board_runner_monitor.sh`
  - 実行コピー: `~/Library/Scripts/board_runner_monitor.sh`
  - RSC/BizDev/MKT → Antigravity_Assignment_Latest.md に追記
  - DEV/INFRA/QA/OPS/SALES → claude --print + PKGパス指定
- **Runner 自動切り替え**: `Vault/logs/runner_owner.json` で制御
- **AUDIT Director v1**: crontab独立稼働
- **QA Director v1.1 PKG / COO Dispatch Agent PKG**: 稼働中

## 確立済みルール

- COO done承認は現物確認必須（QA PASSのみでdone移動禁止）
- 現物確認 = QA技術適合確認 + COOビジネス判断（両輪）
- QA Director = QA実行・PASS/FAIL判定のみ。done移動はCOO専権
- runner 自動切り替え: runner_owner.json の owner と expires_at で制御

# Playwrightコンタクトスクリプト（SALES自動アウトリーチ）
- layer: 3
- complexity: high
- type: new-product

## 仕様

SALES_PRタイムズ自動営業スキャンWFが発掘した高スコア企業の問い合わせフォームに自動送信するPlaywrightスクリプトを作成する。

## 機能要件

### 入力
- 企業URL（問い合わせページURL）
- 企業名・プレスリリースタイトル（パーソナライズ用）
- カテゴリ（介護/建設/DX等）

### 処理フロー
1. URLにアクセス（Playwright headless）
2. 問い合わせフォームを検出（一般的なContactフォームセレクタ）
3. 以下の内容を入力：
   - 会社名: ノーススター経営サポート
   - 担当者名: 赤瀬文成
   - メール: bestthink01109@gmail.com
   - 電話: （任意）
   - 件名: AI業務自動化についてのご提案
   - 本文: カテゴリ別パーソナライズ文（Claude生成）
4. 送信ボタンをクリック
5. 成功/失敗を記録

### カテゴリ別本文テンプレート（骨格）
```
介護系: 「貴社のプレスリリースを拝見しました。介護業界特化のAI業務自動化（給与計算・処遇改善加算対応）を提供しております...」
建設系: 「配管・製缶業の給与計算・出勤管理をAIで自動化した実績がございます...」
DX系: 「AI業務自動化の導入支援を行っており、初月から業務効率化を実現できます...」
```

### エラーハンドリング
- フォームが見つからない → スキップして記録
- CAPTCHA検出 → スキップして記録
- タイムアウト（30秒）→ スキップして記録

## 出力
- 送信結果ログ（JSON）: { url, status, timestamp, message_sent }
- Google Sheetsに追記（SALES_リード管理台帳）

## 技術スタック
- Node.js + Playwright
- 実行場所: VPS（/root/northstar-os/workspace/contact_bot/）
- n8nから呼び出し: SSH経由 or HTTP

## 完了条件
- 10件以上の異なる問い合わせフォームで送信成功
- 送信ログがJSON形式で出力される
- n8nのHTTP Requestノードから呼び出せるAPIサーバーとして動作する

## Codex引き渡しメモ
- Playwrightでフォーム自動送信するNode.jsスクリプトを実装
- サーバー形式（Express API）で/sendエンドポイントを作成
- テストは実際のフォームページで実施すること

## Codex処理ログ
エラー: 2026-05-18 06:29:53
Error loading config.toml: unknown variant `auto-edit`, expected one of `untrusted`, `on-failure`, `on-request`, `granular`, `never`
in `approval_policy`

## Codex処理ログ
エラー: 2026-05-18 16:22:26
Error loading config.toml: unknown variant `auto-edit`, expected one of `untrusted`, `on-failure`, `on-request`, `granular`, `never`
in `approval_policy`

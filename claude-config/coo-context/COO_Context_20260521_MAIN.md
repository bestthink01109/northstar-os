# COO Context | 2026-05-21 MAIN（セッション終了版）

## 本セッションの主な完了事項

### MKT/SALES WF完全修正
- MKT_PRタイムズ: data[0].items対応・Drive2ステップ・jsonBody統一完了
- SALES_PRタイムズ: 同様修正・稼働確認済み
- System QA: $('sq-token')参照エラー修正
- DEV QA: specifyBody:json追加

### n8n TZ=Asia/Tokyo確定（重要）
- cronは全てJST値で設定（UTC計算不要）
- MKT_PR 30 5/SALES_PR 45 5/RSC 0 6/SALES日次 30 6/全社ボード 50 6/朝7:00

### LINE設計完成
- 全12WF onError:continueRegularOutput設定済み
- エラーアラート5分重複チェック追加
- 月次200通：朝夕ブリーフィング+エラーのみ

### 冗長化体制確立
- GitHub: WF定義(backups/n8n/)・context・VPSスクリプト・knowledge
- VPS: SQLite日次(daily_backup.sh 3:30 JST)

### ナレッジ体系
- dev/templates/reports/ Type A~D登録
- knowledge/ パターン・決定事項・OAuth仕様

## 積み残し
- OPS純青 Python実装（最優先）
- LINE月次上限（6/1自動回復）
- MKT/SALES_PR明朝定時実行確認
- Instagram/note展開（アカウント作成後）

## 技術メモ
- OAuth参照: $('OAuthトークン取得').item.json.access_token（名前で参照）
- n8n TZ=Asia/Tokyo → JSTでcron設定
- continueRegularOutput → LINE失敗でもWF継続

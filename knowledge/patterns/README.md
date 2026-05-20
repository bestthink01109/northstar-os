# patterns/ — 問題解決パターン一覧

> 作業中に発見した再利用可能な問題解決パターンをカテゴリ別に管理する。
> 新しいパターンを発見したら即座にここへ登録すること。

---

## カテゴリ一覧

| カテゴリ | パス | 登録数 | 最終更新 |
|---------|-----|--------|---------|
| n8n | [patterns/n8n/](n8n/README.md) | 4 | 2026-05-20 |
| API連携 | [patterns/api/](api/README.md) | 0 | 2026-05-20 |
| OPS業務 | [patterns/ops/](ops/README.md) | 0 | 2026-05-20 |

---

## 登録ルール

### パターン登録フォーマット

```markdown
## P-[連番]: パターン名

- **カテゴリ**: n8n / api / ops
- **症状**: （何が起きたか・どんなエラーが出たか）
- **原因**: （なぜ起きたか・根本原因）
- **解決策**: （どう直したか・コード例を含む）
- **確認日**: YYYY-MM-DD
- **参照**: （関連WF・チケット・PRなど）
- **登場回数**: 1
```

### 重複が発生した場合

同じパターンが再度登場したら既存エントリの `登場回数` を +1 する。
3回以上になったら `skills/README.md` にスキル候補として昇格させる。

---

## クイックリファレンス

### n8n
- [P-001] HTTP Request v4 JSON Body設定エラー → [n8n/README.md](n8n/README.md#p-001-http-request-v4-json-body設定エラー)
- [P-002] Aggregateノードの出力構造 → [n8n/README.md](n8n/README.md#p-002-aggregateノードの出力構造)
- [P-003] Drive multipartアップロード → [n8n/README.md](n8n/README.md#p-003-drive-multipartアップロード)
- [P-004] LINE monthly limit対応 → [n8n/README.md](n8n/README.md#p-004-line-monthly-limit対応)

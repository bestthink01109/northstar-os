# DEV 3層設計仕様書
# COOより 2026-05-17 確定・緊急共有

## ⚠️ GitHub連携構築前に必ず読むこと

DEVの処理フローは3層設計で確定。
Codexのチケット自動取得はこの設計を前提に構築すること。

---

## 3層設計（確定）

```
DEVチケット受信
        ↓
【Layer 1】テンプレートマッチング（コスト0・約80%）
  既存テンプレートで対応可能？
  → YES: テンプレート適用 → DeepSeek QA → Deploy → 完了
  → NO : Layer 2へ

【Layer 2】Claude API + 差分生成（安価・約15%）
  Claude APIで「差分のみ」生成（全体は作らない）
  → DeepSeek QA → Deploy → 完了
  → FAIL: Layer 3へ

【Layer 3】Claude Code + Codex CLI（高品質・約5%）
  ← Codexが担当するのはここのみ
  Claude Code DEV Agentがコード作成
  → tickets/waiting/ に配置
  → Codex Watcherが自動取得・デバッグ
  → DeepSeek QA → Deploy → 完了
```

---

## Codexの担当範囲

```
Layer 1: Codex不要
Layer 2: Codex不要
Layer 3: Codex必須 ← ここだけ
```

---

## チケットファイルの推奨フォーマット

```markdown
# チケット名
- layer: auto  # auto=自動判定 / 1 / 2 / 3
- complexity: low / medium / high
- type: n8n-wf / python / gas / client-bot / new-product
```

`layer: auto` の場合はCOOまたはn8nが複雑度を判定してLayerを決定する。

---

## テンプレートの有効範囲

| アプリ種別 | テンプレート活用 | 主な層 |
|-----------|--------------|--------|
| n8n WF（社内） | 高い | Layer 1-2 |
| Python（骨格） | 中 | Layer 2-3 |
| GAS操作 | 中 | Layer 2-3 |
| クライアント固有BOT | 低い | Layer 3のみ |
| 新規プロダクト | 低い | Layer 3のみ |

---

## コスト上限
月¥10,000 / 最大3回イテレーション / タイムアウト10分

## 完了後
COOに「Layer対応のGitHub連携完了」として報告すること。

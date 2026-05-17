# DEV チケット管理

## フロー
```
COO(Mac) → todo/ にcommit&push
    ↓ VPS git pull(60秒ポーリング)
DEV Agent(Claude Code) → doing/ → waiting/
    ↓
Codex Watcher → done/ → git push
```

## フォルダ
| フォルダ | 説明 | 操作者 |
|---------|------|--------|
| `todo/` | 未着手チケット | COO が作成 |
| `doing/` | DEV Agent処理中 | DEV Agent が移動 |
| `waiting/` | Codexデバッグ待ち | DEV Agent が移動 |
| `done/` | 完了済み | Codex が移動・push |

## チケット命名規則
```
YYYYMMDD_HHMM_[部門]_[タスク名].md
例: 20260517_2200_DEV_純青OCRパーサー実装.md
```

#!/usr/bin/env python3
"""
L3 DEV Agent - Claude APIを使ってチケットの実装コードを生成する
完了時にType Bレポート形式でチケットファイルに追記する

使い方: python3 l3_agent.py <チケットファイルパス>
"""

import sys
import os
import re
from datetime import datetime
import anthropic

REPO_DIR = "/root/northstar-os"
DONE_DIR = os.path.join(REPO_DIR, "tickets/done")


def load_ticket(ticket_path: str) -> str:
    with open(ticket_path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(ticket_content: str) -> str:
    return f"""以下のチケットに従って、実装コードまたは設定ファイルを生成してください。

# チケット内容
{ticket_content}

# 指示
- 既存の構造を壊さず、変更・追加が必要な部分のみ出力してください。
- 各ファイルは以下の形式で出力してください:

## ファイル: <ファイルパス>
```<言語>
<コード内容>
```

- 実装方針や補足がある場合は最後に「### 実装メモ」セクションを追加してください。
"""


def call_claude_api(prompt: str) -> tuple[str, list[tuple[str, str]]]:
    """Claude APIを呼び出して実装を生成する。
    Returns: (full_response_text, [(filepath, content), ...])
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY が設定されていません")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text

    # ファイルブロックを抽出: "## ファイル: <path>" の後のコードブロック
    files: list[tuple[str, str]] = []
    pattern = re.compile(
        r"## ファイル:\s*(.+?)\n```[^\n]*\n(.*?)```",
        re.DOTALL,
    )
    for match in pattern.finditer(response_text):
        filepath = match.group(1).strip()
        content = match.group(2)
        files.append((filepath, content))

    return response_text, files


def write_generated_files(files: list[tuple[str, str]]) -> None:
    """生成されたファイルをリポジトリに書き出す"""
    for filepath, content in files:
        # 絶対パスでなければ REPO_DIR 配下に置く
        if not filepath.startswith("/"):
            filepath = os.path.join(REPO_DIR, filepath)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[L3] 生成: {filepath}")


def append_type_b_report(
    ticket_path: str,
    ticket_name: str,
    response_text: str,
    files: list[tuple[str, str]],
) -> None:
    """Type Bレポートをチケットファイルに追記する"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_list = "\n".join(f"- {fp}" for fp, _ in files) if files else "（ファイル生成なし）"

    report = f"""
## DEV_レポート（Type B）
- 完了日時: {now} JST
- Layer: L3
- 担当AI: Claude Sonnet（l3_agent.py）

### 実装概要
- 目的: {ticket_name}
- 生成ファイル数: {len(files)}

### 生成ファイル
{file_list}

### 実装詳細
{response_text}

### スキル化候補
（次のCOOセッションで評価）

### 完了確認
- [x] 実装完了
- [ ] 本番環境テスト（要手動確認）
"""

    with open(ticket_path, "a", encoding="utf-8") as f:
        f.write(report)

    print(f"[L3] Type Bレポート追記完了: {ticket_name}")


def run_l3_agent(ticket_path: str) -> int:
    """L3エージェントのメイン処理。終了コードを返す。"""
    if not os.path.isfile(ticket_path):
        print(f"[L3] エラー: チケットが見つかりません: {ticket_path}", file=sys.stderr)
        return 1

    ticket_name = os.path.basename(ticket_path)
    print(f"[L3] 処理開始: {ticket_name}")

    try:
        ticket_content = load_ticket(ticket_path)
        prompt = build_prompt(ticket_content)
        response_text, files = call_claude_api(prompt)

        if files:
            write_generated_files(files)
        else:
            print("[L3] 生成ファイルなし（実装メモのみ）")

        append_type_b_report(ticket_path, ticket_name, response_text, files)
        print(f"[L3] 完了: {ticket_name} (生成ファイル数: {len(files)})")
        return 0

    except EnvironmentError as e:
        print(f"[L3] 環境エラー: {e}", file=sys.stderr)
        return 2
    except anthropic.APIError as e:
        print(f"[L3] Claude APIエラー: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"[L3] 予期しないエラー: {e}", file=sys.stderr)
        return 99


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"使い方: {sys.argv[0]} <チケットファイルパス>", file=sys.stderr)
        sys.exit(1)

    exit_code = run_l3_agent(sys.argv[1])
    sys.exit(exit_code)

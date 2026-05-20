#!/usr/bin/env python3
"""
MKT_PRタイムズ Drive成果物保存 multipart修正スクリプト
WF ID: ht60IBCItF9vt1vO

根本原因:
  n8n HTTP Request v4 の specifyBody="string" が charset=UTF-8 の "=" でボディを
  key=value分割してしまい、Google DriveにJSONオブジェクトとして送信される。

修正方法: 方法A（2ステップアップロード）
  Step1: POST /drive/v3/files でメタデータのみ作成 → fileId取得
  Step2: PATCH /upload/drive/v3/files/{fileId}?uploadType=media でコンテンツをアップロード
"""

import json
import sys
import os
import subprocess
import urllib.request
import urllib.error
import urllib.parse
from typing import Any


# ──────────────────────────────────────────────
# 設定
# ──────────────────────────────────────────────
N8N_BASE_URL = "http://162.43.78.67:5678"
WF_ID = "ht60IBCItF9vt1vO"
DRIVE_FOLDER_ID = "1I_68Pimq8jKjq6xfPMAeD22oeAHc8mTf"
OAUTH_WEBHOOK_URL = "http://localhost:5678/webhook/google-oauth-token"


def get_api_key() -> str:
    """
    /root/n8n-api.sh から APIキーを取得する。
    ローカル実行時は環境変数 N8N_API_KEY があればそちらを優先。
    """
    if os.environ.get("N8N_API_KEY"):
        return os.environ["N8N_API_KEY"].strip()

    api_sh = "/root/n8n-api.sh"
    if not os.path.exists(api_sh):
        raise FileNotFoundError(
            f"{api_sh} が見つかりません。環境変数 N8N_API_KEY を設定するか、"
            "VPS上で実行してください。"
        )

    result = subprocess.run(
        ["bash", "-c", f"source {api_sh} && echo $N8N_API_KEY"],
        capture_output=True, text=True, timeout=10
    )
    key = result.stdout.strip()
    if not key:
        # ファイルを直接パースして KEY= の行を探す
        with open(api_sh, "r") as f:
            for line in f:
                line = line.strip()
                if "N8N_API_KEY" in line and "=" in line:
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        raise ValueError(f"{api_sh} から APIキーを取得できませんでした。")
    return key


def n8n_request(method: str, path: str, api_key: str, body: Any = None) -> Any:
    """n8n REST APIへのリクエストを送信する。"""
    url = f"{N8N_BASE_URL}/api/v1{path}"
    headers = {
        "X-N8N-API-KEY": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"HTTP {e.code} {e.reason} [{method} {url}]\n{error_body}"
        ) from e


def get_workflow(api_key: str) -> dict:
    """WF定義を取得する。"""
    print(f"[INFO] WF取得中: {WF_ID}")
    return n8n_request("GET", f"/workflows/{WF_ID}", api_key)


def find_drive_save_node(wf: dict) -> tuple[int, dict]:
    """
    'Drive成果物保存' ノードを検索して (index, node_dict) を返す。
    見つからない場合は ValueError を raise する。
    """
    nodes: list = wf.get("nodes", [])
    for i, node in enumerate(nodes):
        name: str = node.get("name", "")
        if "Drive" in name and ("保存" in name or "save" in name.lower() or "upload" in name.lower()):
            print(f"[INFO] 対象ノード発見: '{name}' (index={i})")
            return i, node
    # フォールバック: HTTP Requestかつ drive.google.com を含む
    for i, node in enumerate(nodes):
        url_val = (
            node.get("parameters", {}).get("url", "") or
            node.get("parameters", {}).get("requestUrl", "")
        )
        if "drive.google.com" in str(url_val) or "googleapis.com/upload/drive" in str(url_val):
            print(f"[INFO] URLで対象ノード発見: '{node.get('name')}' (index={i})")
            return i, node
    raise ValueError(
        "Drive成果物保存ノードが見つかりませんでした。ノード一覧:\n" +
        "\n".join(f"  [{i}] {n.get('name')}" for i, n in enumerate(nodes))
    )


def find_node_by_name(wf: dict, name: str) -> tuple[int, dict] | tuple[None, None]:
    """名前でノードを検索する。"""
    for i, node in enumerate(wf.get("nodes", [])):
        if node.get("name") == name:
            return i, node
    return None, None


def get_oauth_token_node_template() -> dict:
    """
    OAuthトークン取得ノードのテンプレートを返す。
    共通WFのwebhookから access_token を取得する HTTP Request ノード。
    """
    return {
        "name": "OAuthトークン取得",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4,
        "position": [0, 0],  # 後で座標を調整する
        "parameters": {
            "method": "GET",
            "url": OAUTH_WEBHOOK_URL,
            "authentication": "none",
            "options": {},
            "responseFormat": "json",
        },
    }


def build_drive_metadata_create_node(original_node: dict) -> dict:
    """
    Step1: Drive メタデータ作成ノード。
    POST /drive/v3/files でファイルメタデータのみを作成し fileId を取得する。
    アクセストークンは前段の OAuthトークン取得ノードから参照する。
    """
    pos = original_node.get("position", [600, 300])
    return {
        "name": "Drive_メタデータ作成",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4,
        "position": [pos[0], pos[1]],
        "parameters": {
            "method": "POST",
            "url": "https://www.googleapis.com/drive/v3/files",
            "authentication": "none",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Authorization",
                        "value": "=Bearer {{ $('OAuthトークン取得').item.json.access_token }}",
                    },
                    {
                        "name": "Content-Type",
                        "value": "application/json",
                    },
                ]
            },
            "sendBody": True,
            "contentType": "raw",
            "rawContentType": "application/json",
            "body": (
                '={"name": "MKT_PR\u30bf\u30a4\u30e0\u30ba_'
                '{{ $now.format(\'yyyyMMdd\') }}.md",'
                f'"parents": ["{DRIVE_FOLDER_ID}"],'
                '"mimeType": "text/plain"}'
            ),
            "options": {
                "response": {
                    "response": {
                        "responseFormat": "json",
                    }
                }
            },
        },
    }


def build_drive_content_upload_node(original_node: dict) -> dict:
    """
    Step2: Drive コンテンツアップロードノード。
    PATCH /upload/drive/v3/files/{fileId}?uploadType=media でコンテンツをアップロードする。
    fileId は Step1 のレスポンスから取得する。
    ファイルコンテンツは元の Drive成果物保存ノードが参照していた式をそのまま使う。
    """
    pos = original_node.get("position", [600, 300])

    # 元ノードからコンテンツの参照先を抽出する
    original_params = original_node.get("parameters", {})
    # body / rawBody / bodyParameters の順で探す
    content_expr = (
        original_params.get("body")
        or original_params.get("rawBody")
        or _extract_body_from_params(original_params)
        or "={{ $json.content }}"
    )

    # multipartのJSONパートが含まれている場合は純粋なコンテンツ式を抽出する
    content_expr = _extract_content_from_multipart(content_expr)

    return {
        "name": "Drive_コンテンツアップロード",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4,
        "position": [pos[0] + 250, pos[1]],
        "parameters": {
            "method": "PATCH",
            "url": "={{ 'https://www.googleapis.com/upload/drive/v3/files/' + $('Drive_メタデータ作成').item.json.id + '?uploadType=media' }}",
            "authentication": "none",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Authorization",
                        "value": "=Bearer {{ $('OAuthトークン取得').item.json.access_token }}",
                    },
                    {
                        "name": "Content-Type",
                        "value": "text/plain; charset=UTF-8",
                    },
                ]
            },
            "sendBody": True,
            "contentType": "raw",
            "rawContentType": "text/plain; charset=UTF-8",
            "body": content_expr,
            "options": {
                "response": {
                    "response": {
                        "responseFormat": "json",
                    }
                }
            },
        },
    }


def _extract_body_from_params(params: dict) -> str:
    """bodyParameters から内容を抽出する試み。"""
    body_params = params.get("bodyParameters", {}).get("parameters", [])
    for p in body_params:
        if p.get("name") in ("", "body", "content"):
            return p.get("value", "")
    return ""


def _extract_content_from_multipart(expr: str) -> str:
    """
    multipartボディ文字列からコンテンツ部分（2番目のパート）を抽出する。
    抽出できない場合は元の式をそのまま返す。
    """
    if not expr:
        return "={{ $json.content }}"

    # n8n式 (={{ ... }}) かどうかチェック
    if "boundary" not in expr.lower() and "Content-Type" not in expr:
        return expr

    # multipartっぽい場合: --boundary で分割して2番目のパートのボディ部分を取得
    try:
        lines = expr.replace("\\r\\n", "\n").replace("\r\n", "\n").split("\n")
        boundary_line = lines[0].strip() if lines else ""
        if not boundary_line.startswith("--"):
            return expr

        # パートを分割
        parts = []
        current_part: list[str] = []
        for line in lines[1:]:
            if line.strip().startswith("--"):
                if current_part:
                    parts.append(current_part)
                current_part = []
            else:
                current_part.append(line)
        if current_part:
            parts.append(current_part)

        if len(parts) >= 2:
            # 2番目のパート（コンテンツ部分）のヘッダーをスキップして本文を取得
            content_part = parts[1]
            body_started = False
            body_lines = []
            for line in content_part:
                if not body_started:
                    if line.strip() == "":
                        body_started = True
                else:
                    body_lines.append(line)
            content = "\n".join(body_lines).strip()
            if content:
                return content
    except Exception:
        pass

    return expr


def build_connections_patch(wf: dict, drive_node_name: str) -> dict:
    """
    元の Drive成果物保存ノードへの接続を新しい2ステップノードに置き換える。
    接続マップ全体を返す。
    """
    connections: dict = wf.get("connections", {})
    new_connections: dict = {}

    for src_name, src_conns in connections.items():
        new_connections[src_name] = {}
        for conn_type, conn_list in src_conns.items():
            new_connections[src_name][conn_type] = []
            for output_conns in conn_list:
                new_output = []
                for conn in output_conns:
                    if conn.get("node") == drive_node_name:
                        # OAuthトークン取得ノードへの接続に変更
                        new_output.append({
                            "node": "OAuthトークン取得",
                            "type": conn.get("type", "main"),
                            "index": conn.get("index", 0),
                        })
                    else:
                        new_output.append(conn)
                new_connections[src_name][conn_type].append(new_output)

    # OAuthトークン取得 → Drive_メタデータ作成
    new_connections["OAuthトークン取得"] = {
        "main": [[{"node": "Drive_メタデータ作成", "type": "main", "index": 0}]]
    }
    # Drive_メタデータ作成 → Drive_コンテンツアップロード
    new_connections["Drive_メタデータ作成"] = {
        "main": [[{"node": "Drive_コンテンツアップロード", "type": "main", "index": 0}]]
    }

    # 元の Drive成果物保存からの接続を Drive_コンテンツアップロードに移す
    if drive_node_name in connections:
        new_connections["Drive_コンテンツアップロード"] = connections[drive_node_name]

    return new_connections


def adjust_positions(new_nodes: list[dict], reference_node: dict) -> None:
    """新規ノードの位置を調整する。"""
    ref_pos = reference_node.get("position", [600, 300])
    # OAuthトークン取得: 元ノードより左
    for node in new_nodes:
        if node["name"] == "OAuthトークン取得":
            node["position"] = [ref_pos[0] - 250, ref_pos[1]]
        elif node["name"] == "Drive_メタデータ作成":
            node["position"] = [ref_pos[0], ref_pos[1]]
        elif node["name"] == "Drive_コンテンツアップロード":
            node["position"] = [ref_pos[0] + 250, ref_pos[1]]


def apply_fix(wf: dict) -> dict:
    """
    WF定義に修正を適用して新しい定義を返す。
    - Drive成果物保存ノードを削除
    - OAuthトークン取得 / Drive_メタデータ作成 / Drive_コンテンツアップロード を追加
    - connections を更新
    """
    nodes: list = wf.get("nodes", [])

    # 対象ノード検索
    drive_idx, drive_node = find_drive_save_node(wf)
    drive_node_name: str = drive_node.get("name", "Drive成果物保存")

    # 既存の置換済みノードを削除（冪等性のため）
    nodes = [
        n for n in nodes
        if n.get("name") not in {
            drive_node_name,
            "OAuthトークン取得",
            "Drive_メタデータ作成",
            "Drive_コンテンツアップロード",
        }
    ]

    # 新ノードを構築
    oauth_node = get_oauth_token_node_template()
    meta_node = build_drive_metadata_create_node(drive_node)
    upload_node = build_drive_content_upload_node(drive_node)

    new_nodes = [oauth_node, meta_node, upload_node]
    adjust_positions(new_nodes, drive_node)

    nodes.extend(new_nodes)
    wf["nodes"] = nodes

    # 接続を更新
    wf["connections"] = build_connections_patch(wf, drive_node_name)

    # active フラグをそのまま保持（PUTするとfalseになる場合があるため）
    if "active" not in wf:
        wf["active"] = False

    return wf


def update_workflow(api_key: str, wf: dict) -> dict:
    """WF定義をn8n APIでPUTして更新する。"""
    wf_id = wf["id"]
    print(f"[INFO] WF更新中: {wf_id}")

    # PUT /workflows/{id}
    result = n8n_request("PUT", f"/workflows/{wf_id}", api_key, wf)
    print(f"[INFO] WF更新完了: active={result.get('active')}")
    return result


def activate_workflow(api_key: str, wf_id: str) -> None:
    """WFをアクティブ化する。"""
    try:
        n8n_request("POST", f"/workflows/{wf_id}/activate", api_key)
        print(f"[INFO] WF アクティブ化完了: {wf_id}")
    except Exception as e:
        print(f"[WARN] WF アクティブ化でエラー (既にactiveの可能性): {e}")


def validate_fix(wf: dict) -> None:
    """
    修正後のWF定義を検証する。
    期待するノードが存在し、Drive成果物保存ノードが削除されていることを確認する。
    """
    nodes = wf.get("nodes", [])
    node_names = {n.get("name") for n in nodes}

    required = {"OAuthトークン取得", "Drive_メタデータ作成", "Drive_コンテンツアップロード"}
    missing = required - node_names
    if missing:
        raise ValueError(f"[ERROR] 必要なノードが不足しています: {missing}")

    connections = wf.get("connections", {})

    # OAuthトークン取得 → Drive_メタデータ作成 の接続確認
    oauth_conns = connections.get("OAuthトークン取得", {}).get("main", [[]])
    oauth_targets = {c.get("node") for conns in oauth_conns for c in conns}
    if "Drive_メタデータ作成" not in oauth_targets:
        raise ValueError(
            "[ERROR] OAuthトークン取得 → Drive_メタデータ作成 の接続がありません"
        )

    # Drive_メタデータ作成 → Drive_コンテンツアップロード の接続確認
    meta_conns = connections.get("Drive_メタデータ作成", {}).get("main", [[]])
    meta_targets = {c.get("node") for conns in meta_conns for c in conns}
    if "Drive_コンテンツアップロード" not in meta_targets:
        raise ValueError(
            "[ERROR] Drive_メタデータ作成 → Drive_コンテンツアップロード の接続がありません"
        )

    print("[INFO] 検証OK: すべての必要ノードと接続が存在します")


def print_summary(wf: dict) -> None:
    """修正後のWF概要を出力する。"""
    nodes = wf.get("nodes", [])
    print("\n" + "=" * 60)
    print("修正後のWFノード一覧:")
    print("=" * 60)
    for node in nodes:
        marker = "★" if node.get("name") in {
            "OAuthトークン取得", "Drive_メタデータ作成", "Drive_コンテンツアップロード"
        } else " "
        print(f"  {marker} [{node.get('type', 'unknown')}] {node.get('name')}")
    print("=" * 60)

    print("\n接続フロー（Drive関連）:")
    connections = wf.get("connections", {})
    for src in ["OAuthトークン取得", "Drive_メタデータ作成", "Drive_コンテンツアップロード"]:
        if src in connections:
            for conn_type, conn_list in connections[src].items():
                for conns in conn_list:
                    for c in conns:
                        print(f"  {src} → {c.get('node')}")


def main() -> int:
    """メイン処理。"""
    print("=" * 60)
    print("MKT_PRタイムズ Drive成果物保存 multipart修正スクリプト")
    print("=" * 60)

    try:
        # APIキー取得
        api_key = get_api_key()
        print(f"[INFO] APIキー取得完了: {api_key[:8]}...")

        # WF取得
        wf = get_workflow(api_key)
        print(f"[INFO] WF取得完了: '{wf.get('name')}' (nodes={len(wf.get('nodes', []))})")

        # 修正適用
        print("[INFO] 修正を適用中...")
        fixed_wf = apply_fix(wf)

        # 検証
        validate_fix(fixed_wf)

        # 概要表示
        print_summary(fixed_wf)

        # WF更新
        updated = update_workflow(api_key, fixed_wf)

        # 必要に応じてアクティブ化
        if updated.get("active") is False and wf.get("active") is True:
            activate_workflow(api_key, WF_ID)

        print("\n[SUCCESS] WFの修正が完了しました！")
        print(f"  WF ID: {WF_ID}")
        print(f"  n8n UI: {N8N_BASE_URL}/workflow/{WF_ID}")
        print("\n次のコマンドでテスト実行してください:")
        print(
            "  curl -X POST http://162.43.78.67:5678/webhook/mkt-scan-backup \\\n"
            "    -H 'Content-Type: application/json' -d '{}'"
        )
        return 0

    except FileNotFoundError as e:
        print(f"[ERROR] ファイルが見つかりません: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"[ERROR] 値エラー: {e}", file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(f"[ERROR] API呼び出しエラー: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"[ERROR] 予期しないエラー: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 99


if __name__ == "__main__":
    sys.exit(main())
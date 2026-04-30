#!/usr/bin/env python3
"""
AIシフト自動作成ツール - メインスクリプト
介護・福祉施設向けシフト表を自動生成する。

使用方法:
    python3 main.py --config configs/shift_config_202603.yaml --output output.xlsx
    python3 main.py --config configs/shift_config_202603.yaml --output output.xlsx --time-limit 120
"""

import argparse
import sys
import os
import time

# 同じディレクトリのモジュールをインポート
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shift_solver import create_shift
from shift_exporter import export_to_excel


def main():
    parser = argparse.ArgumentParser(
        description='AIシフト自動作成ツール - 介護・福祉施設向け'
    )
    parser.add_argument(
        '--config', '-c',
        required=True,
        help='施設設定ファイルのパス（YAML形式）'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='出力Excelファイルのパス'
    )
    parser.add_argument(
        '--time-limit', '-t',
        type=int,
        default=60,
        help='ソルバーの制限時間（秒）。デフォルト: 60秒'
    )

    args = parser.parse_args()

    # 設定ファイルの存在確認
    if not os.path.exists(args.config):
        print(f"エラー: 設定ファイルが見つかりません: {args.config}")
        sys.exit(1)

    print("=" * 60)
    print("  AIシフト自動作成ツール")
    print("  kanou経営サポート")
    print("=" * 60)
    print(f"  設定ファイル: {args.config}")
    print(f"  出力ファイル: {args.output}")
    print(f"  制限時間:     {args.time_limit}秒")
    print("=" * 60)
    print()

    start_time = time.time()

    # シフト生成
    result = create_shift(args.config, time_limit=args.time_limit)

    if result is None:
        print("\n❌ シフトの生成に失敗しました。")
        print("設定ファイルの制約条件を見直してください。")
        sys.exit(1)

    # Excel出力
    export_to_excel(result, args.output)

    elapsed = time.time() - start_time

    # 結果サマリー
    print()
    print("=" * 60)
    print("  生成結果サマリー")
    print("=" * 60)
    print(f"  施設名:     {result['facility_name']}")
    print(f"  対象月:     {result['year']}年{result['month']}月")
    print(f"  スタッフ数: {len(result['staff'])}名")
    print(f"  処理時間:   {elapsed:.1f}秒")
    print()

    # 不備報告
    violations = result.get('violations', [])
    if violations:
        print(f"  ⚠ 不備: {len(violations)}件")
        for v in violations:
            print(f"    - {v}")
    else:
        print("  ✅ ルール違反なし")

    print()
    print(f"  出力ファイル: {args.output}")
    print("=" * 60)


if __name__ == '__main__':
    main()

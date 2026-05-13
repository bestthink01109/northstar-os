from get_attendance_data import fetch_attendance_data
import json

month = "2026-05"
print(f"--- {month} のデータ取得テスト ---")
data = fetch_attendance_data(month)

if data:
    # 最初の3人分だけ表示して確認
    sample = {k: data[k] for i, k in enumerate(data) if i < 3}
    print(json.dumps(sample, indent=2, ensure_ascii=False))
    print(f"\n合計 {len(data)} 名のデータを取得しました。")
else:
    print("データが見つかりませんでした。LINEで報告がまだないか、日付が一致していない可能性があります。")

import requests
import json

GAS_URL = "https://script.google.com/macros/s/AKfycbyJRWyE6OMarLdiFTTVnQnN2SiS6uvjv0X-LM4d6FrDMqWr1ldLEZ-nW4ewJ66I8frtGg/exec"

def inspect_raw_data():
    print("--- 実績ログの全件調査 (原文付き) ---")
    response = requests.get(GAS_URL, params={"month": "2026-05"})
    data = response.json()
    
    for i, row in enumerate(data):
        # row: [timestamp, name, date, status, site, overtime, bento, original_message]
        if len(row) < 8: continue
        print(f"Row {i+2}: 氏名={row[1]}, 日付={row[2]}, 残業={row[5]}, 原文='{row[7]}'")

if __name__ == "__main__":
    inspect_raw_data()

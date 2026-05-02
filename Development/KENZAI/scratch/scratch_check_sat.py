import os
import openpyxl

wb_path = os.path.expanduser("~/Library/CloudStorage/GoogleDrive-bestthink01109@gmail.com/マイドライブ/🏢【KENZAI】給与計算/📥 01_ここに入力データをポン（生データ用）/平野工業/【出勤簿】202604.xlsx")
wb = openpyxl.load_workbook(wb_path, data_only=True)
sheet = wb["上田力也"]

print(f"Name: 上田力也")
# 1日、4日、11日の行（1日の行は 14行目? 12行目? 出勤簿なのでA列かB列が日付になっているはず）
for row in range(5, 36):
    day_val = sheet[f"B{row}"].value
    if hasattr(day_val, 'day') and day_val.day in [1, 4, 11]:
        place = sheet[f"D{row}"].value
        t_in = sheet[f"J{row}"].value
        t_site_s = sheet[f"L{row}"].value
        t_site_e = sheet[f"N{row}"].value
        t_out = sheet[f"P{row}"].value
        work = sheet[f"R{row}"].value
        ot_in = sheet[f"T{row}"].value
        ot_out = sheet[f"S{row}"].value
        abs_time = sheet[f"V{row}"].value
        time_off = sheet[f"W{row}"].value
        print(f"{day_val}日: 出={t_in}, 現終={t_site_e}, 退={t_out}, 勤={work}, 内={ot_in}, 外={ot_out}, 欠={abs_time}, 時間休={time_off}")


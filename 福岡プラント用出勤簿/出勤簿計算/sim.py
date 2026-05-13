import openpyxl
from datetime import datetime
wb = openpyxl.load_workbook('../【出勤簿】202604_計算式適用済.xlsx')
ws = wb['坂井　謙斗']

# Mock evaluation of B (date) and D (status)
# April 2026 starts on Wed.
# B4 = Apr 1
dates = []
status = []
for r in range(4, 35):
    d_val = ws[f'D{r}'].value
    dates.append(r) # just use row index as proxy for date if we just need sequential
    status.append(d_val)
    print(f"Row {r}: Status {d_val}")


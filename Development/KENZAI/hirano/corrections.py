"""
hirano/corrections.py
平野工業 出勤簿Excelの入力ミス修正値を定義する。

パーサーがExcelから読み取った値を、ここに定義した正しい値で上書きする。
Excelファイル本体は変更しない。

フォーマット:
    CORRECTIONS = {
        年月(int, YYYYMM): {
            '社員名（シート名）': {
                日(int): {
                    フィールド名: 修正後の値,
                    ...
                }
            }
        }
    }

対応フィールド名（day_rec の dict キー）:
    t_start        ... 実績開始時刻（float, 例 8.0 = 8:00）
    t_end          ... 実績終了時刻（float）
    excel_work     ... Excelの勤務時間記載値
    excel_absence  ... Excelの欠勤記載値
    excel_ot_in    ... Excelの所内（法定内残業）記載値
    excel_ot_out   ... Excelの法定外残業記載値
    time_off       ... 時間休（float, h）
    is_absent      ... 欠勤フラグ（bool）
    is_paid        ... 有給フラグ（bool）
"""

CORRECTIONS = {
    202604: {
        '池田優紀': {
            # Day30: Excelの勤務時間が7hと誤記。時間休3.5hがあるため正解は3.5h
            30: {
                'excel_work': 3.5,
            },
        },
        '松岡颯太': {
            # Day24: 出社時間8:00の入力漏れ。t_startを9.0→8.0に修正
            24: {
                't_start': 8.0,
            },
        },
        '有村正和': {
            # Day21: 勤務時間1h・欠勤6hが誤記。正解は勤務2.5h・欠勤4.5h
            21: {
                'excel_work':    2.5,
                'excel_absence': 4.5,
            },
        },
        '平野珠美': {
            # Day28: Excelの勤務時間が空白（0h）。正解は4h
            28: {
                'excel_work': 4.0,
            },
        },
    },
}


def apply_corrections(all_sheets, year, month):
    """
    parse() が返した all_sheets リストに対して、CORRECTIONS の修正値を適用する。

    Args:
        all_sheets: ExcelParser.parse() の戻り値
        year: 対象年（int）
        month: 対象月（int）

    Returns:
        修正適用済みの all_sheets（in-place 変更）
    """
    yyyymm = year * 100 + month
    if yyyymm not in CORRECTIONS:
        return all_sheets

    month_corrections = CORRECTIONS[yyyymm]

    for sheet_data in all_sheets:
        name = sheet_data['sheet_name']
        if name not in month_corrections:
            continue

        day_corrections = month_corrections[name]
        applied = []

        for day_rec in sheet_data['days']:
            d = day_rec['day']
            if d not in day_corrections:
                continue
            for field, new_val in day_corrections[d].items():
                old_val = day_rec.get(field)
                day_rec[field] = new_val
                applied.append(f'{name} Day{d} {field}: {old_val}→{new_val}')

        if applied:
            for msg in applied:
                print(f'  [補正] {msg}')

    return all_sheets

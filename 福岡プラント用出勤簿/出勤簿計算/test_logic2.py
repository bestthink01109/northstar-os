def calc_week():
    bd = [7, 9, 9, 7, 9, 9, 5]
    d = ['振出', '出張', '出張', '出張', '出張', '出張', '出張']
    
    # Calculate BE, BG
    be = []
    bg = []
    for i in range(7):
        is_sun_furishutsu = (i == 0 and d[i] == '振出')
        is_weekday = (1 <= i <= 5)
        
        be_val = min(bd[i], 7) if (is_weekday or is_sun_furishutsu) else min(bd[i], 5)
        bf = max(0, bd[i] - be_val)
        bg_val = min(bf, 1) if (is_weekday or is_sun_furishutsu) else min(bf, 3)
        
        be.append(be_val)
        bg.append(bg_val)
        
    sum_be = sum(be)
    aj2 = 0
    bi = max(0, 40 - (sum_be + aj2))
    
    bh_cum = aj2
    bj_cum = 0
    
    print("Day | BD | BE | BG | BH | BI | BJ | R | S | T")
    for i in range(7):
        r = max(0, min(be[i], 40 - bh_cum))
        bh_cum += be[i]
        
        s = max(0, min(bg[i], bi - bj_cum))
        bj_cum += bg[i]
        
        t = bd[i] - r - s
        
        print(f"{i}   | {bd[i]}  | {be[i]}  | {bg[i]}  | {bh_cum-be[i]}  | {bi}  | {bj_cum-bg[i]}  | {r} | {s} | {t}")

calc_week()

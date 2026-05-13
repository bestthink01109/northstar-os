def calc_week():
    # Simulate days
    # Sunday (12th) to Saturday (18th)
    # BD = worked hours
    bd = [7, 7, 7, 7, 7, 7, 5]
    d = ['振出', '現場', '現場', '現場', '現場', '現場', '現場']
    
    bi = 0
    bh_cum = 0
    
    print("Day | BD | BE | BG | BI | R | S | T | BH")
    for i in range(7):
        is_sun_furishutsu = (i == 0 and d[i] == '振出')
        is_weekday = (1 <= i <= 5)
        
        # Original BE
        if is_weekday or is_sun_furishutsu:
            be = min(bd[i], 7)
        else:
            be = min(bd[i], 5)
            
        # Original BF
        bf = max(0, bd[i] - be)
        
        # Original BG
        if is_weekday or is_sun_furishutsu:
            bg = min(bf, 1)
        else:
            bg = min(bf, 3)
            
        bi = bh_cum
        bh_cum += be + bg
        
        r = max(0, min(be, 40 - bi))
        s = max(0, min(bg, 40 - bi - r))
        t = bd[i] - r - s
        
        print(f"{i}   | {bd[i]}  | {be}  | {bg}  | {bi} | {r} | {s} | {t} | {bh_cum}")

calc_week()

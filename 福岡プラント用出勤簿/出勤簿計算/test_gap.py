def test():
    # Sun, Mon, Tue, Wed, Thu, Fri, Sat
    # Expected BE: 0 (if not furishutsu), 7, 7, 7, 7, 7, 5
    expected_be = [0, 7, 7, 7, 7, 7, 5]
    actual_be   = [0, 7, 7, 7, 7, 7, 5] # Perfect week
    
    # Gap per day
    daily_gap = [max(0, e - a) for e, a in zip(expected_be, actual_be)]
    print(f"Perfect week gap: {sum(daily_gap)}") # Should be 0
    
    # Absent on Tuesday
    actual_be_absent = [0, 7, 0, 7, 7, 7, 5]
    daily_gap_absent = [max(0, e - a) for e, a in zip(expected_be, actual_be_absent)]
    print(f"Absent Tue gap: {sum(daily_gap_absent)}") # Should be 7
    
    # Incomplete final week (Mon-Thu only)
    expected_inc = [0, 7, 7, 7, 7]
    actual_inc   = [0, 7, 7, 7, 7] # Perfect Mon-Thu
    daily_gap_inc = [max(0, e - a) for e, a in zip(expected_inc, actual_inc)]
    print(f"Incomplete perfect week gap: {sum(daily_gap_inc)}") # Should be 0
    
    # Incomplete final week (Mon-Thu), absent Tue
    actual_inc_absent = [0, 7, 0, 7, 7]
    daily_gap_inc_absent = [max(0, e - a) for e, a in zip(expected_inc, actual_inc_absent)]
    print(f"Incomplete absent Tue gap: {sum(daily_gap_inc_absent)}") # Should be 7

test()

from datetime import datetime

def calculate_fee(minutes: int) -> int:
    if minutes <= 10:
        return 0  # 회차
    elif minutes < 40:
        return 3000  # 기본요금
    else:
        x_fee = (minutes-40 // 10) * 1000
        return 3000 + x_fee + 1000

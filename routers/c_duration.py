from fastapi import APIRouter, HTTPException
from datetime import datetime
import sqlite3, os
from utils.fee import calculate_fee

router = APIRouter(
    prefix="/api/v1",
    tags=["Cars"]
)

DB_PATH = os.path.join(os.path.dirname(__file__), "../db/car.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

@router.get("/duration")
def duration(plate: str):
    # 출차되지 않은 가장 최근 입차 기록 조회
    cursor.execute("""
        SELECT in_time, out_check 
        FROM cars 
        WHERE plate=? AND out_check=0 
        ORDER BY in_time DESC 
        LIMIT 1
    """, (plate,))
    car = cursor.fetchone()

    if not car:
        raise HTTPException(status_code=404, detail="입차 중인 차량이 없습니다.")  

    in_time = datetime.strptime(car[0], "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    diff = now - in_time
    minutes = int(diff.total_seconds() // 60)
    hours = minutes // 60
    remain_minutes = minutes % 60
    fee = calculate_fee(minutes)

    return {
        "plate": plate,
        "time_data": f"{hours}시간 {remain_minutes}분",
        "minutes": minutes,
        "fee": fee
    }

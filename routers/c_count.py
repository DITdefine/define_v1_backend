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

@router.get("/CarCount")
def duration():
    # 출차되지 않은 차량 수 조회
    cursor.execute("""
        SELECT COUNT(*) 
        FROM cars
        WHERE out_check = 0;
    """)
    car = cursor.fetchone()

    if car is None:
        raise HTTPException(status_code=404, detail="ERROR")  

    count_outCheck = car[0]  # 튜플의 첫 번째 값이 COUNT 결과

    return {
        "count": count_outCheck,
    }


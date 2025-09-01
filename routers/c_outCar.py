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

@router.post("/outCar")
def out_car(plate: str):
    cursor.execute("SELECT plate, in_time, out_time, out_check, fee FROM cars WHERE plate=? AND out_check=0", (plate,))
    car = cursor.fetchone()
    if not car:
        raise HTTPException(status_code=404, detail="출차 가능한 차량이 없습니다.")
    
    # car[1] 은 in_time 확실히 가져옴
    in_time = datetime.strptime(car[1], "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    minutes = int((now - in_time).total_seconds() // 60)
    fee = calculate_fee(minutes)

    out_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "UPDATE cars SET out_time=?, out_check=1, fee=? WHERE plate=?",
        (out_time_str, fee, plate)
    )
    conn.commit()
    return {"plate": car[0], "in_time": car[1], "out_time": out_time_str, "fee": fee}


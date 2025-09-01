from fastapi import APIRouter, HTTPException
from datetime import datetime
import sqlite3
import os

router = APIRouter(
    prefix="/api/v1",
    tags=["Cars"]
)

DB_PATH = os.path.join(os.path.dirname(__file__), "../db/car.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

@router.post("/inCar")
def in_car(plate: str):
    cursor.execute("SELECT * FROM cars WHERE plate=? AND out_check=0", (plate,))
    existing = cursor.fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="이미 입차 상태입니다.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO cars (plate, in_time, out_time, out_check, fee) VALUES (?, ?, ?, ?, ?)",
        (plate, now, None, 0, None)
    )
    conn.commit()
    return {"plate": plate, "in_time": now}

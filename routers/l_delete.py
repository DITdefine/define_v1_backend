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

@router.post("/deleteAll")
def out_car():
    cursor.execute("DELETE FROM cars; VACUUM;")
    conn.commit()
    return {"date": "완료"}


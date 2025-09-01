from fastapi import APIRouter
import sqlite3, os

router = APIRouter(
    prefix="/api/v1",
    tags=["List"]
)

DB_PATH = os.path.join(os.path.dirname(__file__), "../db/car.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

@router.get("/list")
def list_in_cars():
    cursor.execute("SELECT plate, in_time FROM cars WHERE out_check=0")
    cars = cursor.fetchall()
    return [{"plate": plate, "in_time": in_time} for plate, in_time in cars]

from fastapi import APIRouter, Query, HTTPException
import sqlite3, os
from typing import Optional

router = APIRouter(
    prefix="/api/v1",
    tags=["List"]
)

DB_PATH = os.path.join(os.path.dirname(__file__), "../db/car.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

@router.get("/log")
def list_log(
    start_date: Optional[str] = Query(None, description="조회 시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="조회 종료 날짜 (YYYY-MM-DD)")
):
    try:
        if start_date and end_date:
            # 기간 조회
            cursor.execute("""
                SELECT plate, in_time, out_time, out_check, fee
                FROM cars
                WHERE DATE(in_time) BETWEEN ? AND ?
                ORDER BY in_time ASC
            """, (start_date, end_date))
        elif start_date:
            # 시작일만 지정 → 해당 날짜 조회
            cursor.execute("""
                SELECT plate, in_time, out_time, out_check, fee
                FROM cars
                WHERE DATE(in_time) = ?
                ORDER BY in_time ASC
            """, (start_date,))
        else:
            # 날짜 미지정 → 오늘 날짜 조회
            cursor.execute("""
                SELECT plate, in_time, out_time, out_check, fee
                FROM cars
                WHERE DATE(in_time) = DATE('now')
                ORDER BY in_time ASC
            """)
        
        cars = cursor.fetchall()
        if not cars:
            raise HTTPException(status_code=404, detail="해당 날짜의 로그가 없습니다.")

        return [
            {
                "plate": plate,
                "in_time": in_time,
                "out_time": out_time,
                "out_check": bool(out_check),
                "fee": fee
            }
            for plate, in_time, out_time, out_check, fee in cars
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    start_datetime: Optional[str] = Query(None, description="조회 시작 일시 (YYYY-MM-DD HH:MM:SS)"),
    end_datetime: Optional[str] = Query(None, description="조회 종료 일시 (YYYY-MM-DD HH:MM:SS)"),
    plate: Optional[str] = Query(None, description="조회할 차량 번호판 (예: 12가3456)")
):
    """
    차량 로그 조회 API  
    - 날짜 + 시간 + 번호판 단위로 조회 가능  
    - 예: /api/v1/log?plate=12가3456&start_datetime=2025-10-15%2000:00:00&end_datetime=2025-10-15%2023:59:59
    """
    try:
        # 쿼리 조합
        query = """
            SELECT plate, in_time, out_time, out_check, fee
            FROM cars
            WHERE 1=1
        """
        params = []

        if start_datetime and end_datetime:
            query += " AND DATETIME(in_time) BETWEEN ? AND ?"
            params += [start_datetime, end_datetime]
        elif start_datetime:
            query += " AND DATETIME(in_time) >= ?"
            params.append(start_datetime)
        elif end_datetime:
            query += " AND DATETIME(in_time) <= ?"
            params.append(end_datetime)
        else:
            query += " AND DATE(in_time) = DATE('now')"

        if plate:
            query += " AND plate LIKE ?"
            params.append(f"%{plate}%")  # 일부 검색도 가능

        query += " ORDER BY in_time ASC"

        cursor.execute(query, params)
        cars = cursor.fetchall()

        if not cars:
            raise HTTPException(status_code=404, detail="해당 조건의 로그가 없습니다.")

        return [
            {
                "plate": plate,
                "in_time": in_time,
                "out_time": out_time,
                "out_check": bool(out_check),
                "fee": fee,
                
            }
            for plate, in_time, out_time, out_check, fee in cars
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

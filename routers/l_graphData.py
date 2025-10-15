from fastapi import APIRouter, Query, HTTPException
import sqlite3, os
from typing import Optional

router = APIRouter(
    prefix="/api/v1",
    tags=["Statistics"]
)

DB_PATH = os.path.join(os.path.dirname(__file__), "../db/car.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()


@router.get("/graphData")
def hourly_entry_and_revenue(
    start_date: Optional[str] = Query(None, description="조회 시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="조회 종료 날짜 (YYYY-MM-DD)")
):
    """
    시간대별 입차량 및 매출 데이터 반환 API  
    - 날짜 미지정 시: 오늘 0시~24시  
    - 날짜 범위 지정 시: 해당 기간 전체 합산  
    - 반환 형태: {"이용량": [...], "매출": [...]}
    """
    try:
        counts = [0] * 24   # 시간대별 입차 수
        revenue = [0] * 24  # 시간대별 매출 (fee 합계)

        # ========== 입차 데이터 ==========
        if start_date and end_date:
            cursor.execute("""
                SELECT STRFTIME('%H', in_time) AS hour, COUNT(*) 
                FROM cars
                WHERE DATE(in_time) BETWEEN ? AND ?
                GROUP BY hour
            """, (start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT STRFTIME('%H', in_time) AS hour, COUNT(*) 
                FROM cars
                WHERE DATE(in_time) = ?
                GROUP BY hour
            """, (start_date,))
        else:
            cursor.execute("""
                SELECT STRFTIME('%H', in_time) AS hour, COUNT(*) 
                FROM cars
                WHERE DATE(in_time) = DATE('now')
                GROUP BY hour
            """)

        for hour, count in cursor.fetchall():
            counts[int(hour)] = count

        # ========== 매출 데이터 ==========
        if start_date and end_date:
            cursor.execute("""
                SELECT STRFTIME('%H', out_time) AS hour, SUM(fee)
                FROM cars
                WHERE out_check = 1
                  AND DATE(out_time) BETWEEN ? AND ?
                GROUP BY hour
            """, (start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT STRFTIME('%H', out_time) AS hour, SUM(fee)
                FROM cars
                WHERE out_check = 1
                  AND DATE(out_time) = ?
                GROUP BY hour
            """, (start_date,))
        else:
            cursor.execute("""
                SELECT STRFTIME('%H', out_time) AS hour, SUM(fee)
                FROM cars
                WHERE out_check = 1
                  AND DATE(out_time) = DATE('now')
                GROUP BY hour
            """)

        for hour, total_fee in cursor.fetchall():
            revenue[int(hour)] = int(total_fee) if total_fee else 0

        return {
            "usage": counts,
            "sales": revenue
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

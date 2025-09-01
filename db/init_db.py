import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "car.db")

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT NOT NULL,
    in_time TEXT,
    out_time TEXT,
    out_check INTEGER,
    fee INTEGER
);
    """)
    
    conn.commit()
    conn.close()

# 직접 실행할 때만 초기화
if __name__ == "__main__":
    init_db()
    print("DB 초기화 완료!")

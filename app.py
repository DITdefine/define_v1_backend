from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    base, c_duration, c_inCar, c_outCar, c_setTime,
    l_list, a_login, l_log, c_count, l_graphData
)
from db.init_db import init_db

app = FastAPI()

# ================================
# ✅ DB 초기화
# ================================
init_db()

# ================================
# ✅ CORS 설정
# ================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (배포 시 제한 권장)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],  # 모든 헤더 허용
)

# ================================
# ✅ 라우터 등록
# ================================
app.include_router(base.router)
app.include_router(c_inCar.router)      # 입차
app.include_router(c_outCar.router)     # 출차
app.include_router(c_setTime.router)    # 시간 강제 설정
app.include_router(c_duration.router)   # 요금 계산
app.include_router(c_count.router)      # 카운트 관련
app.include_router(l_graphData.router)  # 그래프 데이터
app.include_router(a_login.router)      # 로그인
app.include_router(l_list.router)       # 리스트
app.include_router(l_log.router)        # 로그

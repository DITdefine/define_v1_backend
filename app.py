from fastapi import FastAPI
from routers import base, c_duration, c_inCar, c_outCar, c_setTime, l_list, a_login, l_log, c_count
from db.init_db import init_db

app = FastAPI()

init_db()

# 라우터 등록
app.include_router(base.router)

app.include_router(c_inCar.router) # 입차
app.include_router(c_outCar.router) # 출차
app.include_router(c_setTime.router) # 시간강제설정
app.include_router(c_duration.router) # 요금계산
app.include_router(c_count.router)

app.include_router(a_login.router)

app.include_router(l_list.router)
app.include_router(l_log.router)

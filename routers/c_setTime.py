from fastapi import APIRouter, HTTPException
from datetime import datetime
from models.schemas import ResponseModel
from .storage import car_db

router = APIRouter(
    prefix="/api/v1/car",
    tags=["Car - SetTime"]
)

@router.post("/setInTime", response_model=ResponseModel)
def set_in_time(plate: str, newTime: str):
    if plate not in car_db:
        raise HTTPException(status_code=404, detail="차량이 등록되지 않았습니다.")
    
    try:
        new_time = datetime.strptime(newTime, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="시간 형식은 YYYY-MM-DD HH:MM:SS 이어야 합니다.")
    
    car_db[plate].inTime = new_time
    return ResponseModel(
        status=200,
        message="입차 시간이 변경되었습니다.",
        data={
            "plateNumber": plate,
            "newInTime": new_time
        }
    )

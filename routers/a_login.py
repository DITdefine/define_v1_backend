from fastapi import APIRouter, HTTPException
from models.schemas import AuthLoginResponseModel

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth - login"]
)

@router.post("/login", response_model=AuthLoginResponseModel)
def login(id: str, password: str):
    # ✅ 더미 로그인 검증 (추후 DB 연동 가능)
    if id == "test" and password == "test":
        return AuthLoginResponseModel(
            status=200,
            id=id
            # password는 응답에서 제외
        )
    
    # 실패 케이스 (조건 단순화)
    raise HTTPException(status_code=400, detail="아이디 또는 비밀번호가 다릅니다.")

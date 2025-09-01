from fastapi import APIRouter
from models.schemas import ResponseModel

router = APIRouter(
    prefix="/api/v1",
    tags=["Base"]
)

@router.get("/", response_model=ResponseModel)
def hello_world():
    return ResponseModel(
        status=200,
        message="Hello, World!",
        data=[
            {"user": "성해", "id": 1},
            {"user": "성해1", "id": 2},
        ]
    )

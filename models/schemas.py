from pydantic import BaseModel
from datetime import datetime
from typing import Any

class ResponseModel(BaseModel):
    status: int
    message: str
    data: Any

class UploadResponseModel(BaseModel):
    status: int
    plateNumber: str
    inTime: datetime
    outTime: datetime | None
    outCheck: bool
    fee: int | None

class AuthLoginResponseModel(BaseModel):
    status: int
    id: str
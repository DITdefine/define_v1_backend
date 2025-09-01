from models.schemas import UploadResponseModel

# 메모리 DB (모든 라우터에서 공유)
car_db: dict[str, UploadResponseModel] = {}

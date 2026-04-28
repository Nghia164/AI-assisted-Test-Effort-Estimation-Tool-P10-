from fastapi import APIRouter

# ĐÂY LÀ DÒNG QUAN TRỌNG NHẤT: Khai báo biến router
router = APIRouter()

@router.get("/")
async def get_prediction_test():
    return {"message": "Module Prediction đã kết nối thành công"}
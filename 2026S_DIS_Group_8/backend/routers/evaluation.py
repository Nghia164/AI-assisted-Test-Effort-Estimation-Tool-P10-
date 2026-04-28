from fastapi import APIRouter

# ĐÂY LÀ DÒNG THIẾU: Khai báo biến router
router = APIRouter()

@router.get("/")
async def test_evaluation():
    return {"message": "Module Evaluation đã hoạt động"}
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def test_extensions():
    return {"message": "Module Extensions đã kết nối thành công"}
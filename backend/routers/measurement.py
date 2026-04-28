# File: D:\P10\backend\routers\measurement.py
from fastapi import APIRouter

# Bắt buộc phải có biến 'router' này để main.py import được
router = APIRouter()

@router.get("/")
async def test_measurement():
    return {"message": "Module Measurement hoạt động"}
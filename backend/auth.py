# file: auth.py
from passlib.context import CryptContext

# Thiết lập thuật toán mã hóa mật khẩu bằng bcrypt (bảo mật 1 chiều)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Hàm kiểm tra mật khẩu do User nhập có khớp với Hash trong DB không"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hàm mã hóa mật khẩu trước khi lưu xuống SQL Server"""
    return pwd_context.hash(password)

# Code giả lập: Admin không thể xem mật khẩu gốc, chỉ lưu chuỗi băm
# Ví dụ: Mật khẩu "123456" sẽ biến thành "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj
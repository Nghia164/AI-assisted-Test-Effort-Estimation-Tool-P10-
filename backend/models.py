# file: backend/models.py
from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    """
    Bảng Users lưu trữ thông tin tài khoản người dùng và quản trị viên.
    Mật khẩu tuyệt đối không lưu plain-text mà lưu chuỗi băm (hashed_password) [5].
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # BẮT BUỘC: Phải có độ dài (ví dụ 50) để SQL Server cho phép tạo unique=True và index=True
    username = Column(String(50), unique=True, index=True, nullable=False)
    
    # Mật khẩu băm bằng bcrypt thường dài khoảng 60 ký tự, để 255 cho an toàn
    hashed_password = Column(String(255), nullable=False)
    
    # Phân quyền: 'user' (người dùng thường) hoặc 'admin' (quản trị viên) [5, 6]
    role = Column(String(20), default="user")
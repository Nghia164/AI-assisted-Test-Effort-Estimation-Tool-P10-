# file: database.py
from sqlalchemy import create_engine
# Đã sửa lỗi lặp từ ở dòng này thành declarative_base
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy.orm import sessionmaker
import urllib.parse

# Cấu hình chuỗi kết nối chuẩn tới (localdb)\MSSQLLocalDB
server = r'(localdb)\MSSQLLocalDB'
database = 'TestEffortDB'
driver = 'ODBC Driver 17 for SQL Server'

# Mã hóa chuỗi kết nối cho SQLAlchemy
params = urllib.parse.quote_plus(f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;")
SQLALCHEMY_DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"

# Tạo Engine kết nối DB
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Khởi tạo Base
Base = declarative_base()

# Hàm lấy DB session để sử dụng trong các API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
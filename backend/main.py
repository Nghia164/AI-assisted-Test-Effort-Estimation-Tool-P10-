from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
import uvicorn
import json
from typing import Optional
from database import engine, Base, SessionLocal, get_db
import google.generativeai as genai

# --- MODELS (Database Tables) ---
class DBUser(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True)
    email = Column(String(100))
    password = Column(String(100))
    role = Column(String(20), default="user")
    status = Column(String(20), default="active")

class DBHistory(Base):
    __tablename__ = "history"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True)
    filename = Column(String(255))
    ai_analysis = Column(Text)  
    metrics = Column(Text)      
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Lưu ngày tháng

# Tạo bảng (Chạy một lần)
Base.metadata.create_all(bind=engine)

# --- SCHEMAS (Pydantic Models) ---
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class EmailUpdate(BaseModel):
    username: str
    email: str

class PasswordUpdate(BaseModel):
    username: str
    current_password: str
    new_password: str

class HistoryCreate(BaseModel):
    username: str
    filename: str
    ai_analysis: str
    metrics: dict

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        if not db.query(DBUser).filter(DBUser.username == "admin").first():
            db.add(DBUser(username="admin", email="admin@test.com", password="1234a", role="admin"))
            db.commit()
    finally:
        db.close()
    yield

# --- KHỞI TẠO APP ---
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API AUTH ---
@app.post("/api/auth/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Tài khoản không tồn tại")
    if user.password != data.password:
        raise HTTPException(status_code=401, detail="Sai mật khẩu")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị khóa")
        
    return {
        "message": "Đăng nhập thành công",
        "user": {"username": user.username, "email": user.email, "role": user.role}
    }

@app.post("/api/auth/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(DBUser).filter(DBUser.username == data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
        
    new_user = DBUser(
        username=data.username, email=data.email, password=data.password, role="user", status="active"
    )
    db.add(new_user)
    db.commit()
    return {"message": "Đăng ký thành công!"}

# --- API USER ---
@app.get("/api/user/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == username).first()
    if not user: raise HTTPException(404, "User not found")
    return {"email": user.email, "role": user.role}

@app.put("/api/user/update-email")
def update_email(data: EmailUpdate, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == data.username).first()
    if user:
        user.email = data.email
        db.commit()
        return {"message": "Success"}
    return {"error": "User not found"}

@app.put("/api/user/change-password")
def change_password(data: PasswordUpdate, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == data.username).first()
    if user and user.password == data.current_password:
        user.password = data.new_password
        db.commit()
        return {"message": "Success"}
    return {"error": "Mật khẩu cũ không đúng"}

# --- API ADMIN (Khớp với React gọi /api/admin/...) ---
@app.get("/api/admin/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(DBUser).all()
    return {"users": users}

@app.put("/api/admin/users/{u_id}/toggle-status")
def toggle_status(u_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).get(u_id)
    if user:
        user.status = "inactive" if user.status == "active" else "active"
        db.commit()
        return {"message": "Success"}
    return {"error": "Not found"}

# ==================== BỔ SUNG 3 HÀM NÀY BÊN DƯỚI ====================

# 1. Soft Delete (Đưa vào thùng rác)
@app.put("/api/admin/users/{u_id}/soft-delete")
def soft_delete_user(u_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).get(u_id)
    if user:
        user.status = "deleted" # Chuyển trạng thái thành deleted
        db.commit()
        return {"message": "Đã đưa vào thùng rác"}
    return {"error": "Not found"}

# 2. Restore (Phục hồi từ thùng rác)
@app.put("/api/admin/users/{u_id}/restore")
def restore_user(u_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).get(u_id)
    if user:
        user.status = "active" # Khôi phục lại trạng thái hoạt động
        db.commit()
        return {"message": "Đã phục hồi tài khoản"}
    return {"error": "Not found"}

# 3. Hard Delete (Xóa vĩnh viễn khỏi Database)
@app.delete("/api/admin/users/{u_id}")
def hard_delete_user(u_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).get(u_id)
    if user:
        db.delete(user) # Lệnh xóa hẳn row trong DB
        db.commit()
        return {"message": "Đã xóa vĩnh viễn"}
    return {"error": "Not found"}

# --- API AI ESTIMATION (XỬ LÝ AI VÀ TOÁN HỌC CHUẨN) ---
@app.post("/api/analyze-and-estimate")
async def analyze_and_estimate(
    file: Optional[UploadFile] = File(None),
    hist_file: Optional[UploadFile] = File(None),
    manual_data: Optional[str] = Form(None)
):
    try:
        parsed_manual = {}
        if manual_data:
            parsed_manual = json.loads(manual_data)

        # LẤY FP
        fp_data = parsed_manual.get("fp", {})
        def get_fp(fp_type):
            try: return float(fp_data.get(fp_type, {}).get("count") or 0)
            except: return 0.0

        ufc = get_fp("ei")*4 + get_fp("eo")*5 + get_fp("eq")*4 + get_fp("ilf")*10 + get_fp("eif")*7
        try: vaf_sum = float(parsed_manual.get("vaf_sum") or 0)
        except: vaf_sum = 0.0
        vaf = 0.65 + 0.01 * vaf_sum
        fp_total = round(ufc * vaf, 2)

        # LẤY OP
        op_data = parsed_manual.get("op", {})
        screens, reports = op_data.get("screens", {}), op_data.get("reports", {})
        def get_op(data, key, weight):
            try: return float(data.get(key) or 0) * weight
            except: return 0.0

        raw_op = get_op(screens,"s",1) + get_op(screens,"m",2) + get_op(screens,"d",3) + \
                 get_op(reports,"s",2) + get_op(reports,"m",5) + get_op(reports,"d",8)
        
        try: comp_3gl = float(op_data.get("comp_3gl") or 0) * 10
        except: comp_3gl = 0.0
        raw_op += comp_3gl
        
        try: reuse = float(op_data.get("reuse") or 0)
        except: reuse = 0.0
        op_new = round(raw_op * (100 - reuse) / 100, 2)
        
        try: prod = float(op_data.get("prod") or 13)
        except: prod = 13.0
        effort_op_months = round(op_new / prod, 2) if prod > 0 else 0

        # LẤY UCP
        ucp_data = parsed_manual.get("ucp", {})
        actors = ucp_data.get("actors", [])
        use_cases = ucp_data.get("use_cases", [])

        uaw = 0
        for a in actors:
            t = str(a.get("type", "1"))
            uaw += int(t) if t in ["1", "2", "3"] else 1

        uucw = 0
        for u in use_cases:
            try: trans = int(u.get("transactions") or 0)
            except: trans = 0
            if trans <= 3: uucw += 5
            elif trans <= 7: uucw += 10
            else: uucw += 15

        uucp = uaw + uucw
        ucp_total = round(uucp * vaf, 2)

        # THÔNG SỐ KHÁC
        try: loc = int(parsed_manual.get("loc") or 0)
        except: loc = 0
        try: reqs = int(parsed_manual.get("requirements") or 0)
        except: reqs = 0

        # --- ĐỔI TOÁN HỌC: QUY RA THÁNG (MONTHS) THAY VÌ NGÀY/TUẦN ---
        primary_size = fp_total if fp_total > 0 else ucp_total
        test_cases = round(primary_size * 1.2) if primary_size > 0 else (reqs * 3)
        
        # Giả sử 1 người làm 20 ngày/tháng
        person_days = round(primary_size / 5) if primary_size > 0 else round(effort_op_months * 20)
        person_months = round(person_days / 20, 2) if person_days > 0 else effort_op_months
        person_months = max(0.1, person_months) # Ít nhất là 0.1 tháng

        team_size = 3
        duration_months = round(person_months / team_size, 2)

        # Tạo Testing Schedule
        prep_time = round(duration_months * 0.2, 2)
        exec_time = round(duration_months * 0.6, 2)
        close_time = round(duration_months * 0.2, 2)
        testing_schedule = f"1. Chuẩn bị Test Plan ({prep_time} tháng) | 2. Thực thi Test ({exec_time} tháng) | 3. Đóng gói & Review ({close_time} tháng)"

        # --- TẠO PHÂN TÍCH AI CHI TIẾT (GIỐNG CHATGPT) ---
        ai_text = f"""Chào bạn, dựa trên các thông số bạn vừa cung cấp, tôi đã phân tích chi tiết dự án như sau:

**1. Phân tích Quy mô Hệ thống (Size Measurement):**
* **Function Points (FP) - Đạt {fp_total}:** Dựa trên luồng dữ liệu đầu vào/đầu ra, dự án có độ phức tạp ở mức {'cao' if fp_total > 200 else 'trung bình'}.
* **Object Points (OP) - Đạt {op_new}:** Sau khi trừ đi tỷ lệ tái sử dụng mã nguồn ({reuse}%), chi phí để xây dựng các màn hình và báo cáo tốn khoảng {effort_op_months} person-months.
* **Use Case Points (UCP) - Đạt {ucp_total}:** Tổng cộng có {len(actors)} tác nhân và {len(use_cases)} Use cases tác động vào hệ thống.

**2. Ước lượng Nỗ lực & Nhân sự (Effort & Resource):**
* **Test Cases dự kiến:** Cần thiết kế khoảng **{test_cases} kịch bản test** để bao phủ toàn bộ luồng nghiệp vụ.
* **Nỗ lực Kiểm thử (Test Effort):** Tổng nỗ lực dự kiến là **{person_months} person-months** (tháng công).
* **Nhân sự (Testers):** Đề xuất sử dụng **{team_size} Testers** làm việc song song để tối ưu tiến độ.
* **Thời gian thực tế (Duration):** Với đội ngũ {team_size} người, dự án sẽ kéo dài khoảng **{duration_months} tháng**.

**3. Lịch trình Kiểm thử (Testing Schedule):**
Để quản lý tiến độ hiệu quả, bạn nên chia phase theo lịch trình sau:
* *Phase 1 (Chuẩn bị & Viết Testcase):* {prep_time} tháng.
* *Phase 2 (Thực thi & Log Bug):* {exec_time} tháng.
* *Phase 3 (Regression & UAT):* {close_time} tháng.

**💡 Đánh giá Rủi ro & Khuyến nghị:**
Nếu thời gian ({duration_months} tháng) quá dài so với Deadline thực tế, bạn cân nhắc tăng lượng Tester lên 4-5 người, hoặc ưu tiên áp dụng Automation Test vào Phase 2 để đẩy nhanh tốc độ hồi quy.
"""

        filename = file.filename if file else "Nhập liệu tay (Đã tính toán)"

        return {
            "filename": filename,
            "metrics": {
                "ufc": ufc,
                "vaf": round(vaf, 2),
                "fp": fp_total,
                "raw_op": raw_op,
                "op_new": op_new,
                "effort_op_months": effort_op_months,
                "uaw": uaw,
                "uucw": uucw,
                "uucp": uucp,
                "ucp": ucp_total,
                "loc": loc,
                "requirements": reqs,
                "estimated_test_cases": test_cases,
                "test_effort_person_months": person_months, # Cập nhật Key thành Months
                "estimated_duration_months": duration_months, # Cập nhật Key thành Months
                "recommended_team_size": team_size,
                "testing_schedule": testing_schedule # Bổ sung Testing Schedule
            },
            "ai_analysis": ai_text
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}
    
# --- API HISTORY ---
@app.post("/api/history")
def save_history(data: HistoryCreate, db: Session = Depends(get_db)):
    try:
        new_hist = DBHistory(
            username=data.username,
            filename=data.filename,
            ai_analysis=data.ai_analysis,
            metrics=json.dumps(data.metrics) 
        )
        db.add(new_hist)
        db.commit()
        return {"message": "Success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{username}")
def get_history(username: str, db: Session = Depends(get_db)):
    # Sắp xếp lịch sử lưu mới nhất lên đầu
    histories = db.query(DBHistory).filter(DBHistory.username == username).order_by(DBHistory.created_at.desc()).all()
    
    result = []
    for h in histories:
        try:
            metrics_dict = json.loads(h.metrics) if h.metrics else {}
        except:
            metrics_dict = {}
            
        result.append({
            "id": h.id,
            "username": h.username,
            "filename": h.filename,
            "ai_analysis": h.ai_analysis,
            "metrics": metrics_dict,
            "created_at": h.created_at.isoformat() if h.created_at else None
        })
        
    return {"history": result}


# CẤU HÌNH API KEY CỦA GEMINI (Thay thế chuỗi này bằng API Key thật của bạn)
GEMINI_API_KEY = "AIzaSyDrDKfhqZ8nQ0UIuhIG1r5U3liswm3-GcA"
genai.configure(api_key=GEMINI_API_KEY)

# Schema nhận dữ liệu Chat từ Frontend
class ChatMessage(BaseModel):
    message: str

# --- API CHATBOT (KẾT NỐI GEMINI) ---
@app.post("/api/chat")
async def chat_with_ai(data: ChatMessage):
    try:
        # Sử dụng mô hình Gemini 1.5 Flash (Nhanh) hoặc 2.5 Pro
        model = genai.GenerativeModel('gemini-2.5-flash') 
        
        # Nhồi thêm ngữ cảnh để AI đóng vai chuyên gia
        prompt = f"""Bạn là một chuyên gia cao cấp về kỹ thuật phần mềm và ước lượng kiểm thử (Test Effort Estimation).
        Người dùng đang sử dụng hệ thống của bạn và có câu hỏi sau: "{data.message}"
        Hãy trả lời trực tiếp, chuyên nghiệp, ngắn gọn và dễ hiểu. Sử dụng định dạng markdown (in đậm, gạch đầu dòng) để trình bày."""

        response = model.generate_content(prompt)
        return {"reply": response.text}
        
    except Exception as e:
        return {"reply": f"❌ Xin lỗi, hệ thống AI đang bận hoặc API Key chưa đúng. Chi tiết lỗi: {str(e)}"}

# --- CHẠY SERVER ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
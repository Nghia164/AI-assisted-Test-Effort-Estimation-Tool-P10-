🚀 Đồ án: AI-assisted Test Effort Estimation Tool (P10)
Môn học: Software Measurement & Analysis (CMU-CS 462)
Giảng viên hướng dẫn: Nguyễn Đức Mận
Tổ chức: Đại học Duy Tân (Duy Tan University)

--------------------------------------------------------------------------------
📖 1. Giới thiệu (Overview)
AI-assisted Test Effort Estimation Tool là công cụ phần mềm chuyên dụng hỗ trợ đo lường quy mô dự án và ước lượng nỗ lực kiểm thử (Test Effort) dựa trên các tiêu chuẩn đo lường quốc tế: Function Point (FP), Use-Case Point (UCP), và Object Point (OP).
Thay vì phải đếm và tính toán thủ công hàng trăm trang tài liệu, hệ thống tích hợp sâu Trí tuệ Nhân tạo (Google Gemini) để tự động đọc tài liệu Đặc tả yêu cầu (SRS), bóc tách thực thể (Actor, Transaction) và dự đoán trực tiếp các thông số: Số lượng kịch bản kiểm thử (Test cases), Nỗ lực (Person-days), Lịch trình (Schedule), và Quy mô đội ngũ (Team Size).
✨ Tính năng nổi bật
Phân tích tài liệu đa định dạng: Hỗ trợ đọc file .pdf, .docx, .txt, .csv, .xlsx.
Đo lường Đa mô hình (Multi-model): Tích hợp công thức chuẩn của FP, UCP, OP và COCOMO.
AI Trợ lý ảo (Chatbot): Tích hợp AI hỏi đáp trực tiếp về các chỉ số rủi ro của dự án.
Báo cáo chuẩn Kỹ sư: Tự động sinh Testing Estimation Report có thể chỉnh sửa và xuất ra PDF, Word, TXT.
Quản trị hệ thống (Admin Panel): Quản lý phân quyền người dùng, theo dõi lịch sử dự án, trạng thái hệ thống.

--------------------------------------------------------------------------------
🛠 2. Công nghệ sử dụng (Tech Stack)
Frontend: ReactJS, TailwindCSS (Giao diện Clean & Minimalist, tương thích cao), Chart.js.
Backend: Python, FastAPI (Xử lý bất đồng bộ, hiệu năng cao).
Cơ sở dữ liệu: SQL Server 2022 (localdb)\MSSQLLocalDB (Kết nối qua ORM SQLAlchemy & PyODBC).
Trí tuệ nhân tạo (AI/ML): Google Gemini 2.5 Flash API, kết hợp Xử lý ngôn ngữ tự nhiên (NLP).
Bảo mật: Bcrypt Hash (Mã hóa mật khẩu một chiều).

--------------------------------------------------------------------------------
⚙️ 3. Hướng dẫn Cài đặt & Vận hành (Installation & Setup)
Yêu cầu hệ thống: Python 3.9+, Node.js (v16+), và SQL Server Management Studio (SSMS) 2022.
Bước 3.1: Chuẩn bị Cơ sở dữ liệu (Database)
Mở phần mềm SQL Server Management Studio (SSMS) 2022.
Tại ô Server Name, nhập chính xác chuỗi sau và nhấn Connect:
Mở cửa sổ New Query và chạy lệnh SQL sau để tạo cơ sở dữ liệu:
Bước 3.2: Cài đặt và Khởi chạy Backend (Python / FastAPI)
Mở Terminal và di chuyển vào thư mục backend.
Tạo và kích hoạt môi trường ảo (Virtual Environment):
Cài đặt toàn bộ các thư viện bắt buộc:
Cấu hình AI: Mở file backend/estimation_logic.py, tìm biến GEMINI_API_KEY và dán API Key thật của bạn vào.
Khởi chạy Server:
(Backend sẽ chạy tại http://localhost:8000. Bạn có thể truy cập http://localhost:8000/docs để xem tài liệu API Swagger UI).
Bước 3.3: Cài đặt và Khởi chạy Frontend (ReactJS)
Mở một cửa sổ Terminal mới và di chuyển vào thư mục frontend.
Khởi tạo dự án React (Bỏ qua bước này nếu thư mục đã có sẵn mã nguồn React):
Cài đặt các thư viện phụ thuộc:
Khởi chạy ứng dụng:
(Trình duyệt sẽ tự động mở tại http://localhost:3000 hoặc 3001).

--------------------------------------------------------------------------------
🎯 4. Hướng dẫn sử dụng nhanh (Quick Start)
Truy cập vào ứng dụng Frontend.
Đăng ký một tài khoản mới hoặc sử dụng tài khoản mặc định admin / 1234a (được hệ thống tự sinh nếu DB trống).
Tại giao diện Dashboard, bạn có thể:
Cách 1: Tải lên một file Đặc tả yêu cầu (SRS) và để AI tự động đếm các thông số.
Cách 2: Nhập thủ công số lượng Màn hình (Screens), Báo cáo (Reports), hoặc số Actor để kiểm tra công thức tính OP/FP/UCP.
Bấm Bắt đầu ước lượng và xem hệ thống xuất Báo cáo chi tiết.

--------------------------------------------------------------------------------
👥 5. Đội ngũ phát triển (Team Members)
1.
2.
3.

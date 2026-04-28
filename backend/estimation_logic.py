import json
import re
from google import genai
import math

GEMINI_API_KEY = "AIzaSyDrDKfhqZ8nQ0UIuhIG1r5U3liswm3-GcA" 
client = genai.Client(api_key=GEMINI_API_KEY)

# --- CÁC HÀM THAM CHIẾU BẢNG FP ---
def get_ei_weight(det, ftr):
    if ftr <= 1: return 3 if det <= 15 else 4
    elif ftr == 2: return 3 if det <= 4 else (4 if det <= 15 else 6)
    else: return 4 if det <= 4 else 6

def get_eo_eq_weight(det, ftr, is_eo=True):
    low, avg, high = (4, 5, 7) if is_eo else (3, 4, 6)
    if ftr <= 1: return low if det <= 19 else avg
    elif ftr <= 3: return low if det <= 5 else (avg if det <= 19 else high)
    else: return avg if det <= 5 else high

def get_ilf_eif_weight(det, ret, is_ilf=True):
    low, avg, high = (7, 10, 15) if is_ilf else (5, 7, 10)
    if ret <= 1: return low if det <= 50 else avg
    elif ret <= 5: return low if det <= 19 else (avg if det <= 50 else high)
    else: return avg if det <= 19 else high

# THÊM MỚI: Xử lý logic nếu để trống thì lấy Average
def get_fp_weight(comp_type, det_val, ftr_val):
    # Các trọng số Average mặc định theo chuẩn
    averages = {'ei': 4, 'eo': 5, 'eq': 4, 'ilf': 10, 'eif': 7}
    
    # Nếu người dùng để trống DET hoặc FTR/RET -> Trả về trọng số Average
    if det_val == "" or ftr_val == "" or det_val is None or ftr_val is None:
        return averages.get(comp_type, 0)
        
    try:
        d = int(det_val)
        f = int(ftr_val)
    except ValueError:
        # Fallback nếu nhập chữ linh tinh
        return averages.get(comp_type, 0)
        
    if comp_type == 'ei': return get_ei_weight(d, f)
    elif comp_type == 'eo': return get_eo_eq_weight(d, f, is_eo=True)
    elif comp_type == 'eq': return get_eo_eq_weight(d, f, is_eo=False)
    elif comp_type == 'ilf': return get_ilf_eif_weight(d, f, is_ilf=True)
    elif comp_type == 'eif': return get_ilf_eif_weight(d, f, is_ilf=False)
    
    return 0

# --- HÀM XỬ LÝ CHÍNH ---
def calculate_all_metrics(data: dict):
    # 1. Tính UFC và FP
    fp_data = data.get('fp', {})
    ufc = 0
    
    ei = fp_data.get('ei', {})
    ufc += int(ei.get('count') or 0) * get_fp_weight('ei', ei.get('det'), ei.get('ftr'))
    
    eo = fp_data.get('eo', {})
    ufc += int(eo.get('count') or 0) * get_fp_weight('eo', eo.get('det'), eo.get('ftr'))
    
    eq = fp_data.get('eq', {})
    ufc += int(eq.get('count') or 0) * get_fp_weight('eq', eq.get('det'), eq.get('ftr'))
    
    ilf = fp_data.get('ilf', {})
    ufc += int(ilf.get('count') or 0) * get_fp_weight('ilf', ilf.get('det'), ilf.get('ret'))
    
    eif = fp_data.get('eif', {})
    ufc += int(eif.get('count') or 0) * get_fp_weight('eif', eif.get('det'), eif.get('ret'))
    
    vaf_sum = float(data.get('vaf_sum', 0))
    vaf = 0.65 + 0.01 * vaf_sum
    fp = ufc * vaf

    # 2. Tính OP (Object Points) 
    op_data = data.get('op', {})
    scr = op_data.get('screens', {})
    rep = op_data.get('reports', {})
    
    raw_op = (
        (int(scr.get('s', 0) or 0) * 1) + (int(scr.get('m', 0) or 0) * 2) + (int(scr.get('d', 0) or 0) * 3) +
        (int(rep.get('s', 0) or 0) * 2) + (int(rep.get('m', 0) or 0) * 5) + (int(rep.get('d', 0) or 0) * 8) +
        (int(op_data.get('comp_3gl', 0) or 0) * 10)
    )
    
    reuse_percent = int(op_data.get('reuse', 0) or 0)
    op_new = raw_op * (100 - reuse_percent) / 100
    prod = int(op_data.get('prod', 13) or 13)
    effort_op_months = op_new / prod if prod > 0 else 0

    # 3. Tính UCP (Use Case Points)
    ucp_data = data.get('ucp', {})
    actors = ucp_data.get('actors', [])
    use_cases = ucp_data.get('use_cases', [])
    
    uaw = sum(int(act.get('type', '1')) for act in actors)

    uucw = 0
    for uc in use_cases:
        trans = int(uc.get('transactions', 0) or 0)
        if trans == 0: pass 
        elif trans <= 3: uucw += 5
        elif trans <= 7: uucw += 10
        else: uucw += 15

    uucp = uaw + uucw
    ucp = uucp * vaf 

    # 4. Tính LOC & Number of Requirements
    total_loc = int(data.get('loc', 0) or 0)
    requirements = int(data.get('requirements', 0) or 0)

    # 5. Tổng hợp ước lượng
    estimated_test_cases = int(ucp * 1.2 + fp * 0.5 + requirements * 2) 
    final_effort_days = round((effort_op_months * 20) + (ucp * 0.5), 1)
    
    # --- FIX: TÍNH SỐ TESTER VÀ THỜI GIAN LINH ĐỘNG THEO CHUẨN COCOMO ---
    # 5.1 Quy đổi nỗ lực ra tháng công (Person-Months), giả định 20 ngày làm việc/tháng
    effort_person_months = final_effort_days / 20 if final_effort_days > 0 else 0
    
    if effort_person_months > 0:
        # 5.2 Ước lượng thời gian làm (Duration) bằng công thức chuẩn: Duration = 2.5 * (Effort ^ 0.38)
        --duration_months = 2.5 * math.pow(effort_person_months, 0.38)
        duration_months = 0
        # 5.3 Số lượng Tester = Tổng Nỗ lực / Thời gian (làm tròn lên)
        team_size = math.ceil(effort_person_months / duration_months)
    else:
        duration_months = 0
        team_size = 1

    # Đảm bảo tối thiểu luôn có 1 Tester
    team_size = max(1, int(team_size))
    
    # Quy đổi thời gian ra tuần để hiển thị (1 tháng ~ 4 tuần)
    duration_weeks = round(duration_months * 4, 1)
    # -------------------------------------------------------------------

    return {
        "ufc": ufc, "vaf": round(vaf, 4), "fp": round(fp, 2),
        "raw_op": raw_op, "op_new": round(op_new, 2), "effort_op_months": round(effort_op_months, 2),
        "uaw": uaw, "uucw": uucw, "uucp": uucp, "ucp": round(ucp, 2),
        "loc": total_loc,
        "requirements": requirements,
        "estimated_test_cases": estimated_test_cases,
        "test_effort_person_days": final_effort_days,
        "recommended_team_size": team_size,
        "estimated_duration_weeks": duration_weeks
    }

def generate_report_with_ai(metrics, historical_data):
    prompt = f"""
    Bạn là Chuyên gia Kỹ nghệ Phần mềm. Hệ thống đã tính quy mô dự án:
    
    [SỐ LIỆU TÍNH TOÁN]
    - Function Point: UFC={metrics['ufc']}, VAF={metrics['vaf']} => FP={metrics['fp']}
    - Object Point: Raw OP={metrics['raw_op']}, OP Mới={metrics['op_new']}, Effort Code (tháng)={metrics['effort_op_months']}
    - Use Case Point: UAW={metrics['uaw']}, UUCW={metrics['uucw']}, UUCP={metrics['uucp']} => UCP={metrics['ucp']}
    - Số lượng Requirements (Yêu cầu): {metrics['requirements']}
    - LOC: {metrics['loc']}
    - Lịch sử: {historical_data}
    
    [KẾT QUẢ ƯỚC LƯỢNG]
    - Test Case: {metrics['estimated_test_cases']}
    - Nỗ lực (Person-days): {metrics['test_effort_person_days']}
    - Thời gian (Weeks): {metrics['estimated_duration_weeks']}
    - Nhân sự đề xuất: {metrics['recommended_team_size']}
    
    Hãy viết Báo Cáo Ước Lượng Kiểm Thử giải thích ngắn gọn dựa vào số liệu. 
    Lưu ý: Bạn có thể trình bày chi tiết công thức tính FP, OP và UCP.
    TRẢ VỀ TEXT RAW HOẶC MARKDOWN.
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text
    except Exception as e:
        return f"Lỗi khi AI tạo báo cáo: {str(e)}"
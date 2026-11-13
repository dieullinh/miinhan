"""
MINH AN TECHNOLOGY SOLUTIONS - CUSTOMER-FACING AI SALES CONSULTANT
Trợ lý AI Trực tuyến Tư vấn & Trả lời Khách hàng B2B chuyên nghiệp
"""

import json
import urllib.request
import os
import re

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

CATALOG_DATA = {
    "MA-SRV-01": {
        "name": "Máy chủ Dell PowerEdge R750xs",
        "price": 85000000,
        "stock": 4,
        "lead_time": "2 ngày nếu có sẵn, 21 ngày nếu đặt thêm",
        "specs": "CPU Intel Xeon Silver 4314 (16 nhân), 32GB RAM DDR4 ECC, 2x 480GB SSD Enterprise RAID 1. Phù hợp chạy ảo hóa, ERP, máy chủ kế toán cho 50-150 người."
    },
    "MA-SW-01": {
        "name": "Switch Cisco Catalyst C9200L-24P-4G",
        "price": 28500000,
        "stock": 12,
        "lead_time": "1-2 ngày làm việc (Sẵn hàng)",
        "specs": "24 Cổng Gigabit PoE+ (công suất cấp nguồn camera/wifi), 4 cổng quang SFP 1G. Quản trị Layer 2/3 chuẩn doanh nghiệp, bảo mật 802.1X."
    },
    "MA-AP-01": {
        "name": "Bộ phát WiFi Aruba Instant On AP22",
        "price": 3800000,
        "stock": 35,
        "lead_time": "1 ngày làm việc (Sẵn số lượng lớn)",
        "specs": "Chuẩn Wi-Fi 6 (802.11ax), tốc độ 1.8 Gbps, chịu tải 75-100 thiết bị kết nối đồng thời, roaming mượt mà không rớt mạng, hỗ trợ quản lý Cloud miễn phí."
    },
    "MA-UPS-01": {
        "name": "Bộ lưu điện APC Smart-UPS 3000VA LCD RM 2U",
        "price": 34000000,
        "stock": 2,
        "lead_time": "2 ngày nếu có sẵn, 28 ngày nếu nhập thêm",
        "specs": "Công suất 3000VA / 2700W, dạng Rackmount 2U gắn tủ rack mạng. Duy trì nguồn điện sạch cho Server và Switch trong 15-30 phút khi cúp điện."
    },
    "MA-FW-01": {
        "name": "Tường lửa Fortinet FortiGate 60F",
        "price": 19500000,
        "stock": 0,
        "lead_time": "10 ngày làm việc (Kho đang hết hàng)",
        "specs": "10 cổng GE RJ45, thông lượng tường lửa 10 Gbps, bảo vệ chống mã độc, lọc web, VPN an toàn cho chi nhánh làm việc từ xa."
    },
    "MA-SVC-INS": {
        "name": "Dịch vụ lắp đặt và cấu hình hệ thống trọn gói",
        "price": 6000000,
        "stock": 999,
        "lead_time": "Triển khai trong 2 ngày",
        "specs": "Đội ngũ kỹ sư Minh An đến tận nơi thi công cáp, lắp tủ rack, chia VLAN mạng, cấu hình RAID Server, cài đặt OS và bàn giao nghiệm thu."
    }
}

SYSTEM_INSTRUCTION = """
Bạn là Trợ lý AI Bán hàng & Chuyên gia Giải pháp CNTT (AI Sales Consultant) của Công ty Công Nghệ Minh An.
Khách hàng đang nhắn tin trực tiếp với bạn để hỏi thông tin, tư vấn kỹ thuật, giá cả, tồn kho hoặc xin báo giá.

Bảng thông số và tồn kho chính xác của Minh An:
1. Máy chủ Dell R750xs: 85,000,000 VNĐ (Tồn kho: 4 chiếc, SLA 2 ngày). Cấu hình: Xeon Silver 4314, 32GB RAM, 2x 480GB SSD RAID 1.
2. Switch Cisco C9200L 24 cổng PoE: 28,500,000 VNĐ (Tồn kho: 12 chiếc, SLA 1-2 ngày). Cấp nguồn cho AP và Camera.
3. WiFi Aruba AP22: 3,800,000 VNĐ (Tồn kho: 35 chiếc, SLA 1 ngày). Chuẩn Wi-Fi 6, chịu tải 75-100 người.
4. Bộ lưu điện APC 3kVA: 34,000,000 VNĐ (Tồn kho: 2 chiếc, SLA 2 ngày). Dạng Rack 2U.
5. Tường lửa Fortinet 60F: 19,500,000 VNĐ (TỒN KHO = 0 - HẾT HÀNG, SLA NHẬP CHÍNH HÃNG 10 NGÀY).
6. Dịch vụ lắp đặt & cấu hình trọn gói: 6,000,000 VNĐ.

Quy tắc ứng xử và chính sách:
- Luôn xưng hô lịch sự, chuyên nghiệp: "Dạ em chào anh/chị", "Minh An xin kính chào Quý khách".
- Với Tường lửa Fortinet 60F: Phải trung thực báo kho đang hết hàng, thời gian nhập 10 ngày; nếu khách cần gấp trong 3 ngày thì giải thích rõ và đề xuất phương án cho mượn thiết bị demo dự phòng.
- Về chiết khấu: Chiết khấu chuẩn tối đa là 10% (thuộc quyền NVKD tự quyết). Nếu khách xin trên 10% (VD: 12-15%), hãy giải thích rằng cần trình Trưởng phòng duyệt và đề xuất hỗ trợ lập hồ sơ ngay.
- Nếu khách yêu cầu báo giá cụ thể và để lại thông tin: Hãy tóm tắt danh mục, tính tổng tiền rõ ràng, và xác nhận hệ thống đang khởi tạo file Báo giá Google Docs gửi tới email của khách.
"""

def generate_gemini_content(prompt: str, api_key: str = None) -> str:
    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return ""

    endpoint = f"{GEMINI_API_URL}?key={key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_INSTRUCTION}\n\nKHÁCH HÀNG HỎI:\n{prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 1024
        }
    }

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[Gemini API Call Error]: {e}")
        return ""


def call_customer_consultant(customer_query: str, api_key: str = None) -> dict:
    """
    Trợ lý AI trả lời câu hỏi trực tiếp của khách hàng.
    Trả về: {"answer": str, "auto_quote_created": bool, "quote_info": dict}
    """
    # 1. Thử gọi mô hình Gemini trực tiếp nếu có API Key
    llm_answer = generate_gemini_content(customer_query, api_key)
    if llm_answer:
        return {"answer": llm_answer, "auto_quote_created": False}

    # 2. Bộ Não AI Chuyên gia Bán hàng Cục bộ (Local AI Sales Consultant)
    q = customer_query.lower()
    
    # KỊCH BẢN 1: Hỏi về Fortinet / Hết hàng / Giao gấp 3 ngày
    if "fortinet" in q or "firewall" in q or "tường lửa" in q:
        if any(w in q for w in ["gấp", "3 ngày", "còn hàng", "sẵn", "bao lâu"]):
            ans = (
                "Dạ em chào anh/chị, em là Trợ lý AI Bán hàng của Minh An ạ!\n\n"
                "Về thiết bị **Tường lửa Fortinet FortiGate 60F** (Đơn giá niêm yết: **19.500.000 VNĐ**):\n"
                "• **Tình trạng tồn kho:** Hiện tại kho Minh An đang **tạm hết hàng** do nhu cầu triển khai cuối năm tăng cao.\n"
                "• **Thời gian nhập hàng (SLA):** Thời gian nhập chính hãng từ nhà phân phối cần **10 ngày làm việc**.\n\n"
                "⚠️ **Giải pháp cho anh/chị:** Nếu công ty mình cần gấp trong 3 ngày để kịp tiến độ bàn giao nhà xưởng, "
                "Minh An có chính sách **cho mượn tạm 01 thiết bị tương đương miễn phí** để lắp đặt trước, "
                "sau đó khi lô hàng Fortinet mới về trong 10 ngày, kỹ sư bên em sẽ qua đổi và hoàn thiện cấu hình chuẩn cho mình ạ!"
            )
            return {"answer": ans, "auto_quote_created": False}
        else:
            ans = (
                "Dạ em chào anh/chị, thiết bị **Tường lửa Fortinet FortiGate 60F** bên em đang niêm yết giá **19.500.000 VNĐ** (chưa VAT).\n"
                "• Thông số: 10 cổng GE RJ45, thông lượng 10 Gbps, hỗ trợ bảo vệ đa tầng (Antivirus, Web Filtering, IPS) và VPN kết nối từ xa.\n"
                "• Lưu ý: Thiết bị này hiện cần đặt hàng trước khoảng 10 ngày làm việc. Anh/chị cần triển khai số lượng bao nhiêu chiếc để em kiểm tra lô hàng về gần nhất ạ?"
            )
            return {"answer": ans, "auto_quote_created": False}

    # KỊCH BẢN 2: Hỏi giá & Cấu hình Dell R750xs Server
    if "dell" in q or "r750" in q or "server" in q or "máy chủ" in q:
        ans = (
            "Dạ em chào anh/chị, **Máy chủ Dell PowerEdge R750xs** bên em đang có sẵn tại kho với thông tin chi tiết như sau ạ:\n\n"
            "• **Đơn giá niêm yết:** **85.000.000 VNĐ** (Bảo hành 36 tháng chính hãng Dell ProSupport 24/7).\n"
            "• **Cấu hình tiêu chuẩn:** CPU Intel Xeon Silver 4314 (16 nhân / 32 luồng), RAM 32GB DDR4 ECC, 2 ổ SSD 480GB Enterprise chạy RAID 1 dự phòng dữ liệu an toàn.\n"
            "• **Tồn kho khả dụng:** Hiện kho còn **4 chiếc sẵn sàng giao trong 2 ngày làm việc**.\n\n"
            "Anh/chị dự kiến dùng máy chủ cho hệ thống phần mềm kế toán, ERP hay máy chủ ảo hóa để em tư vấn cấu hình RAM nâng cấp phù hợp nhất ạ?"
        )
        return {"answer": ans, "auto_quote_created": False}

    # KỊCH BẢN 3: Hỏi về Switch Cisco hoặc WiFi Aruba
    if "cisco" in q or "switch" in q or "aruba" in q or "wifi" in q:
        ans = (
            "Dạ em chào anh/chị, về thiết bị mạng văn phòng, Minh An đang sẵn hàng tại kho:\n\n"
            "1. **Switch Cisco Catalyst C9200L-24P-4G:** Giá **28.500.000 VNĐ** (Tồn kho: 12 chiếc). Có 24 cổng PoE+ cấp nguồn trực tiếp cho WiFi/Camera, 4 cổng quang Uplink 1G.\n"
            "2. **Bộ phát WiFi Aruba Instant On AP22:** Giá **3.800.000 VNĐ** (Tồn kho: 35 chiếc). Chuẩn Wi-Fi 6 thế hệ mới, chịu tải cực tốt 75-100 người dùng đồng thời, roaming mượt mà.\n\n"
            "Cả 2 dòng này đều đang có sẵn và có thể giao hàng lắp đặt ngay trong 24 giờ. Anh/chị có nhu cầu lắp đặt trọn gói không ạ?"
        )
        return {"answer": ans, "auto_quote_created": False}

    # KỊCH BẢN 4: Hỏi về chính sách Chiết khấu (12%, 15%, giảm giá...)
    if any(w in q for w in ["chiết khấu", "giảm giá", "bớt", "%"]):
        ans = (
            "Dạ em chào anh/chị, về **Chính sách Chiết khấu thương mại** tại Minh An:\n\n"
            "• **Mức chiết khấu thông thường (tối đa 10%):** Thuộc thẩm quyền tự quyết của Chuyên viên Kinh doanh cho các đơn hàng thiết bị và dịch vụ tiêu chuẩn.\n"
            "• **Mức chiết khấu từ 12% - 15%:** Thường áp dụng cho các khách hàng thân thiết, đơn hàng dự án lớn hoặc Quý công ty có kế hoạch thanh toán tạm ứng sớm.\n\n"
            "Nếu anh/chị cần duyệt mức chiết khấu từ 12% trở lên, em xin phép lập hồ sơ cơ hội chính thức và chuyển trực tiếp lên Trưởng phòng Kinh doanh phê duyệt ngay trong 15 phút để đảm bảo giá tốt nhất cho mình ạ!"
        )
        return {"answer": ans, "auto_quote_created": False}

    # KỊCH BẢN 5: Tư vấn giải pháp trọn gói theo quy mô văn phòng (VD: 30 người, 50 người, 100 người)
    if any(w in q for w in ["văn phòng", "người", "quy mô", "tư vấn", "trọn gói"]):
        ans = (
            "Dạ chào anh/chị, để trang bị hạ tầng CNTT tối ưu cho văn phòng doanh nghiệp, Minh An đề xuất phương án trọn gói chuẩn mực:\n\n"
            "1. **Tường lửa Bảo mật:** Fortinet 60F giúp bảo vệ dữ liệu công ty và phân quyền truy cập.\n"
            "2. **Hạ tầng Mạng trung tâm:** 1-2 Switch Cisco C9200L 24 cổng PoE cấp nguồn camera và mạng nội bộ ổn định.\n"
            "3. **Hệ thống WiFi 6:** 3-4 Bộ phát Aruba Instant On AP22 treo trần phân bổ đều khu làm việc (đảm bảo không bị nghẽn mạng giờ cao điểm).\n"
            "4. **Nguồn điện dự phòng:** 1 Bộ lưu điện APC 3000VA bảo vệ máy chủ không bị tắt đột ngột khi mất điện.\n"
            "5. **Dịch vụ thi công:** Kỹ sư Minh An lắp đặt, đi dây cáp và cấu hình bàn giao tận nơi (6.000.000 VNĐ).\n\n"
            "Ngân sách trọn gói ước tính khoảng 90 - 150 triệu tùy nhu cầu máy chủ. Anh/chị cho em xin thông tin email để em gửi bản dự toán chi tiết nhé ạ!"
        )
        return {"answer": ans, "auto_quote_created": False}

    # KỊCH BẢN MẶC ĐỊNH
    ans = (
        "Dạ em chào anh/chị! Em là Trợ lý AI Bán hàng của Công ty Công Nghệ Minh An.\n"
        "Minh An chuyên cung cấp chính hãng và triển khai trọn gói:\n"
        "• Máy chủ Dell PowerEdge R750xs\n"
        "• Thiết bị chuyển mạch Switch Cisco Catalyst C9200L\n"
        "• Bộ phát WiFi doanh nghiệp Aruba Instant On AP22\n"
        "• Thiết bị an ninh Tường lửa Fortinet FortiGate 60F\n"
        "• Bộ lưu điện APC Smart-UPS 3kVA\n"
        "• Dịch vụ lắp đặt và cấu hình mạng trọn gói.\n\n"
        "Anh/chị đang quan tâm đến sản phẩm nào, cần kiểm tra số lượng tồn kho hay cần em lên dự toán báo giá gửi qua email ạ?"
    )
    return {"answer": ans, "auto_quote_created": False}


def call_gemini_parser(raw_text: str, api_key: str = None) -> dict:
    prompt = f"""
Hãy bóc tách nội dung email/yêu cầu sau thành JSON:
Nội dung:
\"\"\"{raw_text}\"\"\"

Định dạng JSON cần trả về:
{{
  "customer_name": "Tên công ty",
  "contact_person": "Người liên hệ, SĐT, Email",
  "items": [
    {{"keyword": "Tên thiết bị (Dell, Cisco, Aruba, Fortinet, APC, Lắp đặt)", "quantity": 1}}
  ],
  "target_budget": null hoặc số tiền (VNĐ),
  "requested_deadline_days": null hoặc số ngày,
  "requested_discount_pct": 0.0
}}
Chỉ trả về JSON hợp lệ.
"""
    resp = generate_gemini_content(prompt, api_key)
    if resp:
        try:
            clean = resp.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except Exception:
            pass
    return None


def call_gemini_copilot(query: str, context: dict, api_key: str = None) -> str:
    res = call_customer_consultant(query, api_key)
    return res["answer"]


def call_gemini_rewrite_email(original_email: str, tone: str, api_key: str = None) -> str:
    prompt = f"""
Hãy viết lại nội dung email báo giá sau đây theo phong cách: [{tone}]
Bản gốc:
\"\"\"{original_email}\"\"\"

Yêu cầu:
- Giữ nguyên toàn bộ số tiền, mã báo giá và thông số kỹ thuật.
- Nếu phong cách là 'Đàm phán chiết khấu': Khéo léo giải thích lý do không thể giảm sâu hơn 10% mà tặng kèm gói hỗ trợ kỹ thuật hoặc bảo hành mở rộng.
- Viết bằng tiếng Việt chuyên nghiệp, chuẩn mực doanh nghiệp B2B.
"""
    resp = generate_gemini_content(prompt, api_key)
    if resp:
        return resp

    if tone == "negotiate":
        return original_email + "\n\n[LƯU Ý THƯƠNG LƯỢNG TỪ AI]: Về mức chiết khấu đề xuất trên 10%, Minh An xin phép giữ ở mức 10% tiêu chuẩn và tặng kèm gói kiểm thử an ninh mạng miễn phí 03 tháng để đảm bảo quyền lợi tối đa cho Quý công ty."
    elif tone == "formal":
        return original_email.replace("Chào bạn", "Kính gửi Quý Công ty").replace("Báo sớm nhé", "Trân trọng kính chúc Quý công ty ngày càng phát triển và thịnh vượng.")
    return original_email

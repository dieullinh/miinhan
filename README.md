# HỆ THỐNG AI AGENT CRM TỰ ĐỘNG HÓA - CÔNG TY CÔNG NGHỆ MINH AN

Giải pháp tích hợp AI Agent vào quy trình xử lý yêu cầu báo giá doanh nghiệp B2B (Email/Form -> Google Sheets -> Duyệt Email -> Google Docs).

---

## 1. MỤC TIÊU & GIẢI QUYẾT ĐIỂM NGHẼN

| Điểm nghẽn cũ của Minh An | Giải pháp của AI Agent |
| :--- | :--- |
| **Bỏ sót hạng mục / SKU không rõ** | AI Parser bóc tách từng sản phẩm, dịch vụ đi kèm; Fuzzy Match với Master Catalog để ánh xạ chính xác mã SKU. |
| **Dùng giá cũ hoặc giá tự nhớ** | AI tự động tra cứu bảng giá niêm yết hiện hành trong Master Catalog; không cho phép dùng giá cũ. |
| **Hứa thời hạn không đáp ứng được** | AI đối soát tồn kho khả dụng và thời gian đặt hàng (SLA); tự động cảnh báo nếu khách đòi gấp hơn năng lực kho. |
| **Thiếu ngân sách / Chưa rõ người duyệt** | Tự động phân tích trần ngân sách, gán NVKD theo thuật toán Round-Robin; nhận diện chiết khấu > 10% để chuyển Trưởng phòng duyệt. |
| **Chuyển qua lại không người theo dõi** | Mỗi yêu cầu tạo thành 1 Mã Hồ sơ Cơ hội (OPP-ID) với NVKD chịu trách nhiệm duy nhất và log kiểm toán (Audit Trail). |

---

## 2. KIẾN TRÚC ĐA TÁC NHÂN (MULTI-AGENT ARCHITECTURE)

1. **Ingestion & Extraction Agent**: Đọc hiểu văn bản phi cấu trúc từ Email/Web Form, trích xuất: Khách hàng, Sản phẩm, Số lượng, Ngân sách, Deadline, Mức chiết khấu.
2. **Catalog & Inventory Validation Agent**: Ánh xạ mã sản phẩm chuẩn, đối soát tồn kho khả dụng, tính SLA bàn giao.
3. **Policy & Approval Routing Agent**: Kiểm tra điều kiện chiết khấu (> 10% chuyển Trưởng phòng; $\le$ 10% NVKD tự quyết); so sánh ngân sách trần.
4. **Proposal & CRM Logging Agent**: Tự tạo bản ghi trên CRM/Google Sheets, nhân bản mẫu Google Docs và soạn sẵn Bản nháp Email gửi khách hàng.

---

## 3. CẤU TRÚC THƯ MỤC

- `agent_engine.py`: Module AI Agent Core (Python thuần không phụ thuộc thư viện ngoài).
- `data/master_catalog.json`: Bảng giá chuẩn, tồn kho khả dụng, SLA triển khai và danh sách NVKD.
- `data/test_inquiries.json`: Dữ liệu kiểm thử mẫu các yêu cầu thực tế.
- `google_apps_script/Code.gs`: Mã nguồn Google Apps Script nhúng trực tiếp vào Google Sheets / Google Docs theo đúng sơ đồ luồng của công ty.


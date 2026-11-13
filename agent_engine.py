"""
MINH AN TECHNOLOGY SOLUTIONS - AI AGENT ENGINE (STANDALONE ZERO-DEPENDENCY)
Hệ thống AI Agent tự động hóa xử lý Yêu cầu Báo giá & Hồ sơ Cơ hội
"""

import json
import os
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict


# ==========================================
# 1. DATA MODELS & SCHEMAS (Standard Dataclasses)
# ==========================================

@dataclass
class ExtractedItem:
    raw_text: str
    inferred_keyword: str
    quantity: int = 1


@dataclass
class ExtractedInquiry:
    inquiry_id: str
    customer_name: str
    contact_person: str
    email: str
    phone: str
    raw_request_text: str
    items: List[ExtractedItem] = field(default_factory=list)
    target_budget: Optional[float] = None
    requested_deadline_days: Optional[int] = None
    requested_discount_pct: float = 0.0
    missing_info_flags: List[str] = field(default_factory=list)


@dataclass
class ValidatedItem:
    sku: str
    product_name: str
    category: str
    quantity: int
    unit_price: float
    total_price: float
    stock_available: int
    is_in_stock: bool
    lead_time_days: int
    note: str = ""


@dataclass
class OpportunityProfile:
    opportunity_id: str
    created_at: str
    assigned_rep_id: str
    assigned_rep_name: str
    assigned_rep_email: str
    customer_name: str
    contact_person: str
    email: str
    phone: str
    items: List[ValidatedItem]
    subtotal: float
    discount_pct: float
    discount_amount: float
    final_total: float
    target_budget: Optional[float]
    budget_variance: Optional[float]
    budget_evaluation: str
    max_lead_time_days: int
    requested_deadline_days: Optional[int]
    deadline_feasibility: str
    approval_required: bool
    approval_status: str  # "AUTO_APPROVED", "PENDING_SALES_MANAGER", "REJECTED"
    approver_email: Optional[str]
    audit_notes: List[str] = field(default_factory=list)


# ==========================================
# 2. CATALOG & KNOWLEDGE BASE SERVICE
# ==========================================

class CatalogService:
    def __init__(self, catalog_path: str):
        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.products: List[Dict[str, Any]] = data["products"]
        self.policy: Dict[str, Any] = data["policy"]

    def find_best_product_match(self, query: str) -> Optional[Dict[str, Any]]:
        query_norm = query.lower()
        
        # Priority keyword mapping
        keyword_map = {
            "r750": "MA-SRV-01",
            "dell": "MA-SRV-01",
            "server": "MA-SRV-01",
            "cisco": "MA-SW-01",
            "c9200": "MA-SW-01",
            "switch": "MA-SW-01",
            "aruba": "MA-AP-01",
            "wifi": "MA-AP-01",
            "ap22": "MA-AP-01",
            "apc": "MA-UPS-01",
            "ups": "MA-UPS-01",
            "lưu điện": "MA-UPS-01",
            "fortinet": "MA-FW-01",
            "fortigate": "MA-FW-01",
            "firewall": "MA-FW-01",
            "tường lửa": "MA-FW-01",
            "lắp đặt": "MA-SVC-INS",
            "triển khai": "MA-SVC-INS",
            "cấu hình": "MA-SVC-INS"
        }

        matched_sku = None
        for kw, sku in keyword_map.items():
            if kw in query_norm:
                matched_sku = sku
                break

        if matched_sku:
            for p in self.products:
                if p["sku"] == matched_sku:
                    return p

        for p in self.products:
            if any(word in query_norm for word in p["name"].lower().split() if len(word) > 3):
                return p

        return None


# ==========================================
# 3. AGENT PIPELINE IMPLEMENTATION
# ==========================================

class MinhAnSalesAIAgent:
    def __init__(self, catalog_service: CatalogService):
        self.catalog = catalog_service
        self.rep_counter = 0

    def assign_rep(self) -> Dict[str, str]:
        """Round-robin load balancing for 6 sales reps"""
        reps = self.catalog.policy["reps"]
        rep = reps[self.rep_counter % len(reps)]
        self.rep_counter += 1
        return rep

    def parse_inquiry_agent(self, raw_data: Dict[str, Any]) -> ExtractedInquiry:
        """
        Agent 1: Ingestion & Extraction Agent
        Phân tích văn bản email/biểu mẫu, trích xuất thực thể và phát hiện thiếu thông tin.
        """
        raw_text = raw_data["raw_content"]
        inq_id = raw_data.get("id", "INQ-AUTO")
        cust = raw_data.get("customer", {})

        items = []
        lines = raw_text.split("\n")

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("Chào") or line_str.startswith("Tổng") or line_str.startswith("Yêu cầu"):
                continue

            # Check for service
            if any(k in line_str.lower() for k in ["lắp đặt", "triển khai", "cấu hình"]):
                items.append(ExtractedItem(raw_text=line_str, inferred_keyword="lắp đặt triển khai", quantity=1))
                continue

            # Regex matching
            m = re.search(r"(\d+)\s*(chiếc|bộ phát|bộ|con|cái|máy chủ)?\s*([a-zA-Z0-9\s\-_/]+)", line_str, re.IGNORECASE)
            if m:
                qty = int(m.group(1))
                desc = m.group(3).strip()
                if len(desc) > 3 and not desc.lower().startswith("ngày"):
                    items.append(ExtractedItem(raw_text=line_str, inferred_keyword=desc, quantity=qty))

        # Extract budget
        target_budget = None
        budget_match = re.search(r"ngân sách\s*(?:dự trù|khoảng|tối đa)?\s*[:\s]*(\d+[\.,]?\d*)\s*(triệu|tỷ|vnd|đ|tr)", raw_text, re.IGNORECASE)
        if budget_match:
            val = float(budget_match.group(1).replace(",", "."))
            unit = budget_match.group(2).lower()
            if unit in ["triệu", "tr"]:
                target_budget = val * 1_000_000
            elif unit == "tỷ":
                target_budget = val * 1_000_000_000
            else:
                target_budget = val

        # Extract deadline
        deadline_days = None
        deadline_match = re.search(r"(?:trong|sau|trước)\s*(\d+)\s*ngày", raw_text, re.IGNORECASE)
        if deadline_match:
            deadline_days = int(deadline_match.group(1))

        # Extract discount request
        requested_discount = 0.0
        discount_match = re.search(r"chiết khấu\s*(?:thêm|khoảng|mong muốn)?\s*[:\s]*(\d+[\.,]?\d*)\s*%", raw_text, re.IGNORECASE)
        if discount_match:
            requested_discount = float(discount_match.group(1).replace(",", "."))

        # Flags for missing info
        missing_flags = []
        if target_budget is None:
            missing_flags.append("Thiếu thông tin ngân sách dự trù (Budget not specified)")
        if deadline_days is None:
            missing_flags.append("Chưa xác định thời hạn triển khai mong muốn")
        if not items:
            missing_flags.append("Chưa nhận diện được danh sách sản phẩm cụ thể")

        return ExtractedInquiry(
            inquiry_id=inq_id,
            customer_name=cust.get("company_name", "Khách hàng Doanh nghiệp"),
            contact_person=cust.get("contact_person", "Đại diện mua hàng"),
            email=cust.get("email", ""),
            phone=cust.get("phone", ""),
            raw_request_text=raw_text,
            items=items,
            target_budget=target_budget,
            requested_deadline_days=deadline_days,
            requested_discount_pct=requested_discount,
            missing_info_flags=missing_flags
        )

    def validate_and_price_agent(self, extracted: ExtractedInquiry) -> OpportunityProfile:
        """
        Agent 2 & 3: Catalog/Inventory Validation + Policy & Routing Agent
        """
        validated_items: List[ValidatedItem] = []
        max_lead_time = 0
        audit_notes: List[str] = []

        for item in extracted.items:
            product = self.catalog.find_best_product_match(item.inferred_keyword)
            if product:
                qty = item.quantity
                unit_price = float(product["unit_price"])
                total = unit_price * qty
                in_stock = product["stock_available"] >= qty

                lead_days = product["lead_time_in_stock_days"] if in_stock else product["lead_time_out_stock_days"]
                if lead_days > max_lead_time:
                    max_lead_time = lead_days

                note = "Sẵn hàng tại kho" if in_stock else f"Tồn kho ({product['stock_available']}/{qty}) - Cần nhập hàng SLA {lead_days} ngày"

                validated_items.append(ValidatedItem(
                    sku=product["sku"],
                    product_name=product["name"],
                    category=product["category"],
                    quantity=qty,
                    unit_price=unit_price,
                    total_price=total,
                    stock_available=product["stock_available"],
                    is_in_stock=in_stock,
                    lead_time_days=lead_days,
                    note=note
                ))
            else:
                audit_notes.append(f"Không nhận diện được SKU chuẩn cho: '{item.raw_text}' -> Cần NVKD kiểm tra thủ công.")

        # Subtotal calculation
        subtotal = sum(i.total_price for i in validated_items)
        discount_pct = extracted.requested_discount_pct
        discount_amount = subtotal * (discount_pct / 100.0)
        final_total = subtotal - discount_amount

        # Budget evaluation
        budget_variance = None
        if extracted.target_budget:
            budget_variance = final_total - extracted.target_budget
            if budget_variance > 0:
                budget_status = f"Vượt ngân sách {budget_variance:,.0f} VNĐ ({((final_total/extracted.target_budget)-1)*100:.1f}%)"
            else:
                budget_status = f"Tối ưu trong ngân sách (Dư {-budget_variance:,.0f} VNĐ)"
        else:
            budget_status = "Khách hàng chưa cung cấp ngân sách trần"

        # Deadline feasibility
        if extracted.requested_deadline_days is not None:
            if max_lead_time > extracted.requested_deadline_days:
                deadline_feasibility = f"CẢNH BÁO: Khách yêu cầu {extracted.requested_deadline_days} ngày nhưng hàng cần tối thiểu {max_lead_time} ngày."
                audit_notes.append(deadline_feasibility)
            else:
                deadline_feasibility = f"Khả thi: Cam kết {max_lead_time} ngày (Khách yêu cầu {extracted.requested_deadline_days} ngày)"
        else:
            deadline_feasibility = f"Ước tính tiêu chuẩn: {max_lead_time} ngày làm việc"

        # Approval routing rule (Chiết khấu > 10%)
        approval_required = discount_pct > self.catalog.policy["max_rep_discount_percent"]
        approval_status = "PENDING_SALES_MANAGER" if approval_required else "AUTO_APPROVED"
        approver = self.catalog.policy["approver_email"] if approval_required else None

        if approval_required:
            audit_notes.append(f"Chiết khấu {discount_pct}% > 10% quy định -> Tự động chuyển luồng Trình Trưởng phòng duyệt.")
        else:
            audit_notes.append(f"Chiết khấu {discount_pct}% <= 10% -> Thuộc thẩm quyền NVKD, tự động duyệt.")

        rep = self.assign_rep()

        return OpportunityProfile(
            opportunity_id=f"OPP-{datetime.now().strftime('%Y%m%d')}-{extracted.inquiry_id.split('-')[-1]}",
            created_at=datetime.now().isoformat(),
            assigned_rep_id=rep["id"],
            assigned_rep_name=rep["name"],
            assigned_rep_email=rep["email"],
            customer_name=extracted.customer_name,
            contact_person=extracted.contact_person,
            email=extracted.email,
            phone=extracted.phone,
            items=validated_items,
            subtotal=subtotal,
            discount_pct=discount_pct,
            discount_amount=discount_amount,
            final_total=final_total,
            target_budget=extracted.target_budget,
            budget_variance=budget_variance,
            budget_evaluation=budget_status,
            max_lead_time_days=max_lead_time,
            requested_deadline_days=extracted.requested_deadline_days,
            deadline_feasibility=deadline_feasibility,
            approval_required=approval_required,
            approval_status=approval_status,
            approver_email=approver,
            audit_notes=audit_notes
        )

    def generate_proposals_and_drafts(self, opp: OpportunityProfile) -> Dict[str, str]:
        """
        Agent 4: Proposal & Email Response Generation Agent
        """
        items_table_text = ""
        for i, item in enumerate(opp.items, 1):
            items_table_text += f"  {i}. {item.product_name} | SL: {item.quantity} | Đơn giá: {item.unit_price:,.0f} VNĐ | TT: {item.total_price:,.0f} VNĐ ({item.note})\n"

        email_to_customer = f"""Kính gửi {opp.contact_person} - {opp.customer_name},

Cảm ơn Quý công ty đã tin tưởng gửi yêu cầu báo giá thiết bị và giải pháp công nghệ tới Minh An.
Tôi là {opp.assigned_rep_name}, Chuyên viên Kinh doanh phụ trách hỗ trợ trực tiếp Quý công ty.

Hệ thống đã tiếp nhận và lập phương án sơ bộ theo đúng yêu cầu như sau:
--------------------------------------------------------------------------------
CHI TIẾT DANH MỤC THIẾT BỊ & DỊCH VỤ:
{items_table_text}
- Tổng giá trị niêm yết: {opp.subtotal:,.0f} VNĐ
- Chiết khấu thương mại ({opp.discount_pct}%): -{opp.discount_amount:,.0f} VNĐ
- TỔNG GIÁ TRỊ ĐỀ XUẤT (Chưa VAT): {opp.final_total:,.0f} VNĐ
- Tiến độ triển khai dự kiến: {opp.max_lead_time_days} ngày làm việc kể từ ngày ký hợp đồng.
--------------------------------------------------------------------------------
{f"LƯU Ý VỀ TIẾN ĐỘ: {opp.deadline_feasibility}" if "CẢNH BÁO" in opp.deadline_feasibility else ""}

Bản báo giá chính thức chi tiết đã được khởi tạo tại liên kết Google Docs đính kèm:
[TẢI BÁO GIÁ CHÍNH THỨC SỐ {opp.opportunity_id}](https://docs.google.com/document/d/demo-minhan-{opp.opportunity_id})

Quý khách vui lòng phản hồi hoặc liên hệ trực tiếp tôi qua số hotline/Zalo để hoàn thiện thủ tục ký duyệt sớm nhất.

Trân trọng,
{opp.assigned_rep_name} | Phòng Kinh Doanh B2B
Công ty Công Nghệ Minh An | Email: {opp.assigned_rep_email}
"""

        email_to_manager = None
        if opp.approval_required:
            email_to_manager = f"""[TRÌNH PHÊ DUYỆT BÁO GIÁ VƯỢT THẨM QUYỀN - {opp.opportunity_id}]
Kính gửi Trưởng phòng Kinh doanh,

NVKD: {opp.assigned_rep_name} ({opp.assigned_rep_id}) vừa tiếp nhận cơ hội mới cần Trưởng phòng duyệt chiết khấu:
- Khách hàng: {opp.customer_name}
- Liên hệ: {opp.contact_person} ({opp.phone} - {opp.email})
- Tổng giá niêm yết: {opp.subtotal:,.0f} VNĐ
- Mức chiết khấu đề xuất: {opp.discount_pct}% (Vượt mức tự quyết 10% -> Cần duyệt)
- Giá trị sau chiết khấu: {opp.final_total:,.0f} VNĐ (Giảm {opp.discount_amount:,.0f} VNĐ)
- Đánh giá ngân sách khách hàng: {opp.budget_evaluation}
- Tính khả thi tiến độ kho: {opp.deadline_feasibility}

Hành động nhanh từ Email:
[ĐỒNG Ý DUYỆT] (Ghi nhận trạng thái Đã Duyệt & Tự động tạo Báo giá)
[TỪ CHỐI DUYỆT] (Chuyển trạng thái Hoàn thành - Từ chối)
"""

        return {
            "customer_email_draft": email_to_customer,
            "manager_approval_email": email_to_manager
        }


# ==========================================
# 4. EXECUTION DEMO
# ==========================================

def run_pipeline():
    print("=" * 80)
    print(" HỆ THỐNG AI AGENT CRM TỰ ĐỘNG HÓA - CÔNG TY CÔNG NGHỆ MINH AN")
    print("=" * 80)

    catalog_service = CatalogService("d:\\AGENT\\data\\master_catalog.json")
    agent = MinhAnSalesAIAgent(catalog_service)

    with open("d:\\AGENT\\data\\test_inquiries.json", "r", encoding="utf-8") as f:
        inquiries = json.load(f)

    results = []

    for idx, inq_data in enumerate(inquiries, 1):
        print(f"\n>>> [XỬ LÝ YÊU CẦU {idx}/{len(inquiries)}]: {inq_data['id']} từ {inq_data['customer']['company_name']}")
        
        # Step 1: Extraction
        extracted = agent.parse_inquiry_agent(inq_data)
        print(f"  [AI Agent 1] Bóc tách thành công {len(extracted.items)} hạng mục. Cảnh báo thiếu: {len(extracted.missing_info_flags)}")
        
        # Step 2: Validate & Price
        opp = agent.validate_and_price_agent(extracted)
        print(f"  [AI Agent 2 & 3] Tạo Hồ sơ Cơ hội: {opp.opportunity_id}")
        print(f"    - NVKD phụ trách: {opp.assigned_rep_name} ({opp.assigned_rep_id})")
        print(f"    - Tổng niêm yết: {opp.subtotal:,.0f} VNĐ | Đề xuất CK: {opp.discount_pct}% -> Sau CK: {opp.final_total:,.0f} VNĐ")
        print(f"    - Phân tích Ngân sách: {opp.budget_evaluation}")
        print(f"    - Khả thi Tồn kho & SLA: {opp.deadline_feasibility}")
        print(f"    - Phê duyệt: {opp.approval_status} (Chiết khấu > 10%: {opp.approval_required})")

        # Step 3: Proposals & Drafts
        drafts = agent.generate_proposals_and_drafts(opp)
        print(f"  [AI Agent 4] Đã tạo Draft Email phản hồi & Docs báo giá!")

        results.append({
            "extracted": asdict(extracted),
            "opportunity": asdict(opp),
            "drafts": drafts
        })

    with open("d:\\AGENT\\pipeline_execution_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(" HOÀN TẤT XỬ LÝ TOÀN BỘ YÊU CẦU. KẾT QUẢ ĐÃ LƯU TẠI pipeline_execution_result.json")
    print("=" * 80)


if __name__ == "__main__":
    run_pipeline()

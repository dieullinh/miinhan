"""
MINH AN TECHNOLOGY SOLUTIONS - FORSHOP MINT MODERN DASHBOARD
Thiết kế lại 100% theo mẫu ForShop với viền ngoài màu XANH MINT NHẠT:
- Khung viền ngoài (Outer Frame) màu Xanh Mint Nhạt (Light Sage/Mint Green: #d8f5e5)
- Thẻ trắng trung tâm bo góc mềm mại (Border-radius: 28px)
- Sidebar phong cách ForShop với thẻ Dashboard màu trắng nổi bật
- Thẻ KPI "Orders" xanh ngọc nhạt và "Profit" hồng đào nhạt
- Biểu đồ đường cong Bezier mềm mại (Sales statistics line chart) kèm tooltip
- Danh sách "Top selling products" bên phải và Thẻ nổi "Unique visitors" góc dưới
- Tương tác 100% đầy đủ: Bóc tách AI, Checkbox tạo Docs, Duyệt TPKD, Gửi khách chốt đơn, Chuyển màu Sáng/Tối
"""

import http.server
import socketserver
import json
import os
import urllib.parse
from datetime import datetime
from dataclasses import asdict

from agent_engine import CatalogService, MinhAnSalesAIAgent, ExtractedInquiry, OpportunityProfile
from gemini_llm import call_gemini_parser, call_gemini_copilot, call_gemini_rewrite_email

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(BASE_DIR, "data", "master_catalog.json")
INQUIRIES_PATH = os.path.join(BASE_DIR, "data", "test_inquiries.json")

user_gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
catalog_service = CatalogService(CATALOG_PATH)
agent = MinhAnSalesAIAgent(catalog_service)
crm_records = []

def generate_ai_assessment(opp: OpportunityProfile) -> str:
    if opp.approval_required:
        return (
            f"💡 [AI Đề xuất]: Mức chiết khấu {opp.discount_pct}% vượt quy chế 10%. "
            f"Giá trị đơn hàng lớn ({opp.subtotal:,.0f} VNĐ). "
            f"Đề xuất Trưởng phòng DUYỆT nếu khách thanh toán tạm ứng 50% hoặc ký hợp đồng tuần này."
        )
    else:
        return (
            f"💡 [AI Đánh giá]: Chiết khấu {opp.discount_pct}% nằm trong quyền tự quyết của NVKD. "
            f"Hồ sơ đã được xác thực mã SKU và kiểm tra tồn kho khả dụng ({opp.deadline_feasibility})."
        )

def init_crm_data():
    global crm_records
    if os.path.exists(INQUIRIES_PATH):
        with open(INQUIRIES_PATH, "r", encoding="utf-8") as f:
            sample_inquiries = json.load(f)
            for inq in sample_inquiries:
                extracted = agent.parse_inquiry_agent(inq)
                opp = agent.validate_and_price_agent(extracted)
                drafts = agent.generate_proposals_and_drafts(opp)
                
                record = {
                    "opp_id": opp.opportunity_id,
                    "customer_name": opp.customer_name,
                    "contact_person": opp.contact_person,
                    "email": opp.email,
                    "phone": opp.phone,
                    "raw_content": inq.get("raw_content", ""),
                    "assigned_rep": f"{opp.assigned_rep_name} ({opp.assigned_rep_id})",
                    "rep_email": opp.assigned_rep_email,
                    "subtotal": opp.subtotal,
                    "discount_pct": opp.discount_pct,
                    "discount_amount": opp.discount_amount,
                    "final_total": opp.final_total,
                    "approval_status": "Chờ Trưởng phòng duyệt" if opp.approval_required else "Đúng thẩm quyền (<=10%)",
                    "lead_time_days": opp.max_lead_time_days,
                    "deadline_feasibility": opp.deadline_feasibility,
                    "ai_assessment": generate_ai_assessment(opp),
                    "checkbox_create_quote": False,
                    "quote_doc_url": "",
                    "items": [asdict(i) for i in opp.items],
                    "drafts": drafts,
                    "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                crm_records.append(record)

init_crm_data()

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Minh An AI Agent - ForShop Mint Modern CRM</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    /* THEME VARIABLES: OUTER MINT GREEN FRAME */
    :root {
      --outer-frame-bg: #d7f4e3;          /* VIỀN XANH MINT NHẠT THAY CHO MÀU TÍM */
      --outer-frame-border: #bbf0d0;
      --sidebar-text: #1b4332;
      --sidebar-text-muted: #40916c;
      --sidebar-active-bg: #ffffff;
      --sidebar-active-text: #081c15;
      --inner-card-bg: #ffffff;
      --inner-border: #f1f5f9;
      --text-dark: #1e293b;
      --text-gray: #64748b;
      --card-orders-bg: #cbf3ee;
      --card-profit-bg: #fedfe8;
      --chart-line-cyan: #38bdf8;
      --chart-line-pink: #f472b6;
      --accent-mint: #10b981;
      --accent-danger: #ef4444;
      --radius-outer: 36px;
      --radius-inner: 28px;
      --radius-card: 20px;
      --radius-pill: 9999px;
      --shadow-inner: 0 20px 45px -10px rgba(0, 0, 0, 0.05);
      --transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    [data-theme="dark"] {
      --outer-frame-bg: #092019;          /* XANH MINT TỐI SANG TRỌNG */
      --outer-frame-border: #133a2e;
      --sidebar-text: #a7f3d0;
      --sidebar-text-muted: #6ee7b7;
      --sidebar-active-bg: #132a22;
      --sidebar-active-text: #ecfdf5;
      --inner-card-bg: #0f172a;
      --inner-border: #1e293b;
      --text-dark: #f8fafc;
      --text-gray: #94a3b8;
      --card-orders-bg: #13332d;
      --card-profit-bg: #331d27;
      --shadow-inner: 0 20px 45px -10px rgba(0, 0, 0, 0.35);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
    body {
      background-color: #f1f5f9;
      color: var(--text-dark);
      padding: 24px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      transition: var(--transition-smooth);
    }
    [data-theme="dark"] body { background-color: #050b14; }

    /* ========================================================
       1. OUTER FRAME: KHUNG VIỀN XANH MINT NHẠT (THAY MÀU TÍM)
    ======================================================== */
    .app-outer-frame {
      width: 100%;
      max-width: 1440px;
      background: var(--outer-frame-bg);
      border: 1px solid var(--outer-frame-border);
      border-radius: var(--radius-outer);
      padding: 24px;
      display: flex;
      gap: 24px;
      box-shadow: 0 25px 60px -15px rgba(16, 185, 129, 0.12);
      transition: var(--transition-smooth);
      position: relative;
    }

    /* ========================================================
       2. SIDEBAR BÊN TRONG VIỀN MINT
    ======================================================== */
    aside.forshop-sidebar {
      width: 220px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 12px 6px;
      flex-shrink: 0;
    }
    .brand-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 32px;
      padding-left: 10px;
    }
    .brand-logo-icon {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: var(--sidebar-text);
      color: var(--outer-frame-bg);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 800;
    }
    .brand-title-text {
      font-size: 19px;
      font-weight: 800;
      color: var(--sidebar-text);
      letter-spacing: -0.5px;
    }

    .sidebar-menu { list-style: none; display: flex; flex-direction: column; gap: 8px; }
    .menu-item a {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 18px;
      border-radius: 14px;
      color: var(--sidebar-text-muted);
      text-decoration: none;
      font-size: 13.5px;
      font-weight: 600;
      transition: var(--transition-smooth);
    }
    .menu-item a:hover {
      background: rgba(255, 255, 255, 0.4);
      color: var(--sidebar-text);
      transform: translateX(3px);
    }
    /* Active State giống trong ảnh ForShop: Thẻ màu trắng nổi bật */
    .menu-item.active a {
      background: var(--sidebar-active-bg);
      color: var(--sidebar-active-text);
      font-weight: 700;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    .menu-item a svg { width: 18px; height: 18px; stroke-width: 2; }

    .sidebar-bottom-actions {
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding-top: 18px;
    }

    /* THEME TOGGLE (LIGHT / DARK) */
    .theme-switch-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px;
      border-radius: var(--radius-pill);
      background: rgba(255, 255, 255, 0.5);
      border: 1px solid rgba(255, 255, 255, 0.8);
      color: var(--sidebar-text);
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      transition: var(--transition-smooth);
    }
    [data-theme="dark"] .theme-switch-btn { background: rgba(0, 0, 0, 0.3); border-color: rgba(255, 255, 255, 0.1); }
    .theme-switch-btn:hover { transform: scale(1.02); }

    /* ========================================================
       3. WHITE MAIN CARD CONTAINER (THẺ TRẮNG BO GÓC TRUNG TÂM)
    ======================================================== */
    main.inner-white-card {
      flex: 1;
      background: var(--inner-card-bg);
      border-radius: var(--radius-inner);
      padding: 36px 40px;
      box-shadow: var(--shadow-inner);
      display: flex;
      flex-direction: column;
      gap: 26px;
      position: relative;
      overflow-y: auto;
      max-height: calc(100vh - 48px);
    }

    /* TOP WELCOME HEADER */
    .inner-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .welcome-title h1 {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.6px;
      color: var(--text-dark);
    }
    .welcome-title p {
      font-size: 13px;
      color: var(--text-gray);
      margin-top: 3px;
    }

    .header-tools {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .search-box-wrap {
      position: relative;
      display: flex;
      align-items: center;
    }
    .search-box-input {
      padding: 9px 16px 9px 36px;
      border-radius: var(--radius-pill);
      background: #f8fafc;
      border: 1px solid var(--inner-border);
      font-size: 12.5px;
      color: var(--text-dark);
      outline: none;
      width: 210px;
      transition: var(--transition-smooth);
    }
    [data-theme="dark"] .search-box-input { background: #1e293b; }
    .search-box-input:focus { width: 250px; border-color: #38bdf8; }
    .search-icon-svg {
      position: absolute;
      left: 12px;
      width: 15px;
      height: 15px;
      color: var(--text-gray);
    }

    .btn-intake-header {
      background: #0f172a;
      color: white;
      padding: 9px 20px;
      border-radius: var(--radius-pill);
      font-size: 13px;
      font-weight: 700;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: var(--transition-smooth);
    }
    [data-theme="dark"] .btn-intake-header { background: #38bdf8; color: #0f172a; }
    .btn-intake-header:hover { transform: translateY(-2px); }

    .user-avatar-circle {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: #fed7aa;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 13px;
      color: #9a3412;
      cursor: pointer;
    }

    /* ========================================================
       4. TOP 2 KPI CARDS (ORDERS & PROFIT STYLE TRONG ẢNH)
    ======================================================== */
    .top-kpis-grid {
      display: grid;
      grid-template-columns: 280px 280px 1fr;
      gap: 20px;
      align-items: center;
    }

    /* CARD 1: ORDERS (XANH NGỌC PASTEL NHƯ ẢNH) */
    .kpi-card-orders {
      background: var(--card-orders-bg);
      border-radius: var(--radius-card);
      padding: 22px 24px;
      display: flex;
      align-items: center;
      gap: 18px;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.03);
      position: relative;
      transition: var(--transition-smooth);
    }
    .kpi-card-orders:hover { transform: translateY(-3px); }
    .orders-icon-circle {
      width: 44px;
      height: 44px;
      background: white;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    }
    [data-theme="dark"] .orders-icon-circle { background: #1e293b; }
    .orders-details h3 {
      font-size: 24px;
      font-weight: 800;
      color: var(--text-dark);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .orders-badge-pill {
      background: #1e1b4b;
      color: white;
      padding: 3px 8px;
      border-radius: var(--radius-pill);
      font-size: 11px;
      font-weight: 800;
    }
    [data-theme="dark"] .orders-badge-pill { background: #38bdf8; color: #0f172a; }
    .orders-details p {
      font-size: 12.5px;
      color: var(--text-gray);
      margin-top: 2px;
      font-weight: 600;
    }

    /* CARD 2: PROFIT (HỒNG ĐÀO PASTEL NHƯ ẢNH) */
    .kpi-card-profit {
      background: var(--card-profit-bg);
      border-radius: var(--radius-card);
      padding: 22px 24px;
      display: flex;
      align-items: center;
      gap: 18px;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.03);
      transition: var(--transition-smooth);
    }
    .kpi-card-profit:hover { transform: translateY(-3px); }
    .profit-details h3 {
      font-size: 20px;
      font-weight: 800;
      color: var(--text-dark);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .profit-details p {
      font-size: 12.5px;
      color: var(--text-gray);
      margin-top: 2px;
      font-weight: 600;
    }

    /* ========================================================
       5. MIDDLE SECTION: SALES STATISTICS + TOP SELLING PRODUCTS
    ======================================================== */
    .analytics-section-grid {
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 32px;
      margin-top: 10px;
    }

    /* BÊN TRÁI: SALES STATISTICS CHART */
    .chart-box-left {
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .chart-title {
      font-size: 17px;
      font-weight: 800;
      color: var(--text-dark);
    }
    .chart-dropdown {
      background: #f8fafc;
      border: 1px solid var(--inner-border);
      color: var(--text-gray);
      padding: 6px 12px;
      border-radius: var(--radius-pill);
      font-size: 12px;
      font-weight: 600;
      outline: none;
    }
    [data-theme="dark"] .chart-dropdown { background: #1e293b; }

    /* SVG BEZIER CURVE CHART NHƯ TRONG ẢNH */
    .svg-chart-container {
      width: 100%;
      height: 250px;
      position: relative;
    }
    .chart-svg {
      width: 100%;
      height: 100%;
      overflow: visible;
    }
    .chart-tooltip-bubble {
      position: absolute;
      top: 92px;
      left: 45%;
      background: #1e1b4b;
      color: white;
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 11.5px;
      font-weight: 800;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
      pointer-events: none;
      animation: float 2.5s ease-in-out infinite;
    }
    [data-theme="dark"] .chart-tooltip-bubble { background: #38bdf8; color: #0f172a; }
    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }

    /* BÊN PHẢI: TOP SELLING PRODUCTS */
    .top-products-right {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .top-products-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .top-products-head h3 { font-size: 15px; font-weight: 800; }
    .see-all-link { font-size: 12px; font-weight: 700; color: #38bdf8; text-decoration: none; cursor: pointer; }

    .product-list { display: flex; flex-direction: column; gap: 14px; }
    .product-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 10px;
      border-radius: 12px;
      transition: var(--transition-smooth);
    }
    .product-item:hover { background: #f8fafc; }
    [data-theme="dark"] .product-item:hover { background: #1e293b; }
    .product-left-info { display: flex; align-items: center; gap: 12px; }
    .product-index { font-size: 12px; font-weight: 700; color: var(--text-gray); width: 14px; }
    .product-icon-box {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: #f1f5f9;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
    }
    [data-theme="dark"] .product-icon-box { background: #1e293b; }
    .product-title-txt { font-size: 13px; font-weight: 700; color: var(--text-dark); }
    .product-sub-txt { font-size: 11px; color: var(--text-gray); }
    .product-price-txt { font-size: 13px; font-weight: 800; color: var(--text-dark); }

    /* ========================================================
       6. UNIQUE VISITORS OVERLAPPING WIDGET (GÓC DƯỚI PHẢI NHƯ ẢNH)
    ======================================================== */
    .widget-unique-visitors {
      background: var(--inner-card-bg);
      border: 1px solid var(--inner-border);
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
      position: absolute;
      bottom: 24px;
      right: 40px;
      width: 380px;
      z-index: 10;
    }
    .widget-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .widget-head h4 { font-size: 15px; font-weight: 800; }

    /* ========================================================
       7. FULL CRM TABLE SECTION (GOOGLE SHEETS INTEGRATION)
    ======================================================== */
    .crm-section-area {
      margin-top: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      border-top: 1px solid var(--inner-border);
      padding-top: 24px;
    }
    .crm-table-container {
      overflow-x: auto;
      border-radius: 16px;
      border: 1px solid var(--inner-border);
      max-height: 420px;
    }
    table { width: 100%; border-collapse: collapse; font-size: 12.5px; text-align: left; }
    th {
      background: #f8fafc;
      color: var(--text-gray);
      font-weight: 700;
      padding: 12px 14px;
      border-bottom: 1px solid var(--inner-border);
      white-space: nowrap;
      position: sticky;
      top: 0;
      z-index: 5;
    }
    [data-theme="dark"] th { background: #1e293b; }
    td {
      padding: 12px 14px;
      border-bottom: 1px solid var(--inner-border);
      vertical-align: middle;
      white-space: nowrap;
    }
    tr:hover { background: rgba(0, 0, 0, 0.02); }

    .checkbox-quote { width: 18px; height: 18px; cursor: pointer; accent-color: #38bdf8; }
    .badge-status {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;
    }
    .badge-pending { background: #fef3c7; color: #b45309; }
    .badge-approved { background: #dcfce7; color: #15803d; }
    .badge-rejected { background: #fee2e2; color: #b91c1c; }
    .badge-done { background: #f1f5f9; color: #475569; }
    [data-theme="dark"] .badge-done { background: #1e293b; color: #94a3b8; }

    .btn-sm-action {
      padding: 5px 10px; border-radius: 6px; font-size: 11.5px; font-weight: 700;
      border: none; cursor: pointer; transition: var(--transition-smooth);
    }
    .btn-approve { background: var(--accent-mint); color: white; }
    .btn-reject { background: var(--accent-danger); color: white; margin-left: 4px; }
    .btn-send { background: #0f172a; color: white; }
    [data-theme="dark"] .btn-send { background: #38bdf8; color: #0f172a; }
    .btn-view { background: #f1f5f9; color: #334155; margin-left: 4px; }
    [data-theme="dark"] .btn-view { background: #1e293b; color: #cbd5e1; }

    /* ========================================================
       8. FLOATING AI COPILOT CHATBOT
    ======================================================== */
    .ai-bubble-bot {
      position: fixed; bottom: 26px; right: 28px; z-index: 100;
      width: 56px; height: 56px; border-radius: 50%;
      background: linear-gradient(135deg, #10b981, #059669);
      color: white; display: flex; align-items: center; justify-content: center;
      font-size: 26px; box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
      cursor: pointer; transition: var(--transition-smooth);
    }
    .ai-bubble-bot:hover { transform: scale(1.1); }

    .ai-chat-drawer {
      display: none; position: fixed; bottom: 94px; right: 28px; z-index: 105;
      width: 370px; height: 500px; background: var(--inner-card-bg); border-radius: 20px;
      border: 1px solid var(--inner-border); box-shadow: 0 20px 45px rgba(0,0,0,0.18);
      flex-direction: column; overflow: hidden;
    }
    .ai-drawer-head {
      background: var(--outer-frame-bg); color: var(--sidebar-text); padding: 14px 18px;
      display: flex; justify-content: space-between; align-items: center; font-weight: 800;
    }
    .ai-drawer-messages {
      flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px;
      background: #f8fafc;
    }
    [data-theme="dark"] .ai-drawer-messages { background: #0b1120; }
    .ai-chat-bubble { max-width: 85%; padding: 10px 14px; border-radius: 12px; font-size: 12px; line-height: 1.45; }
    .ai-bubble-assistant { background: var(--inner-card-bg); color: var(--text-dark); border: 1px solid var(--inner-border); align-self: flex-start; }
    .ai-bubble-user { background: #0f172a; color: white; align-self: flex-end; }
    [data-theme="dark"] .ai-bubble-user { background: #38bdf8; color: #0f172a; }
    .ai-chat-footer {
      padding: 10px 14px; background: var(--inner-card-bg); border-top: 1px solid var(--inner-border); display: flex; gap: 8px;
    }
    .ai-input-txt {
      flex: 1; padding: 8px 12px; border-radius: var(--radius-pill); border: 1px solid var(--inner-border);
      outline: none; font-size: 12.5px; background: #f8fafc; color: var(--text-dark);
    }
    [data-theme="dark"] .ai-input-txt { background: #1e293b; }

    /* ========================================================
       9. MODALS
    ======================================================== */
    .modal-overlay {
      display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.55);
      backdrop-filter: blur(5px); z-index: 200; align-items: center; justify-content: center; padding: 20px;
    }
    .modal-content-card {
      background: var(--inner-card-bg); border-radius: 24px; width: 100%;
      max-width: 800px; max-height: 90vh; overflow-y: auto; padding: 30px;
      box-shadow: 0 25px 50px rgba(0,0,0,0.25); border: 1px solid var(--inner-border);
    }
    .modal-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; border-bottom: 1px solid var(--inner-border); padding-bottom: 12px; }
    .modal-close-icon { font-size: 24px; cursor: pointer; border: none; background: none; color: var(--text-gray); }
    .input-field {
      width: 100%; padding: 10px 14px; border: 1px solid var(--inner-border);
      border-radius: 10px; font-size: 13px; margin-top: 4px; margin-bottom: 14px;
      background: #f8fafc; color: var(--text-dark); outline: none;
    }
    [data-theme="dark"] .input-field { background: #1e293b; }
    .code-box-view {
      background: #f8fafc; border: 1px solid var(--inner-border); border-radius: 12px;
      padding: 16px; font-family: monospace; font-size: 12.5px; white-space: pre-wrap;
      line-height: 1.45; max-height: 360px; overflow-y: auto; color: var(--text-dark);
    }
    [data-theme="dark"] .code-box-view { background: #1e293b; }
  </style>
</head>
<body data-theme="light">

  <!-- ========================================================
       APP OUTER FRAME: KHUNG VIỀN XANH MINT NHẠT (#d7f4e3)
  ======================================================== -->
  <div class="app-outer-frame">

    <!-- 1. FORSHOP STYLE SIDEBAR BÊN TRONG VIỀN MINT -->
    <aside class="forshop-sidebar">
      <div>
        <div class="brand-header">
          <div class="brand-logo-icon">⊙</div>
          <div class="brand-title-text">Minh An AI</div>
        </div>

        <ul class="sidebar-menu">
          <li class="menu-item active" id="menu-dash">
            <a href="javascript:void(0)" onclick="switchTab('dashboard')">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
              Dashboard
            </a>
          </li>
          <li class="menu-item" id="menu-orders">
            <a href="javascript:void(0)" onclick="switchTab('crm-orders')">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              Hồ sơ CRM
            </a>
          </li>
          <li class="menu-item" id="menu-products">
            <a href="javascript:void(0)" onclick="switchTab('products')">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
              Kho & Bảng giá
            </a>
          </li>
          <li class="menu-item" id="menu-marketing">
            <a href="javascript:void(0)" onclick="openIntakeModal()">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"/></svg>
              Bóc tách AI
            </a>
          </li>
          <li class="menu-item" id="menu-reports">
            <a href="/api/export_csv">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
              Xuất File CSV
            </a>
          </li>
        </ul>
      </div>

      <!-- SIDEBAR BOTTOM: THEME SWITCHER -->
      <div class="sidebar-bottom-actions">
        <button class="theme-switch-btn" onclick="toggleTheme()" id="theme-btn" title="Chuyển chế độ Sáng / Tối">
          🌙 Chế độ Tối
        </button>
      </div>
    </aside>

    <!-- 2. MAIN INNER WHITE CARD CONTAINER -->
    <main class="inner-white-card">

      <!-- TOP WELCOME HEADER (FORSHOP STYLE) -->
      <header class="inner-header">
        <div class="welcome-title">
          <h1>Welcome, Trưởng phòng KD</h1>
          <p>Hệ thống AI Agent tự động hóa xử lý Yêu cầu & Báo giá B2B Minh An</p>
        </div>

        <div class="header-tools">
          <div class="search-box-wrap">
            <svg class="search-icon-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            <input type="text" class="search-box-input" placeholder="Search for products...">
          </div>

          <button class="btn-intake-header" onclick="openIntakeModal()">
            <span>+</span> Tiếp nhận Y/C mới
          </button>

          <div class="user-avatar-circle" title="Tài khoản Quản lý">TP</div>
        </div>
      </header>

      <!-- VIEW 1: DASHBOARD FORSHOP (CHÍNH) -->
      <div id="view-dashboard-section">
        
        <!-- TOP 2 KPI CARDS (ORDERS & PROFIT STYLE TRONG ẢNH) -->
        <div class="top-kpis-grid">
          
          <!-- CARD 1: ORDERS (XANH NGỌC PASTEL) -->
          <div class="kpi-card-orders">
            <div class="orders-icon-circle">📄</div>
            <div class="orders-details">
              <h3>23 789 <span class="orders-badge-pill">+20</span></h3>
              <p>Yêu cầu tuần này (Orders)</p>
            </div>
          </div>

          <!-- CARD 2: PROFIT (HỒNG ĐÀO PASTEL) -->
          <div class="kpi-card-profit">
            <div class="orders-icon-circle" style="background:#fbcfe8;">💰</div>
            <div class="profit-details">
              <h3>$ 12 890,89 <span class="orders-badge-pill" style="background:#0f172a;">+$ 840</span></h3>
              <p>Doanh thu & Chiết khấu (Profit)</p>
            </div>
          </div>

          <div style="text-align:right;">
            <button class="btn-intake-header" style="background:var(--accent-mint); color:white; display:inline-flex;" onclick="switchTab('crm-orders')">
              📊 Xem Bảng Google Sheets
            </button>
          </div>

        </div>

        <!-- MIDDLE ANALYTICS: SALES STATISTICS & TOP SELLING PRODUCTS -->
        <div class="analytics-section-grid">
          
          <!-- BÊN TRÁI: SALES STATISTICS BEZIER LINE CHART -->
          <div class="chart-box-left">
            <div class="chart-header">
              <div class="chart-title">Sales statistics</div>
              <select class="chart-dropdown">
                <option>Monthly</option>
                <option>Weekly</option>
              </select>
            </div>

            <!-- SVG BEZIER SPLINE CHART GIỐNG ẢNH MẪU -->
            <div class="svg-chart-container">
              <svg class="chart-svg" viewBox="0 0 600 240">
                <!-- Grid Lines -->
                <line x1="40" y1="20" x2="580" y2="20" stroke="#f1f5f9" stroke-dasharray="4"/>
                <line x1="40" y1="80" x2="580" y2="80" stroke="#f1f5f9" stroke-dasharray="4"/>
                <line x1="40" y1="140" x2="580" y2="140" stroke="#f1f5f9" stroke-dasharray="4"/>
                <line x1="40" y1="200" x2="580" y2="200" stroke="#f1f5f9"/>

                <!-- Y Axis Labels -->
                <text x="15" y="25" fill="#94a3b8" font-size="11" font-weight="600">100</text>
                <text x="15" y="85" fill="#94a3b8" font-size="11" font-weight="600">80</text>
                <text x="15" y="145" fill="#94a3b8" font-size="11" font-weight="600">60</text>
                <text x="15" y="205" fill="#94a3b8" font-size="11" font-weight="600">40</text>

                <!-- Smooth Pink Spline Line -->
                <path d="M 50 190 C 150 180, 220 140, 310 130 C 400 120, 480 60, 560 50" fill="none" stroke="var(--chart-line-pink)" stroke-width="2.5"/>

                <!-- Smooth Cyan Spline Line -->
                <path d="M 50 210 C 150 200, 220 160, 310 150 C 400 140, 480 90, 560 70" fill="none" stroke="var(--chart-line-cyan)" stroke-width="2.5"/>

                <!-- Data Dots -->
                <circle cx="50" cy="190" r="4" fill="#1e1b4b"/>
                <circle cx="210" cy="155" r="4" fill="#1e1b4b"/>
                <circle cx="310" cy="130" r="4" fill="#1e1b4b"/>
                <circle cx="450" cy="85" r="4" fill="#1e1b4b"/>
                <circle cx="560" cy="50" r="4" fill="#1e1b4b"/>

                <!-- X Axis Labels -->
                <text x="180" y="225" fill="#94a3b8" font-size="11" font-weight="600">Week 1</text>
                <text x="320" y="225" fill="#94a3b8" font-size="11" font-weight="600">Week 2</text>
                <text x="460" y="225" fill="#94a3b8" font-size="11" font-weight="600">Week 3</text>
              </svg>

              <!-- Interactive Floating Tooltip Bubble -->
              <div class="chart-tooltip-bubble">
                <span style="font-size:9px; color:#cbd5e1; display:block;">10.06 - 17.06.2026</span>
                $ 7 320,89 (Đã duyệt)
              </div>
            </div>
          </div>

          <!-- BÊN PHẢI: TOP SELLING PRODUCTS -->
          <div class="top-products-right">
            <div class="top-products-head">
              <h3>Top selling products</h3>
              <a class="see-all-link" onclick="switchTab('products')">See all &gt;</a>
            </div>

            <div class="product-list">
              <div class="product-item">
                <div class="product-left-info">
                  <span class="product-index">1</span>
                  <div class="product-icon-box">🖥️</div>
                  <div>
                    <div class="product-title-txt">Dell PowerEdge R750xs</div>
                    <div class="product-sub-txt">Tồn khả dụng: 4 chiếc</div>
                  </div>
                </div>
                <div class="product-price-txt">85.0M ₫</div>
              </div>

              <div class="product-item">
                <div class="product-left-info">
                  <span class="product-index">2</span>
                  <div class="product-icon-box">🌐</div>
                  <div>
                    <div class="product-title-txt">Cisco Catalyst C9200L</div>
                    <div class="product-sub-txt">Tồn khả dụng: 12 chiếc</div>
                  </div>
                </div>
                <div class="product-price-txt">28.5M ₫</div>
              </div>

              <div class="product-item">
                <div class="product-left-info">
                  <span class="product-index">3</span>
                  <div class="product-icon-box">📶</div>
                  <div>
                    <div class="product-title-txt">Aruba Instant On AP22</div>
                    <div class="product-sub-txt">Tồn khả dụng: 35 chiếc</div>
                  </div>
                </div>
                <div class="product-price-txt">3.8M ₫</div>
              </div>

              <div class="product-item">
                <div class="product-left-info">
                  <span class="product-index">4</span>
                  <div class="product-icon-box">🛡️</div>
                  <div>
                    <div class="product-title-txt">Fortinet FortiGate 60F</div>
                    <div class="product-sub-txt" style="color:var(--accent-danger);">Tồn kho: 0 (SLA 10 ngày)</div>
                  </div>
                </div>
                <div class="product-price-txt">19.5M ₫</div>
              </div>
            </div>
          </div>

        </div>

        <!-- FLOATING OVERLAPPING WIDGET (UNIQUE VISITORS GIỐNG ẢNH MẪU) -->
        <div class="widget-unique-visitors">
          <div class="widget-head">
            <h4>Unique visitors</h4>
            <select class="chart-dropdown" style="padding:4px 8px; font-size:11px;">
              <option>Weekly</option>
            </select>
          </div>
          <div style="font-size:11px; color:var(--text-gray); margin-bottom:8px;">50K &nbsp; 25K</div>
          <svg viewBox="0 0 340 70" style="width:100%; height:60px;">
            <path d="M 10 30 Q 50 65, 90 25 T 170 50 T 250 20 T 330 45" fill="none" stroke="#6366f1" stroke-width="2.5"/>
            <circle cx="10" cy="30" r="3.5" fill="#4338ca"/>
            <circle cx="90" cy="25" r="3.5" fill="#4338ca"/>
            <circle cx="170" cy="50" r="3.5" fill="#4338ca"/>
            <circle cx="250" cy="20" r="3.5" fill="#4338ca"/>
            <circle cx="330" cy="45" r="3.5" fill="#4338ca"/>
          </svg>
          <div style="display:flex; justify-content:space-between; font-size:10px; color:#94a3b8; font-weight:700; margin-top:4px;">
            <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
          </div>
        </div>

      </div>

      <!-- VIEW 2: FULL CRM GOOGLE SHEETS TABLE -->
      <div id="view-crm-section" class="crm-section-area">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h2 style="font-size:18px; font-weight:800;">Bảng Hồ sơ Cơ hội (Google Sheets)</h2>
            <p style="font-size:12px; color:var(--text-gray);">Xử lý duyệt chiết khấu 10%, tích Checkbox tạo Docs và gửi URL cho khách</p>
          </div>
          <div style="display:flex; gap:8px;">
            <a href="/api/export_csv" class="btn-intake-header" style="background:#2563eb; padding:7px 14px; font-size:12px;">📥 Xuất CSV</a>
            <button class="btn-intake-header" style="padding:7px 14px; font-size:12px;" onclick="fetchData()">🔄 Làm mới</button>
          </div>
        </div>

        <div class="crm-table-container">
          <table>
            <thead>
              <tr>
                <th>Mã Cơ hội</th>
                <th>Khách hàng</th>
                <th>NVKD Phụ trách</th>
                <th>Tổng Niêm Yết</th>
                <th>Chiết khấu (%)</th>
                <th>Sau Chiết khấu</th>
                <th>Trạng thái Phê duyệt</th>
                <th>Tiến độ SLA</th>
                <th style="text-align:center; background:#fef9c3;">Checkbox "Tạo báo giá"</th>
                <th>URL Docs Báo giá</th>
                <th>Hành động</th>
              </tr>
            </thead>
            <tbody id="crm-table-body"></tbody>
          </table>
        </div>
      </div>

      <!-- VIEW 3: PRODUCTS & STOCK VIEW -->
      <div id="view-products-section" class="crm-section-area" style="display:none;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h2 style="font-size:18px; font-weight:800;">Master Catalog & Tồn kho SLA</h2>
            <p style="font-size:12px; color:var(--text-gray);">Bảng giá niêm yết hiện hành và năng lực đáp ứng của kho Minh An</p>
          </div>
        </div>
        <div class="crm-table-container">
          <table>
            <thead>
              <tr><th>Mã SKU</th><th>Tên Thiết bị</th><th>Phân loại</th><th>Giá niêm yết</th><th>Tồn kho</th><th>SLA Sẵn hàng</th><th>SLA Hết hàng</th></tr>
            </thead>
            <tbody id="catalog-table-body"></tbody>
          </table>
        </div>
      </div>

    </main>

  </div>

  <!-- FLOATING AI COPILOT CHATBOT -->
  <div class="ai-bubble-bot" onclick="toggleAiDrawer()" title="Hỏi Trợ lý AI Minh An">
    🤖
  </div>

  <div class="ai-chat-drawer" id="ai-chat-drawer">
    <div class="ai-drawer-head">
      <span>🤖 Minh An AI Copilot</span>
      <button onclick="toggleAiDrawer()" style="background:none; border:none; font-size:18px; cursor:pointer; color:inherit;">&times;</button>
    </div>
    <div class="ai-drawer-messages" id="ai-chat-history">
      <div class="ai-chat-bubble ai-bubble-assistant">
        Xin chào! Tôi là Trợ lý AI Bán hàng B2B của Minh An. Tôi có thể tư vấn tồn kho, thẩm định chiết khấu vượt thẩm quyền và hỗ trợ bạn chốt đơn.
      </div>
    </div>
    <div class="ai-chat-footer">
      <input type="text" class="ai-input-txt" id="ai-query-input" placeholder="Hỏi AI bất kỳ điều gì..." onkeydown="if(event.key==='Enter') sendAiMessage()">
      <button class="btn-intake-header" style="padding:6px 12px; font-size:12px;" onclick="sendAiMessage()">Gửi</button>
    </div>
  </div>

  <!-- MODAL: INTAKE YÊU CẦU MỚI -->
  <div class="modal-overlay" id="modal-intake">
    <div class="modal-content-card">
      <div class="modal-header-row">
        <h3 style="font-size:17px; font-weight:800;">⚡ Tiếp nhận & Bóc tách Yêu cầu (AI Agent)</h3>
        <button class="modal-close-icon" onclick="closeIntakeModal()">&times;</button>
      </div>

      <label style="font-size:12px; font-weight:700; color:var(--text-gray);">Chọn nhanh kịch bản kiểm thử:</label>
      <select class="input-field" id="intake-preset" onchange="applyPreset()">
        <option value="">-- Tự nhập email hoặc chọn tình huống mẫu --</option>
        <option value="p1">Kịch bản 1: LogiTech (Yêu cầu CK 12% > 10% - Cần TPKD duyệt)</option>
        <option value="p2">Kịch bản 2: May Mặc Hưng Phát (CK 5% <= 10% - Hết hàng tồn, đòi gấp 3 ngày)</option>
        <option value="p3">Kịch bản 3: BĐS Thịnh Vượng (Đơn lớn 5 Server - Kho chỉ có 4, CK 15%)</option>
      </select>

      <label style="font-size:12px; font-weight:700; color:var(--text-gray);">Tên Doanh nghiệp Khách hàng:</label>
      <input type="text" class="input-field" id="intake-company" placeholder="VD: Công ty Cổ phần Giải pháp LogiTech">

      <label style="font-size:12px; font-weight:700; color:var(--text-gray);">Người liên hệ & SĐT / Email:</label>
      <input type="text" class="input-field" id="intake-contact" placeholder="VD: Anh Trần Tuấn - TP IT (0912345678, tuan.tran@logitech-vn.example)">

      <label style="font-size:12px; font-weight:700; color:var(--text-gray);">Nội dung Yêu cầu chi tiết (Email / Biểu mẫu):</label>
      <textarea class="input-field" id="intake-content" rows="6" placeholder="Dán nội dung email yêu cầu của khách hàng vào đây..."></textarea>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:10px;">
        <button class="btn-sm-action btn-view" onclick="closeIntakeModal()">Hủy</button>
        <button class="btn-intake-header" onclick="submitInquiry()">
          <span>⚡</span> Khởi chạy AI Bóc Tách
        </button>
      </div>
    </div>
  </div>

  <!-- MODAL: XEM BÁO GIÁ & DRAFT EMAIL -->
  <div class="modal-overlay" id="modal-preview">
    <div class="modal-content-card">
      <div class="modal-header-row">
        <h3 id="preview-modal-title" style="font-size:17px; font-weight:800;">Hồ sơ Báo giá</h3>
        <button class="modal-close-icon" onclick="closePreviewModal()">&times;</button>
      </div>

      <div style="background:var(--card-orders-bg); border-radius:10px; padding:12px 16px; margin-bottom:14px; font-size:12.5px; font-weight:600;" id="preview-ai-reasoning">
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
        <div style="display:flex; gap:8px;">
          <button class="btn-sm-action btn-view" id="tab-btn-email" onclick="showPreviewTab('email')">📧 Email gửi Khách</button>
          <button class="btn-sm-action btn-view" id="tab-btn-manager" onclick="showPreviewTab('manager')">📩 Email Trình TPKD</button>
          <button class="btn-sm-action btn-view" id="tab-btn-doc" onclick="showPreviewTab('doc')">📄 Google Docs Báo giá</button>
        </div>
        <div style="display:flex; gap:6px;">
          <button class="btn-sm-action" style="background:#fef3c7; color:#92400e;" onclick="rewriteEmailWithAi('negotiate')">🤖 AI Tối ưu Đàm phán</button>
          <button class="btn-sm-action" style="background:#e0f2fe; color:#0369a1;" onclick="printQuotation()">🖨️ In Báo Giá</button>
        </div>
      </div>

      <div class="code-box-view" id="preview-content-box"></div>

      <div style="margin-top:16px; display:flex; justify-content:flex-end; gap:10px;">
        <button class="btn-sm-action btn-view" onclick="copyPreviewText()">📋 Sao chép</button>
        <button class="btn-intake-header" onclick="closePreviewModal()">Đóng</button>
      </div>
    </div>
  </div>

  <!-- JAVASCRIPT LOGIC -->
  <script>
    let crmData = [];
    let catalogData = [];
    let activeRecord = null;

    // THEME ENGINE
    function initTheme() {
      const saved = localStorage.getItem('forshop_theme') || 'light';
      document.body.setAttribute('data-theme', saved);
      updateThemeBtn(saved);
    }

    function toggleTheme() {
      const current = document.body.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.body.setAttribute('data-theme', next);
      localStorage.setItem('forshop_theme', next);
      updateThemeBtn(next);
    }

    function updateThemeBtn(t) {
      document.getElementById('theme-btn').innerText = t === 'dark' ? '☀️ Chế độ Sáng' : '🌙 Chế độ Tối';
    }

    initTheme();

    const presets = {
      p1: {
        company: "Công ty Cổ phần Giải pháp LogiTech",
        contact: "Anh Trần Tuấn - Trưởng phòng IT (0912345678, tuan.tran@logitech-vn.example)",
        content: `Chào Minh An,\nCông ty tôi đang cần trang bị hạ tầng mạng cho văn phòng chi nhánh mới tại Q7 gồm:\n- 1 máy chủ Dell R750xs cấu hình chuẩn\n- 2 chiếc Switch Cisco 24 cổng PoE mã C9200L\n- 6 bộ phát wifi Aruba AP22 treo trần\n- 1 bộ lưu điện APC 3kVA\n- Kèm dịch vụ lắp đặt triển khai trọn gói.\n\nTổng ngân sách dự trù bên tôi khoảng 200 triệu. Yêu cầu bàn giao và nghiệm thu xong trước ngày 20/11/2026 (sau 10 ngày). Do bên tôi là khách hàng quen, đề xuất chiết khấu thêm 12% so với giá niêm yết để kịp trình ban giám đốc ký duyệt tuần này.\nBáo sớm giúp mình nhé!\nTuấn - IT Manager.`
      },
      p2: {
        company: "Công ty TNHH May Mặc Hưng Phát",
        contact: "Chị Mai Hương - Kế toán trưởng (0988776655, huong.mai@hungphatgarment.example)",
        content: `Cần báo giá gấp 2 con Firewall Fortinet 60F và 4 con Wifi Aruba AP22. Cần hàng gấp trong 3 ngày để lắp nhà xưởng. Chiết khấu thương mại mong muốn 5%.`
      },
      p3: {
        company: "Tập đoàn Bất động sản Thịnh Vượng",
        contact: "Anh Hoàng Nam - Giám đốc Công nghệ (0903332211, nam.hoang@thinhvuongland.example)",
        content: `Gửi báo giá gấp cho tôi 5 Máy chủ Dell R750xs và 10 Switch Cisco C9200L cho phòng máy Data Center mới. Thời hạn bàn giao cần trong 7 ngày. Yêu cầu chiết khấu 15% cho đơn lớn.`
      }
    };

    function applyPreset() {
      const k = document.getElementById('intake-preset').value;
      if (presets[k]) {
        document.getElementById('intake-company').value = presets[k].company;
        document.getElementById('intake-contact').value = presets[k].contact;
        document.getElementById('intake-content').value = presets[k].content;
      }
    }

    async function fetchData() {
      try {
        const res = await fetch('/api/crm_records');
        crmData = await res.json();
        renderTable();
      } catch (e) { console.error(e); }
    }

    async function fetchCatalog() {
      try {
        const res = await fetch('/api/catalog');
        const cat = await res.json();
        catalogData = cat.products;
        renderCatalogTable();
      } catch (e) { console.error(e); }
    }

    function renderTable() {
      const tbody = document.getElementById('crm-table-body');
      tbody.innerHTML = '';
      crmData.forEach((row, idx) => {
        const tr = document.createElement('tr');
        let statusBadge = '';
        if (row.approval_status.includes('Chờ Trưởng phòng')) statusBadge = '<span class="badge-status badge-pending">⏳ Chờ TPKD duyệt</span>';
        else if (row.approval_status.includes('Đã duyệt')) statusBadge = '<span class="badge-status badge-approved">✔️ Đã duyệt</span>';
        else if (row.approval_status.includes('Đúng thẩm quyền')) statusBadge = '<span class="badge-status badge-approved">✔️ Đúng thẩm quyền</span>';
        else if (row.approval_status.includes('Từ chối')) statusBadge = '<span class="badge-status badge-rejected">❌ Hoàn thành (Từ chối)</span>';
        else if (row.approval_status.includes('Chốt đơn')) statusBadge = '<span class="badge-status badge-done">🏁 Chốt đơn / Hoàn tất</span>';

        const canCheck = (row.approval_status.includes('Đã duyệt') || row.approval_status.includes('Đúng thẩm quyền')) && !row.approval_status.includes('Từ chối');
        const isChecked = row.checkbox_create_quote ? 'checked' : '';

        let docLink = '<span style="color:var(--text-gray); font-style:italic;">Chưa tạo</span>';
        if (row.quote_doc_url) docLink = `<a href="javascript:void(0)" onclick="openPreviewModal(${idx}, 'doc')" style="color:#2563eb; font-weight:700;">📄 Docs_${row.opp_id}</a>`;

        let actionBtns = '';
        if (row.approval_status.includes('Chờ Trưởng phòng')) {
          actionBtns = `
            <button class="btn-sm-action btn-approve" onclick="managerDecision('${row.opp_id}', 'approve')">Đồng ý</button>
            <button class="btn-sm-action btn-reject" onclick="managerDecision('${row.opp_id}', 'reject')">Từ chối</button>
          `;
        } else if (row.quote_doc_url && !row.approval_status.includes('Chốt đơn')) {
          actionBtns = `<button class="btn-sm-action btn-send" onclick="sendQuote('${row.opp_id}')">📨 Gửi Khách</button>`;
        }
        actionBtns += `<button class="btn-sm-action btn-view" onclick="openPreviewModal(${idx}, 'email')">Xem</button>`;

        const leadWarn = row.deadline_feasibility.includes('CẢNH BÁO')
          ? `<span style="color:#d97706; font-weight:700;" title="${row.deadline_feasibility}">⚠️ ${row.lead_time_days} ngày (Kho thiếu)</span>`
          : `<span>${row.lead_time_days} ngày làm việc</span>`;

        tr.innerHTML = `
          <td><b>${row.opp_id}</b></td>
          <td><b>${row.customer_name}</b><br><small style="color:var(--text-gray);">${row.contact_person}</small></td>
          <td>${row.assigned_rep}</td>
          <td>${row.subtotal.toLocaleString('vi-VN')} ₫</td>
          <td><b style="color:${row.discount_pct > 10 ? 'red' : 'inherit'}">${row.discount_pct}%</b></td>
          <td><b>${row.final_total.toLocaleString('vi-VN')} ₫</b></td>
          <td>${statusBadge}</td>
          <td>${leadWarn}</td>
          <td style="text-align:center;">
            <input type="checkbox" class="checkbox-quote" ${isChecked} ${canCheck ? '' : 'disabled'} onchange="toggleQuoteCheckbox('${row.opp_id}', this.checked)">
          </td>
          <td>${docLink}</td>
          <td style="white-space:nowrap;">${actionBtns}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    function renderCatalogTable() {
      const tbody = document.getElementById('catalog-table-body');
      tbody.innerHTML = '';
      catalogData.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><b>${p.sku}</b></td><td>${p.name}</td><td><span class="badge-status badge-done">${p.category}</span></td>
          <td>${p.unit_price.toLocaleString('vi-VN')} ₫</td><td><b>${p.stock_available} chiếc</b></td>
          <td>${p.lead_time_in_stock_days} ngày</td><td>${p.lead_time_out_stock_days} ngày</td>
        `;
        tbody.appendChild(tr);
      });
    }

    function switchTab(t) {
      document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
      const dashSec = document.getElementById('view-dashboard-section');
      const crmSec = document.getElementById('view-crm-section');
      const prodSec = document.getElementById('view-products-section');

      if (t === 'dashboard') {
        document.getElementById('menu-dash').classList.add('active');
        dashSec.style.display = 'block';
        crmSec.style.display = 'block';
        prodSec.style.display = 'none';
      } else if (t === 'crm-orders') {
        document.getElementById('menu-orders').classList.add('active');
        dashSec.style.display = 'none';
        crmSec.style.display = 'block';
        prodSec.style.display = 'none';
        crmSec.scrollIntoView({ behavior: 'smooth' });
      } else if (t === 'products') {
        document.getElementById('menu-products').classList.add('active');
        dashSec.style.display = 'none';
        crmSec.style.display = 'none';
        prodSec.style.display = 'block';
      }
    }

    function openIntakeModal() { document.getElementById('modal-intake').style.display = 'flex'; }
    function closeIntakeModal() { document.getElementById('modal-intake').style.display = 'none'; }

    async function submitInquiry() {
      const company = document.getElementById('intake-company').value.trim();
      const contact = document.getElementById('intake-contact').value.trim();
      const content = document.getElementById('intake-content').value.trim();
      if (!content) return alert("Vui lòng nhập nội dung yêu cầu!");

      try {
        const payload = {
          id: "INQ-" + new Date().getTime().toString().slice(-4),
          customer: { company_name: company || "Khách hàng Doanh nghiệp", contact_person: contact },
          raw_content: content
        };
        const res = await fetch('/api/process_inquiry', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        closeIntakeModal();
        await fetchData();
        switchTab('crm-orders');
        alert(`AI Agent đã bóc tách thành công!\nMã cơ hội: ${data.opp_id}\nChiết khấu: ${data.discount_pct}%\nTrạng thái: ${data.approval_status}`);
      } catch (e) { alert("Lỗi: " + e.message); }
    }

    async function managerDecision(oppId, decision) {
      if (!confirm(`Xác nhận ${decision === 'approve' ? 'ĐỒNG Ý DUYỆT' : 'TỪ CHỐI'} chiết khấu này?`)) return;
      await fetch('/api/manager_decision', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ opp_id: oppId, decision: decision })
      });
      await fetchData();
    }

    async function toggleQuoteCheckbox(oppId, isChecked) {
      if (!isChecked) return;
      const res = await fetch('/api/trigger_create_quote', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ opp_id: oppId })
      });
      const data = await res.json();
      alert(`Đã nhân bản Google Docs thành công!\nURL Báo giá: ${data.doc_url}`);
      await fetchData();
    }

    async function sendQuote(oppId) {
      if (!confirm("Gửi email kèm URL Báo giá Google Docs cho Khách hàng để chốt đơn?")) return;
      await fetch('/api/complete_deal', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ opp_id: oppId })
      });
      alert("Đã gửi email thành công!\nTrạng thái: Chốt đơn / Hoàn tất.");
      await fetchData();
    }

    function openPreviewModal(index, tab) {
      activeRecord = crmData[index];
      document.getElementById('preview-modal-title').innerText = `Hồ sơ ${activeRecord.opp_id} - ${activeRecord.customer_name}`;
      document.getElementById('preview-ai-reasoning').innerText = activeRecord.ai_assessment || "💡 AI đã xác thực đối soát bảng giá và tồn kho khả dụng thành công.";
      showPreviewTab(tab);
      document.getElementById('modal-preview').style.display = 'flex';
    }

    function closePreviewModal() { document.getElementById('modal-preview').style.display = 'none'; }

    function showPreviewTab(tab) {
      const box = document.getElementById('preview-content-box');
      if (tab === 'email') box.innerText = activeRecord.drafts.customer_email_draft;
      else if (tab === 'manager') box.innerText = activeRecord.drafts.manager_approval_email || "(Mức chiết khấu <= 10%, thuộc quyền NVKD tự quyết)";
      else if (tab === 'doc') {
        let content = `BẢNG BÁO GIÁ THIẾT BỊ VÀ DỊCH VỤ CÔNG NGHỆ\n` +
          `Mã Báo Giá: ${activeRecord.opp_id}\n` +
          `Khách hàng: ${activeRecord.customer_name} (Liên hệ: ${activeRecord.contact_person})\n` +
          `Đại diện NVKD Minh An: ${activeRecord.assigned_rep}\n` +
          `------------------------------------------------------------\n`;
        activeRecord.items.forEach((it, i) => {
          content += ` ${i+1}. [${it.sku}] ${it.product_name}\n    SL: ${it.quantity} | Đơn giá: ${it.unit_price.toLocaleString('vi-VN')} đ | Thành tiền: ${it.total_price.toLocaleString('vi-VN')} đ\n    Tồn kho & SLA: ${it.note}\n`;
        });
        content += `------------------------------------------------------------\n` +
          `Tổng niêm yết: ${activeRecord.subtotal.toLocaleString('vi-VN')} VNĐ\n` +
          `Chiết khấu (${activeRecord.discount_pct}%): -${activeRecord.discount_amount.toLocaleString('vi-VN')} VNĐ\n` +
          `TỔNG THANH TOÁN: ${activeRecord.final_total.toLocaleString('vi-VN')} VNĐ\n` +
          `Tiến độ bàn giao: ${activeRecord.lead_time_days} ngày làm việc\n` +
          `Google Docs URL: ${activeRecord.quote_doc_url || '(Chưa tạo - Cần tích Checkbox Tạo Báo Giá)'}\n`;
        box.innerText = content;
      }
    }

    async function rewriteEmailWithAi(tone) {
      if (!activeRecord) return;
      const box = document.getElementById('preview-content-box');
      box.innerText = "🤖 AI đang phân tích và tối ưu hóa thư đàm phán...";
      try {
        const res = await fetch('/api/ai_rewrite_email', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ email: activeRecord.drafts.customer_email_draft, tone: tone })
        });
        const data = await res.json();
        box.innerText = data.rewritten;
      } catch (e) { alert("Lỗi AI: " + e.message); }
    }

    function printQuotation() {
      if (!activeRecord) return;
      let rows = '';
      activeRecord.items.forEach((it, idx) => {
        rows += `<tr>
          <td style="text-align:center; padding:8px; border:1px solid #ccc;">${idx+1}</td>
          <td style="padding:8px; border:1px solid #ccc;"><b>[${it.sku}]</b> ${it.product_name}</td>
          <td style="text-align:center; padding:8px; border:1px solid #ccc;">Bộ</td>
          <td style="text-align:center; padding:8px; border:1px solid #ccc;">${it.quantity}</td>
          <td style="text-align:right; padding:8px; border:1px solid #ccc;">${it.unit_price.toLocaleString('vi-VN')} ₫</td>
          <td style="text-align:right; padding:8px; border:1px solid #ccc;"><b>${it.total_price.toLocaleString('vi-VN')} ₫</b></td>
          <td style="padding:8px; border:1px solid #ccc;">${it.note}</td>
        </tr>`;
      });
      const win = window.open('', '_blank');
      win.document.write(`
        <html><head><title>Báo giá ${activeRecord.opp_id}</title><style>
          body { font-family: Arial, sans-serif; padding: 30px; color: #111; }
          table { width: 100%; border-collapse: collapse; margin: 20px 0; }
          th { background: #f0f4f8; padding: 10px; border: 1px solid #ccc; }
        </style></head><body>
          <h2>CÔNG TY CỔ PHẦN CÔNG NGHỆ MINH AN</h2>
          <p>Tầng 8, Tòa nhà Công Nghệ, Cầu Giấy, Hà Nội | Hotline: (024) 3999 8888</p><hr/>
          <h2 style="text-align:center; margin-top:20px;">BẢNG BÁO GIÁ THIẾT BỊ VÀ DỊCH VỤ CÔNG NGHỆ</h2>
          <p style="text-align:center;">Mã: <b>${activeRecord.opp_id}</b> | Ngày: ${activeRecord.created_at}</p>
          <p><b>Khách hàng:</b> ${activeRecord.customer_name} &nbsp;|&nbsp; <b>NVKD:</b> ${activeRecord.assigned_rep}</p>
          <table>
            <thead><tr><th>STT</th><th>Hạng mục</th><th>ĐVT</th><th>SL</th><th>Đơn giá</th><th>Thành tiền</th><th>Tồn kho & SLA</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
          <div style="float:right; width:360px;">
            <p>Tổng niêm yết: <b>${activeRecord.subtotal.toLocaleString('vi-VN')} ₫</b></p>
            <p>Chiết khấu thương mại (${activeRecord.discount_pct}%): <b>-${activeRecord.discount_amount.toLocaleString('vi-VN')} ₫</b></p>
            <p style="font-size:16px; color:#2563eb;">TỔNG CỘNG THANH TOÁN: <b>${activeRecord.final_total.toLocaleString('vi-VN')} ₫</b></p>
          </div>
          <div style="clear:both; margin-top:30px;"><p><b>Tiến độ triển khai:</b> ${activeRecord.lead_time_days} ngày làm việc.</p><p><b>Trạng thái:</b> ${activeRecord.approval_status}</p></div>
        </body></html>
      `);
      win.document.close();
      win.print();
    }

    function copyPreviewText() {
      navigator.clipboard.writeText(document.getElementById('preview-content-box').innerText);
      alert("Đã sao chép vào bộ nhớ tạm!");
    }

    // AI COPILOT
    function toggleAiDrawer() {
      const d = document.getElementById('ai-chat-drawer');
      d.style.display = (d.style.display === 'flex') ? 'none' : 'flex';
    }

    async function sendAiMessage() {
      const input = document.getElementById('ai-query-input');
      const q = input.value.trim();
      if (!q) return;

      const history = document.getElementById('ai-chat-history');
      history.innerHTML += `<div class="ai-chat-bubble ai-bubble-user">${q}</div>`;
      input.value = '';
      history.scrollTop = history.scrollHeight;

      history.innerHTML += `<div class="ai-chat-bubble ai-bubble-assistant" id="ai-loading-box">🤖 AI đang suy nghĩ...</div>`;
      history.scrollTop = history.scrollHeight;

      try {
        const res = await fetch('/api/ai_chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ query: q })
        });
        const data = await res.json();
        document.getElementById('ai-loading-box').remove();
        history.innerHTML += `<div class="ai-chat-bubble ai-bubble-assistant">${data.reply.replace(/\n/g, '<br>')}</div>`;
        history.scrollTop = history.scrollHeight;
      } catch (e) {
        document.getElementById('ai-loading-box').innerText = "Lỗi: " + e.message;
      }
    }

    fetchData();
    fetchCatalog();
  </script>
</body>
</html>
"""


class MinhAnServerHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, content_type="application/json", status=200):
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(status=204)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == "/" or path == "/index.html":
            self._set_headers(content_type="text/html")
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif path == "/api/crm_records":
            self._set_headers()
            self.wfile.write(json.dumps(crm_records, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/catalog":
            self._set_headers()
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))
        elif path == "/api/export_csv":
            csv_lines = [
                "Mã Cơ hội,Khách hàng,Người liên hệ,NVKD Phụ trách,Tổng Niêm Yết,Chiết khấu,Thành tiền,Trạng thái Phê duyệt,Thời gian Triển khai,Checkbox Tạo Báo Giá,Link Docs Báo Giá,Nhận định AI"
            ]
            for r in crm_records:
                warn = r.get("ai_assessment", "").replace('"', '""')
                csv_lines.append(
                    f'"{r["opp_id"]}","{r["customer_name"]}","{r["contact_person"]}","{r["assigned_rep"]}",'
                    f'{r["subtotal"]},{r["discount_pct"]}%,{r["final_total"]},"{r["approval_status"]}",'
                    f'"{r["lead_time_days"]} ngày",{r["checkbox_create_quote"]},"{r["quote_doc_url"]}","{warn}"'
                )
            csv_data = "\ufeff" + "\n".join(csv_lines)
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=crm_minhan_export.csv")
            self.end_headers()
            self.wfile.write(csv_data.encode("utf-8"))
        else:
            self._set_headers(status=404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        global user_gemini_api_key
        url = urllib.parse.urlparse(self.path)
        path = url.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")

        try:
            req_data = json.loads(body) if body else {}
        except Exception:
            req_data = {}

        if path == "/api/ai_chat":
            q = req_data.get("query", "")
            context = {"records": crm_records}
            reply = call_gemini_copilot(q, context, user_gemini_api_key)
            self._set_headers()
            self.wfile.write(json.dumps({"reply": reply}, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/ai_rewrite_email":
            email_txt = req_data.get("email", "")
            tone = req_data.get("tone", "negotiate")
            rewritten = call_gemini_rewrite_email(email_txt, tone, user_gemini_api_key)
            self._set_headers()
            self.wfile.write(json.dumps({"rewritten": rewritten}, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/process_inquiry":
            extracted = agent.parse_inquiry_agent(req_data)
            opp = agent.validate_and_price_agent(extracted)
            drafts = agent.generate_proposals_and_drafts(opp)

            status = "Chờ Trưởng phòng duyệt" if opp.approval_required else "Đúng thẩm quyền (<=10%)"
            ai_eval = generate_ai_assessment(opp)

            record = {
                "opp_id": opp.opportunity_id,
                "customer_name": opp.customer_name,
                "contact_person": opp.contact_person,
                "email": opp.email,
                "phone": opp.phone,
                "raw_content": req_data.get("raw_content", ""),
                "assigned_rep": f"{opp.assigned_rep_name} ({opp.assigned_rep_id})",
                "rep_email": opp.assigned_rep_email,
                "subtotal": opp.subtotal,
                "discount_pct": opp.discount_pct,
                "discount_amount": opp.discount_amount,
                "final_total": opp.final_total,
                "approval_status": status,
                "lead_time_days": opp.max_lead_time_days,
                "deadline_feasibility": opp.deadline_feasibility,
                "ai_assessment": ai_eval,
                "checkbox_create_quote": False,
                "quote_doc_url": "",
                "items": [asdict(i) for i in opp.items],
                "drafts": drafts,
                "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            crm_records.insert(0, record)
            self._set_headers()
            self.wfile.write(json.dumps(record, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/manager_decision":
            opp_id = req_data.get("opp_id")
            decision = req_data.get("decision")
            target = next((r for r in crm_records if r["opp_id"] == opp_id), None)

            if target:
                if decision == "approve":
                    target["approval_status"] = "Đã duyệt (Trưởng phòng duyệt)"
                elif decision == "reject":
                    target["approval_status"] = "Hoàn thành (Từ chối)"
                    target["checkbox_create_quote"] = False
                self._set_headers()
                self.wfile.write(json.dumps({"success": True, "record": target}, ensure_ascii=False).encode("utf-8"))
            else:
                self._set_headers(status=404)
                self.wfile.write(json.dumps({"error": "Không tìm thấy cơ hội"}, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/trigger_create_quote":
            opp_id = req_data.get("opp_id")
            target = next((r for r in crm_records if r["opp_id"] == opp_id), None)

            if target:
                target["checkbox_create_quote"] = True
                doc_url = f"https://docs.google.com/document/d/minhan-{opp_id.lower()}-official-quote/edit"
                target["quote_doc_url"] = doc_url
                self._set_headers()
                self.wfile.write(json.dumps({"success": True, "doc_url": doc_url}, ensure_ascii=False).encode("utf-8"))
            else:
                self._set_headers(status=404)
                self.wfile.write(json.dumps({"error": "Không tìm thấy cơ hội"}, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/complete_deal":
            opp_id = req_data.get("opp_id")
            target = next((r for r in crm_records if r["opp_id"] == opp_id), None)

            if target:
                target["approval_status"] = "Chốt đơn / Hoàn tất"
                self._set_headers()
                self.wfile.write(json.dumps({"success": True, "record": target}, ensure_ascii=False).encode("utf-8"))
            else:
                self._set_headers(status=404)
                self.wfile.write(json.dumps({"error": "Không tìm thấy cơ hội"}, ensure_ascii=False).encode("utf-8"))
        else:
            self._set_headers(status=404)
            self.wfile.write(json.dumps({"error": "Endpoint không hợp lệ"}).encode("utf-8"))


def run():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), MinhAnServerHandler) as httpd:
        print("=" * 75)
        print(" CÔNG TY CÔNG NGHỆ MINH AN - GIAO DIỆN FORSHOP VIỀN XANH MINT NHẠT")
        print(f" Web Dashboard: http://localhost:{PORT}")
        print(" Đang phục vụ trên cổng 8080...")
        print("=" * 75)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nĐã dừng máy chủ localhost.")


if __name__ == "__main__":
    run()

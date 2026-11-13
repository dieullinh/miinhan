# -*- coding: utf-8 -*-
"""
Builder for Minh An Technology:
- Nền ngoài: Màu trắng tinh tế (#ffffff / #fcfdfd)
- Nền trong: Màu xanh mint pastel làm nền canvas chính (#e4f6ee / #d8f3e5)
- Giao diện Khách hàng là 1 trang riêng biệt (Customer Portal):
    * Có thể chuyển đổi mượt mà giữa Doanh nghiệp Minh An và Khách hàng Portal
    * Hỗ trợ URL trực tiếp /customer và /business
    * Cổng Khách hàng có: Form gửi yêu cầu RFQ, Chatbot AI tư vấn trực tiếp 24/7,
      bảng theo dõi báo giá cá nhân, mở Google Docs báo giá và ký xác nhận đơn hàng
"""

import sys

content = '''"""
MINH AN TECHNOLOGY SOLUTIONS - DUAL PORTAL (BUSINESS & CUSTOMER SEPARATE VIEWS)
- Outer background: Pure clean white (#ffffff)
- Inner canvas background: Soft pastel mint (#e4f6ee / #d8f3e5)
- Separate dedicated Customer Portal view & Business CRM Studio
"""

import http.server
import socketserver
import json
import os
import urllib.parse
from datetime import datetime
from dataclasses import asdict

from agent_engine import CatalogService, MinhAnSalesAIAgent, ExtractedInquiry, OpportunityProfile
from gemini_llm import call_customer_consultant, call_gemini_parser, call_gemini_rewrite_email, call_gemini_copilot

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

def load_sample_crm_data():
    global crm_records
    crm_records.clear()
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
                    "quote_doc_url": f"https://docs.google.com/document/d/minhan-{opp.opportunity_id.lower()}-official-quote/edit",
                    "items": [asdict(i) for i in opp.items],
                    "drafts": drafts,
                    "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                crm_records.append(record)

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Minh An AI - B2B Solutions Portal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      /* NỀN NGOÀI MÀU TRẮNG TINH */
      --bg-outer: #ffffff;
      
      /* NỀN TRONG MÀU XANH MINT PASTEL DỊU MÁT */
      --bg-inner-canvas: #e6f6ee;
      --bg-inner-canvas-border: #bdebd4;
      --canvas-shadow: 0 16px 40px rgba(16, 185, 129, 0.08), 0 2px 6px rgba(0, 0, 0, 0.02);
      
      /* THẺ NỘI BỘ MÀU TRẮNG DẬP NỔI */
      --card-bg: #ffffff;
      --card-bg-subtle: #f8faf9;
      --card-border: rgba(230, 243, 236, 0.95);
      --card-shadow: 0 6px 20px rgba(16, 185, 129, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02);
      
      --text-main: #192a24;
      --text-sub: #526b61;
      --text-muted: #829a90;
      
      /* GRADIENTS & ACCENTS */
      --sunset-gradient: linear-gradient(135deg, #fca5a5 0%, #fb923c 55%, #f97316 100%);
      --sunset-glow: 0 8px 24px rgba(251, 146, 60, 0.38);
      
      --mint-gradient: linear-gradient(135deg, #34d399 0%, #10b981 100%);
      --mint-glow: 0 8px 20px rgba(16, 185, 129, 0.3);
      --mint-subtle: #d1fae5;
      --mint-text: #059669;
      
      --pink-pill-bg: #ffe4e6;
      --pink-pill-border: #fecdd3;
      --pink-text: #e11d48;
      
      --orange-accent: #f97316;
      --pink-accent: #ec4899;
      --cyan-accent: #0ea5e9;
      --purple-accent: #a855f7;
      
      --ui-scale: 1;
      --sidebar-width: 245px;
      --border-radius: 26px;
      --card-radius: 20px;
      --font-base: 13.5px;
      
      --transition-smooth: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    [data-theme="dark"] {
      --bg-outer: #0b110f;
      --bg-inner-canvas: #121f1a;
      --bg-inner-canvas-border: rgba(110, 231, 183, 0.2);
      --canvas-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
      
      --card-bg: #182823;
      --card-bg-subtle: #13201c;
      --card-border: rgba(110, 231, 183, 0.15);
      --card-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      
      --text-main: #f0fdf4;
      --text-sub: #a7f3d0;
      --text-muted: #6ee7b7;
      
      --pink-pill-bg: #4c0519;
      --pink-pill-border: #881337;
      --pink-text: #f43f5e;
      --mint-subtle: #064e3b;
      --mint-text: #34d399;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }

    /* NỀN NGOÀI MÀU TRẮNG */
    body {
      background: var(--bg-outer);
      min-height: 100vh;
      color: var(--text-main);
      display: flex; justify-content: center; align-items: center;
      padding: 16px;
      font-size: var(--font-base);
      position: relative;
      overflow-x: hidden;
      transition: background 0.3s ease;
    }

    /* KHUNG TOÀN ỨNG DỤNG (VIEWPORT) */
    .app-viewport {
      width: 100%; max-width: 1540px; height: calc(100vh - 32px);
      display: flex; gap: 16px; position: relative; z-index: 1;
      transform: scale(var(--ui-scale));
      transform-origin: center center;
      transition: transform 0.2s ease;
    }

    /* ========================================================
       1. LEFT SIDEBAR (DÀNH CHO BẢN DOANH NGHIỆP)
    ======================================================== */
    aside.studio-sidebar {
      width: var(--sidebar-width);
      min-width: var(--sidebar-width);
      background: var(--bg-inner-canvas);
      border: 1.5px solid var(--bg-inner-canvas-border);
      border-radius: var(--border-radius);
      box-shadow: var(--canvas-shadow);
      padding: 22px 18px;
      display: flex; flex-direction: column; justify-content: space-between;
      position: relative;
      transition: var(--transition-smooth);
      overflow-y: auto; overflow-x: hidden;
    }

    aside.studio-sidebar.collapsed {
      width: 76px !important; min-width: 76px !important; padding: 20px 10px;
    }
    aside.studio-sidebar.collapsed .hide-on-collapsed { display: none !important; }

    .btn-collapse-sidebar {
      position: absolute; top: 22px; right: 14px;
      width: 26px; height: 26px; border-radius: 50%;
      background: #ffffff; border: 1px solid var(--card-border);
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      font-size: 11px; font-weight: 800; color: var(--text-sub); transition: 0.2s;
    }
    .btn-collapse-sidebar:hover { background: var(--mint-subtle); color: var(--mint-text); }

    .sidebar-brand-row {
      display: flex; align-items: center; gap: 12px; margin-bottom: 24px;
    }
    .brand-squircle-plus {
      width: 38px; height: 38px; min-width: 38px; border-radius: 12px;
      background: var(--mint-gradient);
      box-shadow: var(--mint-glow);
      display: flex; align-items: center; justify-content: center;
      color: white; font-size: 22px; font-weight: 800;
    }
    .brand-text-title {
      font-size: 19px; font-weight: 800; color: var(--text-main); letter-spacing: -0.5px;
    }
    .brand-text-ai { color: #f87171; font-weight: 800; }

    .sidebar-menu-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
    
    .nav-pill-item a {
      display: flex; align-items: center; justify-content: space-between;
      padding: 11px 16px; border-radius: 16px; text-decoration: none;
      font-size: 13.5px; font-weight: 600; color: var(--text-sub);
      transition: var(--transition-smooth);
    }
    .nav-pill-item a:hover {
      background: rgba(255, 255, 255, 0.7); color: var(--text-main);
    }
    .nav-pill-item.active a {
      background: #ffffff;
      color: var(--text-main); font-weight: 800;
      border: 1px solid var(--card-border);
      box-shadow: 0 4px 16px rgba(16, 185, 129, 0.15);
    }
    [data-theme="dark"] .nav-pill-item.active a {
      background: #1c2b26; border-color: rgba(110, 231, 183, 0.3);
    }
    .nav-left-part { display: flex; align-items: center; gap: 12px; }
    .nav-icon-svg {
      width: 18px; height: 18px; stroke: currentColor; fill: none; stroke-width: 2;
      stroke-linecap: round; stroke-linejoin: round; display: flex; align-items: center; justify-content: center;
    }

    .btn-toggle-glow-dark {
      width: 100%; padding: 10px 14px; border-radius: 14px;
      background: #ffffff; border: 1px solid var(--card-border);
      font-size: 12.5px; font-weight: 700; color: var(--text-sub);
      display: flex; align-items: center; justify-content: center; gap: 8px;
      cursor: pointer; transition: 0.2s;
    }
    .btn-toggle-glow-dark:hover { color: var(--text-main); box-shadow: 0 2px 10px rgba(0,0,0,0.05); }

    /* ========================================================
       2. NỀN TRONG XANH MINT (MAIN CANVAS CONTAINER)
    ======================================================== */
    main.studio-main-board, main.customer-portal-board {
      flex: 1;
      background: var(--bg-inner-canvas);
      border: 1.5px solid var(--bg-inner-canvas-border);
      border-radius: var(--border-radius);
      box-shadow: var(--canvas-shadow);
      padding: 22px 26px;
      display: flex; flex-direction: column; gap: 18px;
      overflow-y: auto; overflow-x: hidden;
      position: relative;
    }

    /* TOP HEADER BAR */
    .studio-header-bar {
      display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;
    }
    .top-left-switcher {
      display: inline-flex; align-items: center; background: #ffffff;
      border: 1px solid var(--bg-inner-canvas-border); border-radius: 9999px; padding: 5px; gap: 6px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
    }
    .btn-role-tab {
      border: none; background: transparent; padding: 8px 18px; border-radius: 9999px;
      font-size: 13px; font-weight: 700; color: var(--text-sub); cursor: pointer;
      display: inline-flex; align-items: center; gap: 7px; transition: 0.2s;
    }
    .btn-role-tab.active {
      background: var(--mint-gradient); color: #ffffff; font-weight: 800;
      box-shadow: var(--mint-glow);
    }
    .btn-role-tab:hover:not(.active) {
      background: rgba(16, 185, 129, 0.1); color: var(--mint-text);
    }

    .top-right-actions { display: flex; align-items: center; gap: 10px; }
    
    .btn-chat-ai-pill {
      background: var(--mint-gradient); color: white;
      border: none; border-radius: 9999px; padding: 8px 18px;
      font-size: 12.5px; font-weight: 800; cursor: pointer;
      display: inline-flex; align-items: center; gap: 8px;
      box-shadow: var(--mint-glow); transition: var(--transition-smooth);
    }
    .btn-chat-ai-pill:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(16, 185, 129, 0.45); }

    .btn-sunset-highlight {
      background: var(--sunset-gradient); color: white;
      border: none; border-radius: 9999px; padding: 8px 20px;
      font-size: 12.5px; font-weight: 800; cursor: pointer;
      display: inline-flex; align-items: center; gap: 8px;
      box-shadow: var(--sunset-glow); transition: var(--transition-smooth);
    }
    .btn-sunset-highlight:hover { transform: translateY(-2px); box-shadow: 0 12px 28px rgba(251, 146, 60, 0.5); }

    /* ========================================================
       BUSINESS PORTAL SPECIFIC STYLES
    ======================================================== */
    .top-featured-grid {
      display: grid; grid-template-columns: 1.45fr 1fr; gap: 16px;
    }
    .sales-analytics-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--card-radius);
      padding: 18px 22px;
      box-shadow: var(--card-shadow);
      display: flex; flex-direction: column; justify-content: space-between;
      position: relative; overflow: hidden;
    }
    .analytics-head-row {
      display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
    }
    .analytics-title-tag {
      font-size: 11px; font-weight: 800; letter-spacing: 1px; color: var(--text-sub); text-transform: uppercase;
    }
    .analytics-price-badge {
      background: var(--pink-pill-bg); border: 1px solid var(--pink-pill-border);
      color: var(--pink-text); padding: 4px 12px; border-radius: 9999px;
      font-size: 12px; font-weight: 800;
    }
    .analytics-curve-wrapper {
      width: 100%; height: 110px; position: relative; margin-bottom: 6px;
    }
    .analytics-curve-wrapper svg { width: 100%; height: 100%; overflow: visible; }
    .analytics-footer-text {
      font-size: 11px; font-weight: 600; color: var(--text-muted); text-align: center;
    }

    .neumorphic-control-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--card-radius);
      padding: 18px 22px;
      box-shadow: var(--card-shadow);
      display: flex; flex-direction: column; justify-content: space-between; gap: 12px;
    }
    
    .squircle-buttons-grid {
      display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px;
    }
    .btn-squircle-neu {
      aspect-ratio: 1; border-radius: 12px;
      background: var(--card-bg-subtle); border: 1px solid var(--card-border);
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; color: var(--text-sub); font-size: 14px; font-weight: 800;
      transition: var(--transition-smooth);
    }
    .btn-squircle-neu:hover {
      background: #ffffff; color: var(--text-main); transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15); border-color: var(--mint-subtle);
    }
    .btn-squircle-neu svg {
      width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 2.2;
    }

    .neu-inputs-col { display: flex; flex-direction: column; gap: 8px; }
    .neu-input-pill {
      background: var(--card-bg-subtle); border: 1px solid var(--card-border);
      border-radius: 12px; padding: 8px 14px; font-size: 11.5px; font-weight: 600;
      color: var(--text-main); outline: none; width: 100%; transition: 0.2s;
    }
    .neu-input-pill:focus {
      background: #ffffff; border-color: var(--mint-text); box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.12);
    }

    .btn-login-ai-sunset {
      width: 100%; border: none; border-radius: 14px;
      background: var(--sunset-gradient);
      box-shadow: var(--sunset-glow);
      color: white; padding: 11px 16px; font-size: 12.5px; font-weight: 800;
      letter-spacing: 0.5px; text-transform: uppercase; cursor: pointer;
      display: flex; align-items: center; justify-content: center; gap: 8px;
      transition: var(--transition-smooth);
    }
    .btn-login-ai-sunset:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(251, 146, 60, 0.5); }

    .middle-gauges-profile-grid {
      display: grid; grid-template-columns: 1.1fr 0.9fr 1.3fr; gap: 16px; align-items: stretch;
    }
    .gauges-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 16px 20px;
      box-shadow: var(--card-shadow);
      display: flex; justify-content: space-around; align-items: center;
    }
    .gauge-item { display: flex; flex-direction: column; align-items: center; gap: 6px; }
    .gauge-ring-box {
      width: 64px; height: 64px; position: relative;
      display: flex; align-items: center; justify-content: center;
    }
    .gauge-ring-box svg { width: 64px; height: 64px; transform: rotate(-90deg); }
    .gauge-ring-bg { fill: none; stroke: rgba(0, 0, 0, 0.06); stroke-width: 5; }
    [data-theme="dark"] .gauge-ring-bg { stroke: rgba(255, 255, 255, 0.08); }
    .gauge-ring-val {
      fill: none; stroke-width: 5; stroke-linecap: round;
      stroke-dasharray: 157; transition: stroke-dashoffset 1s ease;
    }
    .gauge-percent-text {
      position: absolute; font-size: 12.5px; font-weight: 800; color: var(--text-main);
    }
    .gauge-label-text { font-size: 11px; font-weight: 700; color: var(--text-sub); }

    .equalizer-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 14px 20px;
      box-shadow: var(--card-shadow);
      display: flex; flex-direction: column; justify-content: space-between; align-items: center;
    }
    .eq-tag { font-size: 10px; font-weight: 800; color: var(--text-muted); letter-spacing: 0.5px; }
    .eq-bars-group { display: flex; align-items: flex-end; gap: 10px; height: 48px; }
    .eq-bar { width: 10px; border-radius: 9999px; transition: height 0.3s ease; }
    .bar-orange { height: 75%; background: var(--orange-accent); }
    .bar-purple { height: 45%; background: var(--purple-accent); }
    .bar-cyan { height: 90%; background: var(--cyan-accent); }

    .profile-rep-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 16px 20px;
      box-shadow: var(--card-shadow);
      display: flex; justify-content: space-between; align-items: center;
    }
    .rep-info-left { display: flex; align-items: center; gap: 12px; }
    .rep-avatar-purple {
      width: 44px; height: 44px; border-radius: 14px;
      background: linear-gradient(135deg, #c084fc 0%, #9333ea 100%);
      box-shadow: 0 4px 14px rgba(147, 51, 234, 0.3);
      display: flex; align-items: center; justify-content: center; color: white;
    }
    .rep-avatar-purple svg { width: 22px; height: 22px; stroke: white; fill: none; stroke-width: 2; }
    .rep-name-title h4 { font-size: 13.5px; font-weight: 800; color: var(--text-main); }
    .rep-name-title p { font-size: 11.5px; color: var(--text-sub); }
    .rep-rating-right { text-align: right; }
    .rep-rating-right .rate-tag { font-size: 10px; font-weight: 800; color: var(--text-muted); letter-spacing: 0.5px; }
    .rep-rating-right .rate-score { font-size: 15px; font-weight: 800; color: var(--text-main); display: flex; align-items: center; gap: 4px; }
    .rate-star-icon { color: #f59e0b; font-size: 16px; }

    .slider-strip-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: 16px; padding: 10px 20px;
      box-shadow: var(--card-shadow);
      display: flex; align-items: center; justify-content: space-between; gap: 16px;
    }
    .slider-track-wrap { display: flex; align-items: center; gap: 12px; flex: 1; }
    .slider-track-wrap span { font-weight: 800; color: var(--text-muted); font-size: 14px; }
    .input-range-styled {
      flex: 1; -webkit-appearance: none; height: 6px; border-radius: 9999px;
      background: rgba(16, 185, 129, 0.15); outline: none;
    }
    .input-range-styled::-webkit-slider-thumb {
      -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%;
      background: #10b981; cursor: pointer; box-shadow: 0 0 10px rgba(16, 185, 129, 0.6);
    }
    .slider-info-badge {
      font-size: 12px; font-weight: 800; color: var(--mint-text); white-space: nowrap;
    }

    .pipeline-diagram-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 16px 20px;
      box-shadow: var(--card-shadow);
      display: flex; flex-direction: column; gap: 12px;
    }
    .pipeline-head-row { display: flex; justify-content: space-between; align-items: center; }
    .pipeline-head-row h3 { font-size: 13px; font-weight: 800; color: var(--text-main); display: flex; align-items: center; gap: 8px; }
    .pipeline-ready-tag { font-size: 11px; font-weight: 800; color: var(--orange-accent); }

    .steps-chain-row { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }
    .chain-step-pill {
      background: var(--card-bg-subtle); border: 1px solid var(--card-border);
      border-radius: 14px; padding: 10px 8px; text-align: center;
      display: flex; flex-direction: column; align-items: center; gap: 4px;
      cursor: pointer; transition: var(--transition-smooth);
    }
    .chain-step-pill:hover { transform: translateY(-2px); border-color: #10b981; }
    .chain-step-pill.active {
      background: #ffffff; border-color: #10b981;
      box-shadow: 0 4px 14px rgba(16, 185, 129, 0.2);
    }
    .step-num-text { font-size: 9.5px; font-weight: 700; color: var(--text-muted); }
    .step-name-text { font-size: 11px; font-weight: 800; color: var(--text-main); line-height: 1.25; }

    .split-resizable-container {
      display: flex; gap: 0; min-height: 320px; position: relative;
    }
    .split-col-left {
      width: 48%; display: flex; flex-direction: column; gap: 10px; padding-right: 12px;
    }
    .split-resizer-handle {
      width: 10px; cursor: col-resize; position: relative; z-index: 10;
      display: flex; align-items: center; justify-content: center;
      transition: background 0.2s;
    }
    .split-resizer-handle:hover, .split-resizer-handle.dragging {
      background: rgba(16, 185, 129, 0.2); border-radius: 4px;
    }
    .split-resizer-handle::after { content: "⋮"; font-size: 16px; color: var(--text-muted); }
    .split-col-right {
      flex: 1; display: flex; flex-direction: column; gap: 10px; padding-left: 12px;
    }

    .scenarios-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 16px 18px;
      box-shadow: var(--card-shadow);
      display: flex; flex-direction: column; gap: 10px; flex: 1; overflow-y: auto;
    }
    .scenario-item-box {
      background: var(--card-bg-subtle); border: 1px solid var(--card-border);
      border-radius: 14px; padding: 12px 14px; cursor: pointer; transition: var(--transition-smooth);
    }
    .scenario-item-box:hover {
      transform: translateY(-2px); border-color: #10b981; box-shadow: 0 4px 14px rgba(0,0,0,0.03);
    }
    .scenario-item-box.selected {
      border: 1.5px solid #f87171; background: #fff1f2;
    }
    [data-theme="dark"] .scenario-item-box.selected {
      background: #4c0519; border-color: #f43f5e;
    }
    .scen-title-bold { font-size: 12.5px; font-weight: 800; color: var(--text-main); }
    .scen-desc-txt { font-size: 11.5px; color: var(--text-sub); line-height: 1.4; margin-top: 4px; }

    .execution-result-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 22px;
      box-shadow: var(--card-shadow);
      display: flex; flex-direction: column; justify-content: center; align-items: center;
      flex: 1; overflow-y: auto; text-align: center; position: relative;
    }
    .empty-sparkle-icon {
      width: 52px; height: 52px; border-radius: 50%;
      background: var(--pink-pill-bg); color: var(--pink-text);
      display: flex; align-items: center; justify-content: center;
      font-size: 24px; margin-bottom: 12px;
      box-shadow: 0 0 20px rgba(244, 63, 94, 0.2);
    }

    .crm-table-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 20px 24px;
      box-shadow: var(--card-shadow);
      display: flex; flex-direction: column; gap: 14px;
    }
    .crm-table-header-row {
      display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;
    }
    .crm-title-area h3 { font-size: 14px; font-weight: 800; color: var(--text-main); }
    .crm-title-area p { font-size: 11.5px; color: var(--text-sub); }

    .crm-action-pills-wrap { display: flex; align-items: center; gap: 8px; }
    .btn-pill-action {
      border: none; border-radius: 9999px; padding: 7px 16px;
      font-size: 11.5px; font-weight: 800; cursor: pointer;
      display: inline-flex; align-items: center; gap: 6px; transition: 0.2s;
    }
    .btn-pill-pink {
      background: var(--pink-pill-bg); border: 1px solid var(--pink-pill-border);
      color: var(--pink-text);
    }
    .btn-pill-pink:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(244, 63, 94, 0.2); }
    .btn-pill-mint {
      background: var(--mint-gradient); color: white; box-shadow: var(--mint-glow);
    }
    .btn-pill-mint:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4); }
    .btn-pill-teal {
      background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
      color: white; box-shadow: 0 4px 14px rgba(14, 165, 233, 0.3);
    }
    .btn-pill-teal:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(14, 165, 233, 0.45); }

    .crm-data-table {
      width: 100%; border-collapse: separate; border-spacing: 0 8px; font-size: 12px;
    }
    .crm-data-table th {
      padding: 10px 14px; color: var(--text-sub); font-weight: 700; text-align: left;
      border-bottom: 1.5px solid var(--card-border);
    }
    .crm-data-table td {
      padding: 12px 14px; background: var(--card-bg-subtle);
      transition: background 0.2s;
    }
    .crm-data-table tr td:first-child { border-top-left-radius: 12px; border-bottom-left-radius: 12px; }
    .crm-data-table tr td:last-child { border-top-right-radius: 12px; border-bottom-right-radius: 12px; }
    .crm-data-table tr:hover td { background: #ffffff; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03); }
    [data-theme="dark"] .crm-data-table tr:hover td { background: #1c2b26; }

    .status-badge-pill {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 800;
    }
    .badge-approved { background: var(--mint-subtle); color: var(--mint-text); }
    .badge-pending { background: #fef3c7; color: #b45309; }
    .badge-closed { background: #dbeafe; color: #1d4ed8; }

    /* ========================================================
       3. GIAO DIỆN KHÁCH HÀNG RIÊNG BIỆT (CUSTOMER PORTAL)
    ======================================================== */
    #customer-page-view {
      display: none; width: 100%; flex-direction: column; gap: 18px;
    }

    .customer-hero-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 24px 28px;
      box-shadow: var(--card-shadow);
      display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;
    }
    .customer-hero-text h2 { font-size: 22px; font-weight: 800; color: var(--text-main); letter-spacing: -0.5px; }
    .customer-hero-text p { font-size: 13.5px; color: var(--text-sub); margin-top: 4px; }

    .customer-grid-layout {
      display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 18px;
    }

    /* FORM GỬI YÊU CẦU BÁO GIÁ CỦA KHÁCH HÀNG */
    .customer-rfq-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 24px;
      box-shadow: var(--card-shadow);
      display: flex; flex-direction: column; gap: 16px;
    }
    .form-group-field { display: flex; flex-direction: column; gap: 6px; }
    .form-group-field label { font-size: 12px; font-weight: 800; color: var(--text-main); }
    .form-input-styled {
      background: var(--card-bg-subtle); border: 1px solid var(--card-border);
      border-radius: 12px; padding: 10px 14px; font-size: 13px; color: var(--text-main);
      outline: none; transition: 0.2s;
    }
    .form-input-styled:focus {
      background: #ffffff; border-color: #10b981; box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
    }
    .form-textarea-styled {
      min-height: 95px; resize: vertical;
    }

    /* MẪU GỢI Ý 1-CLICK CHO KHÁCH */
    .quick-preset-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
    .chip-sample-btn {
      background: var(--mint-subtle); color: var(--mint-text); border: none;
      padding: 5px 12px; border-radius: 9999px; font-size: 11px; font-weight: 700;
      cursor: pointer; transition: 0.2s;
    }
    .chip-sample-btn:hover { background: #10b981; color: white; }

    /* CHATBOT TƯ VẤN TRỰC TIẾP TRÊN TRANG KHÁCH HÀNG */
    .customer-chat-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 20px;
      box-shadow: var(--card-shadow);
      display: flex; flex-direction: column; height: 540px;
    }
    .customer-chat-messages {
      flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px;
      padding: 12px 6px;
    }
    .chat-bubble-ai {
      background: var(--card-bg-subtle); border: 1px solid var(--card-border);
      padding: 12px 16px; border-radius: 16px; border-bottom-left-radius: 4px;
      font-size: 13px; color: var(--text-main); max-width: 88%; align-self: flex-start;
      line-height: 1.5;
    }
    .chat-bubble-user {
      background: var(--mint-gradient); color: white;
      padding: 12px 16px; border-radius: 16px; border-bottom-right-radius: 4px;
      font-size: 13px; font-weight: 600; max-width: 88%; align-self: flex-end;
      box-shadow: var(--mint-glow);
    }

    /* BẢNG THEO DÕI ĐƠN HÀNG CỦA KHÁCH */
    .customer-history-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--card-radius); padding: 22px 26px;
      box-shadow: var(--card-shadow);
      display: flex; flex-direction: column; gap: 14px;
    }

    /* MODAL GLASS CONTROL */
    .glass-control-modal {
      display: none; position: fixed; inset: 0; z-index: 300;
      background: rgba(15, 23, 42, 0.45); backdrop-filter: blur(8px);
      align-items: center; justify-content: center; padding: 20px;
    }
    .glass-control-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: var(--border-radius); padding: 28px; width: 100%; max-width: 580px;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.2); display: flex; flex-direction: column; gap: 18px;
    }
    .control-row { display: flex; justify-content: space-between; align-items: center; gap: 14px; }
    .control-label { font-size: 13px; font-weight: 700; color: var(--text-main); }
    .control-slider {
      flex: 1; -webkit-appearance: none; height: 8px; border-radius: 9999px;
      background: rgba(0, 0, 0, 0.08); outline: none;
    }
    .control-slider::-webkit-slider-thumb {
      -webkit-appearance: none; width: 20px; height: 20px; border-radius: 50%;
      background: #10b981; cursor: pointer; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.5);
    }

    /* FLOATING CHAT BOT ICON */
    .ai-chat-bubble-bot {
      position: fixed; bottom: 26px; right: 28px; z-index: 200;
      width: 54px; height: 54px; border-radius: 50%;
      background: var(--mint-gradient); box-shadow: var(--mint-glow);
      color: white; display: flex; align-items: center; justify-content: center;
      cursor: pointer; transition: 0.2s;
    }
    .ai-chat-bubble-bot:hover { transform: scale(1.1); }
    .ai-chat-bubble-bot svg { width: 26px; height: 26px; stroke: white; fill: none; stroke-width: 2; }

    .ai-chat-drawer {
      display: none; position: fixed; bottom: 90px; right: 28px; z-index: 210;
      width: 420px; height: 560px; background: var(--card-bg);
      backdrop-filter: blur(30px); border: 1px solid var(--card-border);
      border-radius: 24px; box-shadow: 0 25px 60px rgba(0,0,0,0.25);
      flex-direction: column; overflow: hidden;
    }
  </style>
</head>
<body>

  <!-- KHUNG VIEWPORT CHÍNH -->
  <div class="app-viewport" id="app-viewport">

    <!-- ========================================================
         VIEW 1: DOANH NGHIỆP MINH AN (CRM STUDIO VIEW)
    ======================================================== -->
    <div id="business-page-view" style="display:flex; width:100%; gap:16px;">
      
      <!-- 1. LEFT SIDEBAR -->
      <aside class="studio-sidebar" id="studio-sidebar">
        <div>
          <button class="btn-collapse-sidebar" onclick="toggleSidebarCollapse()" title="Thu nhỏ / Mở rộng sidebar">❮</button>

          <!-- BRAND HEADER: SQUIRCLE '+' AND 'Minh An AI' -->
          <div class="sidebar-brand-row">
            <div class="brand-squircle-plus">
              <svg style="width:22px; height:22px; stroke:white; fill:none; stroke-width:3; stroke-linecap:round;" viewBox="0 0 24 24">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </div>
            <div class="hide-on-collapsed">
              <span class="brand-text-title">Minh An <span class="brand-text-ai">AI</span></span>
            </div>
          </div>

          <!-- NAVIGATION MENU -->
          <ul class="sidebar-menu-list">
            <li class="nav-pill-item active" id="menu-pipeline">
              <a href="javascript:void(0)" onclick="setRole('business')">
                <div class="nav-left-part">
                  <svg class="nav-icon-svg" viewBox="0 0 24 24">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                    <polyline points="9 22 9 12 15 12 15 22"></polyline>
                  </svg>
                  <span class="hide-on-collapsed">Dashboard CRM</span>
                </div>
              </a>
            </li>
            <li class="nav-pill-item" id="menu-switch-customer">
              <a href="javascript:void(0)" onclick="setRole('customer')">
                <div class="nav-left-part">
                  <svg class="nav-icon-svg" viewBox="0 0 24 24">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                  <span class="hide-on-collapsed">Cổng Khách Hàng ↗</span>
                </div>
              </a>
            </li>
            <li class="nav-pill-item" id="menu-crm">
              <a href="javascript:void(0)" onclick="scrollToTable()">
                <div class="nav-left-part">
                  <svg class="nav-icon-svg" viewBox="0 0 24 24">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                  </svg>
                  <span class="hide-on-collapsed">Hồ sơ CRM</span>
                </div>
              </a>
            </li>
            <li class="nav-pill-item" id="menu-diagram">
              <a href="/diagram" target="_blank">
                <div class="nav-left-part">
                  <svg class="nav-icon-svg" viewBox="0 0 24 24">
                    <line x1="18" y1="20" x2="18" y2="10"></line>
                    <line x1="12" y1="20" x2="12" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="14"></line>
                  </svg>
                  <span class="hide-on-collapsed">Sơ đồ Quy trình</span>
                </div>
              </a>
            </li>
          </ul>
        </div>

        <div class="hide-on-collapsed" style="display:flex; flex-direction:column; gap:8px;">
          <button class="btn-toggle-glow-dark" onclick="toggleTheme()">
            <svg style="width:16px; height:16px; stroke:currentColor; fill:none; stroke-width:2;" viewBox="0 0 24 24">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
            <span id="theme-btn-text">Chuyển Glow Tối</span>
          </button>
        </div>
      </aside>

      <!-- 2. MAIN STUDIO BOARD (NỀN TRONG XANH MINT) -->
      <main class="studio-main-board" id="studio-main-board">

        <!-- TOP HEADER BAR: ROLE SWITCHER & HIGHLIGHT BUTTONS -->
        <header class="studio-header-bar">
          <div class="top-left-switcher">
            <button class="btn-role-tab active" id="tab-business" onclick="setRole('business')">
              <svg style="width:15px; height:15px; stroke:currentColor; fill:none; stroke-width:2;" viewBox="0 0 24 24">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
              </svg>
              Doanh nghiệp Minh An
            </button>
            <button class="btn-role-tab" id="tab-customer" onclick="setRole('customer')">
              <svg style="width:15px; height:15px; stroke:currentColor; fill:none; stroke-width:2;" viewBox="0 0 24 24">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              Khách hàng Portal
            </button>
          </div>

          <div class="top-right-actions">
            <button class="btn-chat-ai-pill" onclick="toggleAiChat()">
              <span style="font-size:8px;">●</span> Chat AI Tư Vấn
            </button>
            
            <button class="btn-sunset-highlight" onclick="applyPresetAndRun('p1')">
              <svg style="width:14px; height:14px; fill:currentColor;" viewBox="0 0 24 24">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
              </svg>
              TIẾP NHẬN Y/C MỚI
            </button>

            <button class="btn-squircle-neu" style="width:36px; height:36px; border-radius:50%;" onclick="openGlassControlModal()" title="Glass Control">
              <svg viewBox="0 0 24 24"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line></svg>
            </button>
          </div>
        </header>

        <!-- TOP ROW: SALES ANALYTICS + 6 SQUIRCLE BUTTONS & LOGIN CTA -->
        <section class="top-featured-grid">
          
          <div class="sales-analytics-card">
            <div class="analytics-head-row">
              <span class="analytics-title-tag">SALES ANALYTICS</span>
              <span class="analytics-price-badge">$1,560</span>
            </div>
            <div class="analytics-curve-wrapper">
              <svg viewBox="0 0 400 120" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="mintGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#10b981" stop-opacity="0.35"/>
                    <stop offset="100%" stop-color="#10b981" stop-opacity="0.0"/>
                  </linearGradient>
                  <linearGradient id="pinkGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#f43f5e" stop-opacity="0.3"/>
                    <stop offset="100%" stop-color="#f43f5e" stop-opacity="0.0"/>
                  </linearGradient>
                </defs>
                <path d="M 0,90 Q 50,20 100,50 T 200,60 T 300,30 T 400,70 L 400,120 L 0,120 Z" fill="url(#mintGrad)" />
                <path d="M 0,90 Q 50,20 100,50 T 200,60 T 300,30 T 400,70" fill="none" stroke="#10b981" stroke-width="2.5" />
                <path d="M 0,105 Q 60,70 120,80 T 240,40 T 340,55 T 400,45 L 400,120 L 0,120 Z" fill="url(#pinkGrad)" />
                <path d="M 0,105 Q 60,70 120,80 T 240,40 T 340,55 T 400,45" fill="none" stroke="#f43f5e" stroke-width="2.2" stroke-dasharray="3,3" />
              </svg>
            </div>
            <p class="analytics-footer-text">Minh An B2B Sales & AI Intake Trends</p>
          </div>

          <div class="neumorphic-control-card">
            <div class="squircle-buttons-grid">
              <button class="btn-squircle-neu" onclick="adjustScale(0.05)" title="Phóng to UI">+</button>
              <button class="btn-squircle-neu" onclick="adjustScale(-0.05)" title="Thu nhỏ UI">−</button>
              <button class="btn-squircle-neu" onclick="resetScale()" title="Tỉ lệ mặc định">
                <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path></svg>
              </button>
              <button class="btn-squircle-neu" onclick="openGlassControlModal()" title="Menu Tinh chỉnh">
                <svg viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
              </button>
              <button class="btn-squircle-neu" onclick="openDiagramWindow()" title="Xem Sơ đồ">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="1"></circle><circle cx="19" cy="12" r="1"></circle><circle cx="5" cy="12" r="1"></circle></svg>
              </button>
              <button class="btn-squircle-neu" onclick="fetchData()" title="Làm mới">
                <svg viewBox="0 0 24 24"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
              </button>
            </div>

            <div class="neu-inputs-col">
              <input type="text" id="intake-company-input" class="neu-input-pill" placeholder="USERNAME / TÊN CÔNG TY" value="Công ty CP Công Nghệ Sao Việt" />
              <input type="text" id="intake-sku-input" class="neu-input-pill" placeholder="PASSWORD / MÃ THIẾT BỊ" value="2 Dell R750 + 1 Cisco 9200L" />
            </div>

            <button class="btn-login-ai-sunset" onclick="runPipelineFromInput()">
              <svg style="width:15px; height:15px; fill:currentColor;" viewBox="0 0 24 24">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
              </svg>
              LOGIN / KHỞI CHẠY AI BÓC TÁCH
            </button>
          </div>

        </section>

        <!-- MIDDLE ROW: 3 GAUGES + EQUALIZER + SALES REP PROFILE -->
        <section class="middle-gauges-profile-grid">
          
          <div class="gauges-card">
            <div class="gauge-item">
              <div class="gauge-ring-box">
                <svg viewBox="0 0 64 64">
                  <circle class="gauge-ring-bg" cx="32" cy="32" r="25"></circle>
                  <circle class="gauge-ring-val" cx="32" cy="32" r="25" stroke="#f97316" style="stroke-dashoffset: 86;"></circle>
                </svg>
                <span class="gauge-percent-text">45%</span>
              </div>
              <span class="gauge-label-text">Tự duyệt</span>
            </div>

            <div class="gauge-item">
              <div class="gauge-ring-box">
                <svg viewBox="0 0 64 64">
                  <circle class="gauge-ring-bg" cx="32" cy="32" r="25"></circle>
                  <circle class="gauge-ring-val" cx="32" cy="32" r="25" stroke="#ec4899" style="stroke-dashoffset: 62;"></circle>
                </svg>
                <span class="gauge-percent-text">60%</span>
              </div>
              <span class="gauge-label-text">Kho sẵn</span>
            </div>

            <div class="gauge-item">
              <div class="gauge-ring-box">
                <svg viewBox="0 0 64 64">
                  <circle class="gauge-ring-bg" cx="32" cy="32" r="25"></circle>
                  <circle class="gauge-ring-val" cx="32" cy="32" r="25" stroke="#10b981" style="stroke-dashoffset: 39;"></circle>
                </svg>
                <span class="gauge-percent-text">75%</span>
              </div>
              <span class="gauge-label-text">Chốt đơn</span>
            </div>
          </div>

          <div class="equalizer-card">
            <span class="eq-tag">MAX</span>
            <div class="eq-bars-group">
              <div class="eq-bar bar-orange"></div>
              <div class="eq-bar bar-purple"></div>
              <div class="eq-bar bar-cyan"></div>
            </div>
            <span class="eq-tag">MIN</span>
          </div>

          <div class="profile-rep-card">
            <div class="rep-info-left">
              <div class="rep-avatar-purple">
                <svg viewBox="0 0 24 24">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </div>
              <div class="rep-name-title">
                <h4>Ian Rafly (Sale-01)</h4>
                <p>Chuyên viên Tư vấn Hạ tầng Minh An</p>
              </div>
            </div>
            <div class="rep-rating-right">
              <div class="rate-tag">RATING</div>
              <div class="rate-score">5 <span class="rate-star-icon">★</span></div>
            </div>
          </div>

        </section>

        <!-- INTERACTIVE DISCOUNT SLIDER -->
        <section class="slider-strip-card">
          <div class="slider-track-wrap">
            <span>−</span>
            <input type="range" min="0" max="15" value="2" class="input-range-styled" id="discount-live-slider" oninput="updateSliderLabel(this.value)">
            <span>+</span>
          </div>
          <div class="slider-info-badge" id="slider-val-badge">
            Mức Chiết Khấu: 2% (Ngưỡng tự duyệt)
          </div>
        </section>

        <!-- ROW 2: 7-STEP PIPELINE -->
        <section class="pipeline-diagram-card">
          <div class="pipeline-head-row">
            <h3>
              <svg style="width:16px; height:16px; stroke:#10b981; fill:none; stroke-width:2;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
              QUY TRÌNH XỬ LÝ CƠ HỘI BÁN HÀNG B2B - MINH AN COMPANY (SƠ ĐỒ TRỰC QUAN)
            </h3>
            <span class="pipeline-ready-tag">SẴN SÀNG TIẾP NHẬN</span>
          </div>

          <div class="steps-chain-row">
            <div class="chain-step-pill active" id="step-node-1" onclick="focusStep(1)">
              <span class="step-num-text">Bước 1</span>
              <span class="step-name-text">Bắt đầu: Tiếp nhận</span>
            </div>
            <div class="chain-step-pill" id="step-node-2" onclick="focusStep(2)">
              <span class="step-num-text">Bước 2</span>
              <span class="step-name-text">Phân loại & Kiểm tra</span>
            </div>
            <div class="chain-step-pill" id="step-node-3" onclick="focusStep(3)">
              <span class="step-num-text">Điều kiện</span>
              <span class="step-name-text">Có đủ thông tin?</span>
            </div>
            <div class="chain-step-pill" id="step-node-4" onclick="focusStep(4)">
              <span class="step-num-text">Bước 3</span>
              <span class="step-name-text">Tạo Hồ sơ & Gán NVKD</span>
            </div>
            <div class="chain-step-pill" id="step-node-5" onclick="focusStep(5)">
              <span class="step-num-text">Bước 4</span>
              <span class="step-name-text">Thẩm định Tồn & Giá</span>
            </div>
            <div class="chain-step-pill" id="step-node-6" onclick="focusStep(6)">
              <span class="step-num-text">Bước 5</span>
              <span class="step-name-text">Lập Báo giá & Đề xuất</span>
            </div>
            <div class="chain-step-pill" id="step-node-7" onclick="focusStep(7)">
              <span class="step-num-text">Bước 6 & 7</span>
              <span class="step-name-text">Vượt quyền / Kết thúc</span>
            </div>
          </div>
        </section>

        <!-- ROW 3: RESIZABLE SPLIT AREA -->
        <section class="split-resizable-container" id="split-container">
          
          <div class="split-col-left" id="split-left">
            <div class="scenarios-card">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="font-size:13px; font-weight:800; color:var(--text-main); display:flex; align-items:center; gap:6px;">
                  <svg style="width:15px; height:15px; stroke:var(--mint-text); fill:none; stroke-width:2;" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                  KỊCH BẢN THỬ NGHIỆM MẪU
                </h3>
                <span style="font-size:11px; font-weight:700; color:var(--text-muted);">Chọn 1-Click</span>
              </div>

              <div class="scenario-item-box selected" id="scen-p1" onclick="selectScenario('p1')">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span class="scen-title-bold">Kịch bản 1: Yêu cầu chuẩn, đủ thông tin</span>
                  <span style="background:var(--mint-subtle); color:var(--mint-text); font-size:10px; font-weight:800; padding:2px 8px; border-radius:9999px;">Chuẩn / Tự duyệt</span>
                </div>
                <p class="scen-desc-txt">Công ty Sao Việt cần 2 Dell R750 + 1 Cisco 9200L. Đủ thông tin, chiết khấu 4% trong thẩm quyền NVKD.</p>
              </div>

              <div class="scenario-item-box" id="scen-p2" onclick="selectScenario('p2')">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span class="scen-title-bold">Kịch bản 2: Thiếu thông tin quan trọng</span>
                  <span style="background:#fecdd3; color:#be123c; font-size:10px; font-weight:800; padding:2px 8px; border-radius:9999px;">Thiếu thông tin</span>
                </div>
                <p class="scen-desc-txt">Công ty Nam Hải hỏi mua máy chủ/switch, thiếu số lượng và cấu hình. Kích hoạt 'Yêu cầu KH làm rõ/bổ sung'.</p>
              </div>

              <div class="scenario-item-box" id="scen-p3" onclick="selectScenario('p3')">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span class="scen-title-bold">Kịch bản 3: Vượt thẩm quyền (Chiết khấu 10%)</span>
                  <span style="background:#fef3c7; color:#b45309; font-size:10px; font-weight:800; padding:2px 8px; border-radius:9999px;">Vượt quyền >5%</span>
                </div>
                <p class="scen-desc-txt">Tập đoàn An Thịnh cần đơn hàng 800 triệu, xin chiết khấu 10%. Kích hoạt nhánh 'Trưởng phòng duyệt'.</p>
              </div>

              <div class="scenario-item-box" id="scen-p4" onclick="selectScenario('p4')">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span class="scen-title-bold">Kịch bản 4: Lead time & Tồn ATP</span>
                  <span style="background:#e0e7ff; color:#3730a3; font-size:10px; font-weight:800; padding:2px 8px; border-radius:9999px;">Kho ATP</span>
                </div>
                <p class="scen-desc-txt">LogiTech cần 4 Server Dell R650 + 2 Switch Cisco giao gấp 3 ngày. Kiểm tra tồn ATP và cảnh báo lead-time.</p>
              </div>
            </div>
          </div>

          <div class="split-resizer-handle" id="split-resizer"></div>

          <div class="split-col-right" id="split-right">
            <div class="execution-result-card" id="execution-card">
              <div class="empty-sparkle-icon">
                <svg style="width:26px; height:26px; fill:currentColor;" viewBox="0 0 24 24">
                  <path d="M12 2l2.4 7.2h7.6l-6 4.8 2.4 7.2-6.4-4.8-6.4 4.8 2.4-7.2-6-4.8h7.6z"/>
                </svg>
              </div>
              <h4 style="font-size:15px; font-weight:800; color:var(--text-main); margin-bottom:6px;">Chưa có yêu cầu nào được xử lý</h4>
              <p style="font-size:12px; color:var(--text-sub); max-width:420px; line-height:1.5; margin-bottom:16px;">
                Hãy chọn một trong 4 kịch bản mẫu ở bên trái hoặc dán văn bản yêu cầu của khách hàng, sau đó bấm nút khởi chạy quy trình.
              </p>
              <button class="btn-sunset-highlight" onclick="executeCurrentScenario()">
                <svg style="width:14px; height:14px; fill:currentColor;" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                Kích hoạt AI Agent Xử lý Quy trình
              </button>
            </div>
          </div>

        </section>

        <!-- ROW 4: BẢNG HỒ SƠ CƠ HỘI (GOOGLE SHEETS CRM) -->
        <section class="crm-table-card" id="crm-table-section">
          <div class="crm-table-header-row">
            <div class="crm-title-area">
              <h3>Bảng Hồ sơ Cơ hội (Google Sheets CRM)</h3>
              <p>Kiểm soát duyệt chiết khấu 10%, tích Checkbox sinh Docs & gửi URL cho khách</p>
            </div>
            <div class="crm-action-pills-wrap">
              <button class="btn-pill-action btn-pill-pink" onclick="clearAllData()">
                <svg style="width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:2;" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                XÓA SẠCH DỮ LIỆU
              </button>
              <button class="btn-pill-action btn-pill-mint" onclick="fetchData()">
                <svg style="width:14px; height:14px; fill:currentColor;" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                Nạp dữ liệu mẫu
              </button>
              <button class="btn-pill-action btn-pill-teal" onclick="exportCsv()">
                <svg style="width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:2;" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                Xuất CSV
              </button>
            </div>
          </div>

          <div style="overflow-x:auto;">
            <table class="crm-data-table" id="crm-table">
              <thead>
                <tr>
                  <th>Mã Cơ hội</th>
                  <th>Khách hàng</th>
                  <th>NVKD Phụ trách</th>
                  <th>Tổng Niêm Yết</th>
                  <th>Chiết khấu (%)</th>
                  <th>Sau Chiết khấu</th>
                  <th>Trạng thái Phê duyệt</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody id="crm-table-body">
                <!-- Dynamically populated -->
              </tbody>
            </table>
          </div>
        </section>

      </main>
    </div>

    <!-- ========================================================
         VIEW 2: GIAO DIỆN KHÁCH HÀNG (DEDICATED CUSTOMER PORTAL)
    ======================================================== -->
    <div id="customer-page-view" style="display:none; width:100%;">
      <main class="customer-portal-board">
        
        <!-- HEADER CỦA KHÁCH HÀNG -->
        <header class="studio-header-bar">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="brand-squircle-plus">
              <svg style="width:22px; height:22px; stroke:white; fill:none; stroke-width:3; stroke-linecap:round;" viewBox="0 0 24 24">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </div>
            <div>
              <h2 style="font-size:18px; font-weight:800; color:var(--text-main);">Minh An AI • Cổng Khách Hàng Doanh Nghiệp</h2>
              <p style="font-size:12px; color:var(--text-sub);">Hệ thống Báo giá Tự động & Tư vấn Hạ tầng B2B 24/7</p>
            </div>
          </div>

          <div style="display:flex; align-items:center; gap:12px;">
            <div style="background:#ffffff; border:1px solid var(--card-border); padding:6px 14px; border-radius:9999px; font-size:12px; font-weight:700; color:var(--mint-text); display:flex; align-items:center; gap:6px;">
              <span style="font-size:8px;">●</span> AI Tư Vấn Đang Trực Tuyến
            </div>
            <!-- NÚT CHUYỂN VỀ DOANH NGHIỆP MINH AN -->
            <button onclick="setRole('business')" style="background:#ffffff; border:1.5px solid #10b981; color:#059669; padding:8px 18px; border-radius:9999px; font-size:12.5px; font-weight:800; cursor:pointer; display:flex; align-items:center; gap:8px; transition:0.2s;" onmouseover="this.style.background='#10b981'; this.style.color='#fff';" onmouseout="this.style.background='#fff'; this.style.color='#059669';">
              <svg style="width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:2;" viewBox="0 0 24 24">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
              </svg>
              Về Giao diện Doanh nghiệp Minh An
            </button>
          </div>
        </header>

        <!-- BANNER CHÀO MỪNG KHÁCH HÀNG -->
        <section class="customer-hero-card">
          <div class="customer-hero-text">
            <h2>Xin chào Quý Khách Hàng Doanh Nghiệp! 👋</h2>
            <p>Nhận báo giá thiết bị Máy chủ Dell & Thiết bị mạng Cisco chính hãng trong vòng <b>30 giây</b> được AI bóc tách tự động.</p>
          </div>
          <div style="display:flex; gap:10px;">
            <div style="background:var(--mint-subtle); padding:10px 18px; border-radius:14px; text-align:center;">
              <div style="font-size:16px; font-weight:800; color:var(--mint-text);">Cam kết SLA</div>
              <div style="font-size:11px; color:var(--text-sub);">Phản hồi ≤ 4 giờ</div>
            </div>
            <div style="background:var(--pink-pill-bg); padding:10px 18px; border-radius:14px; text-align:center;">
              <div style="font-size:16px; font-weight:800; color:var(--pink-text);">Chiết khấu B2B</div>
              <div style="font-size:11px; color:var(--text-sub);">Lên đến 10%</div>
            </div>
          </div>
        </section>

        <!-- KHUNG 2 CỘT: FORM GỬI YÊU CẦU & CHATBOT TƯ VẤN TRỰC TIẾP -->
        <section class="customer-grid-layout">
          
          <!-- CỘT 1: FORM GỬI YÊU CẦU BÁO GIÁ (RFQ) -->
          <div class="customer-rfq-card">
            <div style="border-bottom:1px solid var(--card-border); padding-bottom:12px;">
              <h3 style="font-size:15px; font-weight:800; color:var(--text-main); display:flex; align-items:center; gap:8px;">
                <svg style="width:18px; height:18px; stroke:#10b981; fill:none; stroke-width:2;" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                Gửi Yêu Cầu Báo Giá Nhanh (RFQ Form)
              </h3>
              <p style="font-size:12px; color:var(--text-sub); margin-top:2px;">Điền thông tin hoặc chọn mẫu có sẵn để AI lập báo giá ngay</p>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
              <div class="form-group-field">
                <label>Tên Doanh nghiệp / Tổ chức (*)</label>
                <input type="text" id="cust-company" class="form-input-styled" placeholder="VD: Công ty TNHH Giải Pháp Công Nghệ ABC" value="Công ty CP Viễn Thông Thăng Long" />
              </div>
              <div class="form-group-field">
                <label>Người liên hệ & Số điện thoại (*)</label>
                <input type="text" id="cust-contact" class="form-input-styled" placeholder="VD: Anh Tuấn - 0988 123 456" value="Anh Lê Hoàng Long (0918 222 333)" />
              </div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
              <div class="form-group-field">
                <label>Email nhận báo giá (*)</label>
                <input type="email" id="cust-email" class="form-input-styled" placeholder="contact@congty.com" value="long.le@thanglong-telecom.vn" />
              </div>
              <div class="form-group-field">
                <label>Mức chiết khấu mong muốn (%):</label>
                <input type="number" id="cust-discount" class="form-input-styled" min="0" max="15" value="5" />
              </div>
            </div>

            <div class="form-group-field">
              <label>Mô tả nhu cầu thiết bị / Cấu hình chi tiết (*)</label>
              <textarea id="cust-content" class="form-input-styled form-textarea-styled" placeholder="Nhập cấu hình, số lượng Server Dell, Switch Cisco hoặc dán yêu cầu dự án vào đây...">Cần 02 Máy chủ Dell PowerEdge R750 (2x Intel Xeon Gold 5318Y, 64GB RAM, 2x 960GB SSD) và 01 Switch Cisco Catalyst 9200L 24 Ports PoE+. Giao hàng tại Hà Nội.</textarea>
            </div>

            <!-- GỢI Ý MẪU 1-CLICK -->
            <div>
              <label style="font-size:11.5px; font-weight:700; color:var(--text-sub);">Hoặc chọn nhanh kịch bản mẫu:</label>
              <div class="quick-preset-chips">
                <button class="chip-sample-btn" onclick="fillCustomerPreset('p1')">Mẫu 1: 2 Dell R750 + 1 Cisco 9200L (Chuẩn)</button>
                <button class="chip-sample-btn" onclick="fillCustomerPreset('p3')">Mẫu 2: Đơn hàng lớn 800 Triệu (Chiết khấu 10%)</button>
                <button class="chip-sample-btn" onclick="fillCustomerPreset('p4')">Mẫu 3: Cần giao gấp 3 ngày (Dell R650)</button>
              </div>
            </div>

            <button class="btn-sunset-highlight" style="padding:12px 20px; font-size:13.5px; justify-content:center;" onclick="submitCustomerRfq()">
              <svg style="width:16px; height:16px; fill:currentColor;" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
              GỬI YÊU CẦU & KÍCH HOẠT AI LẬP BÁO GIÁ NGAY
            </button>

            <!-- KẾT QUẢ XỬ LÝ CHO KHÁCH HÀNG -->
            <div id="cust-rfq-status" style="display:none; background:var(--card-bg-subtle); border:1px solid var(--card-border); border-radius:14px; padding:14px;"></div>
          </div>

          <!-- CỘT 2: TRỢ LÝ AI TƯ VẤN TRỰC TIẾP 24/7 -->
          <div class="customer-chat-card">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--card-border); padding-bottom:12px;">
              <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:30px; height:30px; border-radius:50%; background:var(--mint-gradient); display:flex; align-items:center; justify-content:center; color:white; font-size:14px;">🤖</div>
                <div>
                  <h4 style="font-size:13.5px; font-weight:800; color:var(--text-main);">Trợ Lý Tư Vấn Thiết Bị B2B</h4>
                  <span style="font-size:11px; color:var(--mint-text);">Phản hồi tức thì qua Catalog Minh An</span>
                </div>
              </div>
            </div>

            <!-- LỊCH SỬ CHAT CỦA KHÁCH -->
            <div class="customer-chat-messages" id="customer-chat-stream">
              <div class="chat-bubble-ai">
                Xin chào Quý khách! Tôi là AI Tư vấn kỹ thuật của Công ty Minh An.
                <br><br>Quý khách cần tư vấn cấu hình <b>Máy chủ Dell PowerEdge</b>, thiết bị chuyển mạch <b>Cisco Catalyst</b> hay kiểm tra tiến độ đơn hàng?
              </div>
            </div>

            <!-- GỢI Ý CÂU HỎI NHANH -->
            <div style="display:flex; gap:6px; flex-wrap:wrap; padding:8px 0;">
              <button onclick="askCustomerAi('Dell R750 có sẵn hàng không và bảo hành bao lâu?')" style="background:var(--card-bg-subtle); border:1px solid var(--card-border); padding:4px 10px; border-radius:9999px; font-size:11px; color:var(--text-sub); cursor:pointer;">❓ Dell R750 có sẵn hàng không?</button>
              <button onclick="askCustomerAi('Cisco 9200L 24 Ports PoE+ có mã nào và giá tham khảo bao nhiêu?')" style="background:var(--card-bg-subtle); border:1px solid var(--card-border); padding:4px 10px; border-radius:9999px; font-size:11px; color:var(--text-sub); cursor:pointer;">❓ Báo giá Switch Cisco 9200L</button>
            </div>

            <!-- Ô NHẬP TIN NHẮN -->
            <div style="display:flex; gap:8px; border-top:1px solid var(--card-border); padding-top:12px;">
              <input type="text" id="cust-chat-inp" class="form-input-styled" style="flex:1;" placeholder="Nhập câu hỏi kỹ thuật hoặc yêu cầu..." onkeydown="if(event.key==='Enter') sendCustomerChat()" />
              <button onclick="sendCustomerChat()" style="background:var(--mint-gradient); color:white; border:none; border-radius:12px; padding:0 18px; font-weight:800; cursor:pointer;">Gửi</button>
            </div>
          </div>

        </section>

        <!-- BẢNG TRA CỨU TIẾN ĐỘ & BÁO GIÁ CỦA TÔI -->
        <section class="customer-history-card">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <h3 style="font-size:14px; font-weight:800; color:var(--text-main);">Hồ sơ Báo giá & Đơn hàng của Quý khách</h3>
              <p style="font-size:12px; color:var(--text-sub);">Tra cứu tiến độ duyệt chiết khấu, mở bản Báo giá chính thức và ký hợp đồng trực tuyến</p>
            </div>
            <button onclick="fetchData()" style="background:var(--card-bg-subtle); border:1px solid var(--card-border); padding:6px 14px; border-radius:9999px; font-size:12px; font-weight:700; cursor:pointer;">🔄 Cập nhật tiến độ</button>
          </div>

          <div style="overflow-x:auto;">
            <table class="crm-data-table">
              <thead>
                <tr>
                  <th>Mã Yêu Cầu</th>
                  <th>Đơn vị Khách hàng</th>
                  <th>Chuyên viên Phụ trách</th>
                  <th>Tổng giá trị</th>
                  <th>Chiết khấu</th>
                  <th>Trạng thái Hồ sơ</th>
                  <th>Báo giá Chính thức</th>
                </tr>
              </thead>
              <tbody id="cust-table-body">
                <!-- Dynamically populated -->
              </tbody>
            </table>
          </div>
        </section>

      </main>
    </div>

  </div>

  <!-- FLOATING CHAT ASSISTANT BUBBLE -->
  <div class="ai-chat-bubble-bot" onclick="toggleAiChat()" title="Chat với AI Tư vấn Minh An">
    <svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
  </div>

  <!-- CHAT DRAWER NỔI -->
  <div class="ai-chat-drawer" id="ai-chat-drawer">
    <div style="background:var(--mint-gradient); color:white; padding:16px 20px; display:flex; justify-content:space-between; align-items:center;">
      <div style="display:flex; align-items:center; gap:10px;">
        <div style="width:10px; height:10px; border-radius:50%; background:#fff;"></div>
        <h4 style="font-size:14px; font-weight:800;">Minh An AI Consultant</h4>
      </div>
      <button onclick="toggleAiChat()" style="background:none; border:none; color:white; font-size:18px; cursor:pointer;">✕</button>
    </div>
    <div style="flex:1; padding:16px; overflow-y:auto; display:flex; flex-direction:column; gap:10px;" id="ai-chat-history">
      <div style="background:var(--card-bg-subtle); padding:10px 14px; border-radius:14px; font-size:12.5px; border:1px solid var(--card-border); align-self:flex-start;">
        Xin chào! Tôi là Trợ lý AI Tư vấn B2B Minh An. Bạn cần hỗ trợ kiểm tra mã hàng Dell/Cisco, tồn kho hay chính sách duyệt chiết khấu?
      </div>
    </div>
    <div style="padding:14px; border-top:1px solid var(--card-border); display:flex; gap:8px;">
      <input type="text" id="ai-query-input" placeholder="Nhập câu hỏi tư vấn..." style="flex:1; border:1px solid var(--card-border); border-radius:12px; padding:8px 12px; font-size:12.5px; outline:none;" onkeydown="if(event.key==='Enter') sendAiMessage()" />
      <button onclick="sendAiMessage()" style="background:var(--mint-gradient); color:white; border:none; border-radius:12px; padding:8px 16px; font-weight:800; cursor:pointer;">Gửi</button>
    </div>
  </div>

  <!-- GLASS CONTROL MODAL -->
  <div class="glass-control-modal" id="glass-modal" onclick="if(event.target===this) closeGlassControlModal()">
    <div class="glass-control-card">
      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--card-border); padding-bottom:12px;">
        <h3 style="font-size:15px; font-weight:800; color:var(--text-main);">☷ Bảng Điều Khiển Tùy Biến Giao Diện</h3>
        <button onclick="closeGlassControlModal()" style="background:none; border:none; font-size:18px; cursor:pointer; color:var(--text-sub);">✕</button>
      </div>

      <div class="control-row">
        <span class="control-label">Tỉ lệ giao diện (UI Scale):</span>
        <input type="range" min="0.75" max="1.3" step="0.05" value="1" class="control-slider" oninput="applyScale(this.value)">
        <span style="font-size:12px; font-weight:800; width:45px; text-align:right;" id="scale-val-disp">100%</span>
      </div>

      <div class="control-row">
        <span class="control-label">Độ rộng Menu bên trái (Sidebar):</span>
        <input type="range" min="200" max="340" step="10" value="245" class="control-slider" oninput="applySidebarWidth(this.value)">
        <span style="font-size:12px; font-weight:800; width:45px; text-align:right;" id="sidebar-val-disp">245px</span>
      </div>

      <div class="control-row">
        <span class="control-label">Cỡ chữ chung (Font size):</span>
        <input type="range" min="12" max="16" step="0.5" value="13.5" class="control-slider" oninput="applyFontSize(this.value)">
        <span style="font-size:12px; font-weight:800; width:45px; text-align:right;" id="font-val-disp">13.5px</span>
      </div>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:10px;">
        <button onclick="resetCustomizations()" style="padding:8px 16px; border-radius:12px; border:1px solid var(--card-border); background:var(--card-bg-subtle); cursor:pointer; font-weight:700;">Mặc định</button>
        <button onclick="closeGlassControlModal()" style="padding:8px 18px; border-radius:12px; border:none; background:var(--mint-gradient); color:white; cursor:pointer; font-weight:800;">Đóng</button>
      </div>
    </div>
  </div>

  <script>
    let crmData = [];
    let currentRole = 'business';
    let selectedScenarioKey = 'p1';

    const PRESETS = {
      p1: {
        customer_name: "Công ty Cổ phần Công Nghệ Sao Việt",
        contact_person: "Anh Trần Quang Minh (Trưởng phòng CNTT)",
        email: "minh.tran@saoviet-tech.vn",
        phone: "0903 123 456",
        discount_pct: 4,
        raw_content: "Chào Minh An, chúng tôi cần 02 Máy chủ Dell PowerEdge R750 (2x Xeon Silver 4314, 64GB RAM, 2x 960GB SSD SAS) và 01 Switch Cisco Catalyst 9200L 24 Ports PoE+. Chiết khấu 4% giúp bên mình nhé."
      },
      p2: {
        customer_name: "Công ty TNHH Vận tải Nam Hải",
        contact_person: "Chị Lê Thu Trang",
        email: "trang.le@namhai-logistics.vn",
        phone: "0912 345 678",
        discount_pct: 0,
        raw_content: "Bên mình đang cần mua máy chủ Dell và switch mạng cho văn phòng mới, gửi báo giá gấp cho mình."
      },
      p3: {
        customer_name: "Tập đoàn Đầu tư An Thịnh",
        contact_person: "Ông Vũ Đức An (Giám đốc Khối Mua sắm)",
        email: "an.vu@anthinhgroup.vn",
        phone: "0988 777 999",
        discount_pct: 10,
        raw_content: "An Thịnh chuẩn bị mở trung tâm dữ liệu mới. Chúng tôi cần 04 Server Dell PowerEdge R750 cấu hình cao và 02 Thiết bị mạng Cisco Catalyst 9300 48 Ports. Tổng giá trị đơn hàng trên 800 triệu, xin chiết khấu 10% để ký hợp đồng ngay."
      },
      p4: {
        customer_name: "Công ty Cổ phần Giải pháp LogiTech",
        contact_person: "Anh Hoàng Quốc Hưng",
        email: "hung.hoang@logitech-vietnam.vn",
        phone: "0934 567 890",
        discount_pct: 3,
        raw_content: "Cần gấp 04 Máy chủ Dell PowerEdge R650 và 02 Thiết bị mạng Cisco Catalyst 9200L 48 Ports. Yêu cầu giao hàng trong vòng 3 ngày tới chi nhánh Hà Nội."
      }
    };

    // ĐIỀU HƯỚNG GIỮA DOANH NGHIỆP VÀ KHÁCH HÀNG (TRANG RIÊNG BIỆT)
    function setRole(role) {
      currentRole = role;
      const bView = document.getElementById('business-page-view');
      const cView = document.getElementById('customer-page-view');

      if (role === 'customer') {
        bView.style.display = 'none';
        cView.style.display = 'flex';
        history.pushState({ role: 'customer' }, '', '/customer');
        document.title = "Minh An AI - Cổng Tiếp Nhận Khách Hàng";
      } else {
        cView.style.display = 'none';
        bView.style.display = 'flex';
        history.pushState({ role: 'business' }, '', '/');
        document.title = "Minh An AI - B2B AI Agent Studio";
      }
    }

    window.addEventListener('popstate', (e) => {
      const path = window.location.pathname;
      if (path === '/customer') setRole('customer');
      else setRole('business');
    });

    async function fetchData() {
      try {
        const res = await fetch('/api/crm_records');
        crmData = await res.json();
        renderTable(crmData);
        renderCustomerTable(crmData);
      } catch (e) { console.error("Lỗi tải dữ liệu:", e); }
    }

    function renderTable(data) {
      const tb = document.getElementById('crm-table-body');
      if (!tb) return;
      if (!data || data.length === 0) {
        tb.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:20px; color:var(--text-muted);">Chưa có hồ sơ CRM nào.</td></tr>';
        return;
      }
      tb.innerHTML = data.map(r => {
        let badgeClass = 'badge-pending';
        if (r.approval_status.includes('Đúng thẩm quyền') || r.approval_status.includes('Đã duyệt')) {
          badgeClass = 'badge-approved';
        } else if (r.approval_status.includes('Chốt đơn') || r.approval_status.includes('Đã ký PO')) {
          badgeClass = 'badge-closed';
        }

        const isPending = r.approval_status.includes('Chờ Trưởng phòng duyệt');
        const hasQuote = r.checkbox_create_quote;

        return `
          <tr>
            <td style="font-weight:800; color:var(--mint-text);">${r.opp_id}</td>
            <td>
              <div style="font-weight:700;">${r.customer_name}</div>
              <div style="font-size:11px; color:var(--text-muted);">${r.contact_person || ''}</div>
            </td>
            <td>${r.assigned_rep}</td>
            <td>${Number(r.subtotal).toLocaleString('vi-VN')} đ</td>
            <td style="font-weight:700; color:${r.discount_pct > 5 ? 'var(--orange-accent)' : 'inherit'};">${r.discount_pct}%</td>
            <td style="font-weight:800; color:var(--text-main);">${Number(r.final_total).toLocaleString('vi-VN')} đ</td>
            <td><span class="status-badge-pill ${badgeClass}">${r.approval_status}</span></td>
            <td>
              <div style="display:flex; gap:6px; flex-wrap:wrap;">
                ${isPending ? `
                  <button onclick="managerDecision('${r.opp_id}', 'approve')" style="background:#10b981; color:white; border:none; padding:4px 10px; border-radius:8px; font-size:11px; font-weight:800; cursor:pointer;">Duyệt 10%</button>
                  <button onclick="managerDecision('${r.opp_id}', 'reject')" style="background:#f43f5e; color:white; border:none; padding:4px 8px; border-radius:8px; font-size:11px; font-weight:800; cursor:pointer;">Từ chối</button>
                ` : ''}
                ${!hasQuote ? `
                  <button onclick="triggerQuote('${r.opp_id}')" style="background:var(--sunset-gradient); color:white; border:none; padding:4px 10px; border-radius:8px; font-size:11px; font-weight:800; cursor:pointer;">Tạo Báo Giá Docs</button>
                ` : `
                  <a href="${r.quote_doc_url}" target="_blank" style="background:#3b82f6; color:white; text-decoration:none; padding:4px 10px; border-radius:8px; font-size:11px; font-weight:800; display:inline-block;">Mở Google Docs ↗</a>
                `}
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }

    function renderCustomerTable(data) {
      const tb = document.getElementById('cust-table-body');
      if (!tb) return;
      if (!data || data.length === 0) {
        tb.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:20px; color:var(--text-muted);">Quý khách chưa gửi yêu cầu báo giá nào. Hãy điền form bên trên để nhận báo giá!</td></tr>';
        return;
      }
      tb.innerHTML = data.map(r => {
        let badgeClass = 'badge-pending';
        if (r.approval_status.includes('Đúng thẩm quyền') || r.approval_status.includes('Đã duyệt')) {
          badgeClass = 'badge-approved';
        } else if (r.approval_status.includes('Chốt đơn') || r.approval_status.includes('Đã ký PO')) {
          badgeClass = 'badge-closed';
        }

        return `
          <tr>
            <td style="font-weight:800; color:var(--mint-text);">${r.opp_id}</td>
            <td><b>${r.customer_name}</b></td>
            <td>${r.assigned_rep}</td>
            <td style="font-weight:800;">${Number(r.final_total).toLocaleString('vi-VN')} đ</td>
            <td><b style="color:var(--orange-accent);">${r.discount_pct}%</b></td>
            <td><span class="status-badge-pill ${badgeClass}">${r.approval_status}</span></td>
            <td>
              <div style="display:flex; gap:6px;">
                <a href="${r.quote_doc_url}" target="_blank" style="background:var(--mint-gradient); color:white; text-decoration:none; padding:5px 12px; border-radius:8px; font-size:11px; font-weight:800; display:inline-flex; align-items:center; gap:4px;">
                  📄 Xem Docs Báo Giá ↗
                </a>
                <button onclick="alert('Đã xác nhận chốt đơn! NVKD phụ trách sẽ gửi hợp đồng chính thức tới Quý khách.')" style="background:var(--sunset-gradient); color:white; border:none; padding:5px 12px; border-radius:8px; font-size:11px; font-weight:800; cursor:pointer;">
                  ✍ Ký Đơn PO
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }

    // FORM CỦA KHÁCH HÀNG
    function fillCustomerPreset(key) {
      const p = PRESETS[key];
      if (!p) return;
      document.getElementById('cust-company').value = p.customer_name;
      document.getElementById('cust-contact').value = p.contact_person + ' (' + p.phone + ')';
      document.getElementById('cust-email').value = p.email;
      document.getElementById('cust-discount').value = p.discount_pct;
      document.getElementById('cust-content').value = p.raw_content;
    }

    async function submitCustomerRfq() {
      const company = document.getElementById('cust-company').value.trim();
      const contact = document.getElementById('cust-contact').value.trim();
      const email = document.getElementById('cust-email').value.trim();
      const disc = parseInt(document.getElementById('cust-discount').value) || 0;
      const content = document.getElementById('cust-content').value.trim();

      const statusBox = document.getElementById('cust-rfq-status');
      statusBox.style.display = 'block';
      statusBox.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px;">
          <div style="width:20px; height:20px; border:2px solid #10b981; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
          <span style="font-size:13px; font-weight:700; color:var(--text-main);">AI đang thẩm định tồn kho & lập bảng báo giá...</span>
        </div>
      `;

      try {
        const res = await fetch('/api/process_inquiry', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            customer_name: company || "Khách hàng Doanh nghiệp",
            contact_person: contact,
            email: email,
            phone: "",
            discount_pct: disc,
            raw_content: content
          })
        });
        const rec = await res.json();
        statusBox.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="color:#059669; font-weight:800; font-size:14px;">✔ Đã lập Báo Giá Thành Công: ${rec.opp_id}</span>
              <span class="status-badge-pill badge-approved">${rec.approval_status}</span>
            </div>
            <p style="font-size:12.5px; color:var(--text-sub);">${rec.ai_assessment}</p>
            <div style="display:flex; gap:10px; margin-top:4px;">
              <a href="${rec.quote_doc_url}" target="_blank" style="background:var(--mint-gradient); color:white; text-decoration:none; padding:8px 16px; border-radius:10px; font-size:12px; font-weight:800;">
                Mở Bản Báo Giá Google Docs ↗
              </a>
            </div>
          </div>
        `;
        fetchData();
      } catch (e) {
        statusBox.innerHTML = `<span style="color:#f43f5e; font-weight:700;">Lỗi gửi yêu cầu: ${e.message}</span>`;
      }
    }

    // CHAT CỦA KHÁCH HÀNG
    async function askCustomerAi(q) {
      document.getElementById('cust-chat-inp').value = q;
      await sendCustomerChat();
    }

    async function sendCustomerChat() {
      const inp = document.getElementById('cust-chat-inp');
      const q = inp.value.trim();
      if (!q) return;
      const stream = document.getElementById('customer-chat-stream');
      stream.innerHTML += `<div class="chat-bubble-user">${q}</div>`;
      inp.value = '';
      stream.scrollTop = stream.scrollHeight;

      try {
        const res = await fetch('/api/customer_chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ query: q })
        });
        const d = await res.json();
        stream.innerHTML += `<div class="chat-bubble-ai">${d.answer.replace(/\\n/g, '<br>')}</div>`;
        stream.scrollTop = stream.scrollHeight;
      } catch (e) {
        stream.innerHTML += `<div class="chat-bubble-ai" style="color:#f43f5e;">Lỗi kết nối AI: ${e.message}</div>`;
      }
    }

    // CÁC HÀM XỬ LÝ CHUNG CỦA BẢN DOANH NGHIỆP
    function selectScenario(key) {
      selectedScenarioKey = key;
      document.querySelectorAll('.scenario-item-box').forEach(el => el.classList.remove('selected'));
      const activeEl = document.getElementById('scen-' + key);
      if (activeEl) activeEl.classList.add('selected');
      
      const p = PRESETS[key];
      if (p) {
        document.getElementById('intake-company-input').value = p.customer_name;
        document.getElementById('intake-sku-input').value = p.raw_content;
        document.getElementById('discount-live-slider').value = p.discount_pct;
        updateSliderLabel(p.discount_pct);
      }
    }

    async function executeCurrentScenario() {
      const p = PRESETS[selectedScenarioKey];
      if (!p) return;
      await runPipeline(p);
    }

    async function applyPresetAndRun(key) {
      selectScenario(key);
      await executeCurrentScenario();
    }

    async function runPipelineFromInput() {
      const company = document.getElementById('intake-company-input').value.trim();
      const raw = document.getElementById('intake-sku-input').value.trim();
      const disc = parseInt(document.getElementById('discount-live-slider').value) || 0;
      await runPipeline({
        customer_name: company || "Khách hàng Doanh nghiệp",
        contact_person: "Đại diện mua hàng",
        email: "contact@company.com.vn",
        phone: "0900 000 000",
        discount_pct: disc,
        raw_content: raw || "Yêu cầu thiết bị máy chủ & switch"
      });
    }

    async function runPipeline(payload) {
      const card = document.getElementById('execution-card');
      card.innerHTML = `
        <div style="display:flex; flex-direction:column; align-items:center; gap:14px;">
          <div style="width:40px; height:40px; border:3px solid #10b981; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
          <h4 style="font-size:14px; font-weight:800; color:var(--text-main);">AI Agent đang bóc tách và định giá tự động...</h4>
          <p style="font-size:12px; color:var(--text-sub);">Kiểm tra tồn kho ATP, SKU catalog, chính sách duyệt chiết khấu</p>
        </div>
      `;

      for (let i = 1; i <= 7; i++) {
        document.getElementById('step-node-' + i).classList.remove('active');
      }

      let cur = 1;
      const stepTimer = setInterval(() => {
        if (cur <= 6) {
          document.getElementById('step-node-' + cur).classList.add('active');
          cur++;
        }
      }, 350);

      try {
        const res = await fetch('/api/process_inquiry', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const rec = await res.json();
        clearInterval(stepTimer);
        document.getElementById('step-node-7').classList.add('active');

        const isOver = rec.discount_pct > 10;
        card.innerHTML = `
          <div style="width:100%; text-align:left; display:flex; flex-direction:column; gap:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-size:15px; font-weight:800; color:var(--mint-text);">${rec.opp_id} - ${rec.customer_name}</span>
              <span class="status-badge-pill ${isOver ? 'badge-pending' : 'badge-approved'}">${rec.approval_status}</span>
            </div>
            
            <div style="background:var(--card-bg-subtle); padding:12px 14px; border-radius:12px; font-size:12.5px; border:1px solid var(--card-border);">
              ${rec.ai_assessment}
            </div>

            <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; font-size:12px;">
              <div><b>Tổng niêm yết:</b> ${Number(rec.subtotal).toLocaleString('vi-VN')} đ</div>
              <div><b>Chiết khấu:</b> ${rec.discount_pct}% (-${Number(rec.discount_amount).toLocaleString('vi-VN')} đ)</div>
              <div><b>Thành tiền:</b> <b style="color:#10b981;">${Number(rec.final_total).toLocaleString('vi-VN')} đ</b></div>
            </div>

            <div style="display:flex; gap:10px; margin-top:8px;">
              <a href="${rec.quote_doc_url}" target="_blank" style="background:var(--mint-gradient); color:white; text-decoration:none; padding:8px 18px; border-radius:12px; font-size:12px; font-weight:800;">
                Mở Google Docs Báo giá Chính thức ↗
              </a>
              <button onclick="scrollToTable()" style="background:var(--card-bg-subtle); border:1px solid var(--card-border); padding:8px 14px; border-radius:12px; font-size:12px; font-weight:700; cursor:pointer;">
                Xem chi tiết trong CRM
              </button>
            </div>
          </div>
        `;
        fetchData();
      } catch (e) {
        clearInterval(stepTimer);
        card.innerHTML = `<p style="color:#f43f5e; font-weight:700;">Lỗi xử lý quy trình: ${e.message}</p>`;
      }
    }

    async function managerDecision(opp_id, decision) {
      try {
        await fetch('/api/manager_decision', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ opp_id, decision })
        });
        fetchData();
      } catch (e) { console.error(e); }
    }

    async function triggerQuote(opp_id) {
      try {
        await fetch('/api/trigger_create_quote', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ opp_id })
        });
        fetchData();
      } catch (e) { console.error(e); }
    }

    function exportCsv() { window.location.href = '/api/export_csv'; }
    function clearAllData() { crmData = []; renderTable(crmData); renderCustomerTable(crmData); }

    function updateSliderLabel(val) {
      const badge = document.getElementById('slider-val-badge');
      if (val > 10) {
        badge.innerHTML = `Mức Chiết Khấu: ${val}% (<span style="color:#f43f5e;">Cần Trưởng phòng duyệt</span>)`;
      } else {
        badge.innerHTML = `Mức Chiết Khấu: ${val}% (Ngưỡng tự duyệt)`;
      }
    }

    function focusStep(num) {
      for (let i = 1; i <= 7; i++) {
        document.getElementById('step-node-' + i).classList.toggle('active', i === num);
      }
    }

    function scrollToTable() {
      document.getElementById('crm-table-section').scrollIntoView({ behavior: 'smooth' });
    }

    function openDiagramWindow() { window.open('/diagram', '_blank'); }

    /* CONTROLS RESIZE */
    function adjustScale(delta) {
      const root = document.documentElement;
      let cur = parseFloat(getComputedStyle(root).getPropertyValue('--ui-scale')) || 1;
      cur = Math.min(Math.max(cur + delta, 0.75), 1.3);
      root.style.setProperty('--ui-scale', cur);
      document.getElementById('scale-val-disp').innerText = Math.round(cur * 100) + '%';
    }

    function resetScale() {
      document.documentElement.style.setProperty('--ui-scale', 1);
      document.getElementById('scale-val-disp').innerText = '100%';
    }

    function applyScale(val) {
      document.documentElement.style.setProperty('--ui-scale', val);
      document.getElementById('scale-val-disp').innerText = Math.round(val * 100) + '%';
    }

    function applySidebarWidth(val) {
      document.documentElement.style.setProperty('--sidebar-width', val + 'px');
      document.getElementById('sidebar-val-disp').innerText = val + 'px';
    }

    function applyFontSize(val) {
      document.documentElement.style.setProperty('--font-base', val + 'px');
      document.getElementById('font-val-disp').innerText = val + 'px';
    }

    function resetCustomizations() {
      const root = document.documentElement;
      root.style.setProperty('--ui-scale', 1);
      root.style.setProperty('--sidebar-width', '245px');
      root.style.setProperty('--font-base', '13.5px');
    }

    function openGlassControlModal() { document.getElementById('glass-modal').style.display = 'flex'; }
    function closeGlassControlModal() { document.getElementById('glass-modal').style.display = 'none'; }

    function toggleSidebarCollapse() {
      const sb = document.getElementById('studio-sidebar');
      sb.classList.toggle('collapsed');
    }

    function toggleTheme() {
      const cur = document.body.getAttribute('data-theme');
      const next = (cur === 'dark') ? 'light' : 'dark';
      document.body.setAttribute('data-theme', next);
      document.getElementById('theme-btn-text').innerText = (next === 'dark') ? 'Chuyển Glow Sáng' : 'Chuyển Glow Tối';
    }

    function toggleAiChat() {
      const d = document.getElementById('ai-chat-drawer');
      d.style.display = (d.style.display === 'flex') ? 'none' : 'flex';
      if (d.style.display === 'flex') document.getElementById('ai-query-input').focus();
    }

    async function sendAiMessage() {
      const inp = document.getElementById('ai-query-input');
      const q = inp.value.trim();
      if (!q) return;
      const h = document.getElementById('ai-chat-history');
      h.innerHTML += `<div style="background:var(--mint-gradient); color:white; padding:10px 14px; border-radius:14px; font-size:12.5px; align-self:flex-end;">${q}</div>`;
      inp.value = '';
      try {
        const res = await fetch('/api/customer_chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ query: q })
        });
        const d = await res.json();
        h.innerHTML += `<div style="background:var(--card-bg-subtle); padding:10px 14px; border-radius:14px; font-size:12.5px; border:1px solid var(--card-border); align-self:flex-start;">${d.answer.replace(/\\n/g, '<br>')}</div>`;
        h.scrollTop = h.scrollHeight;
      } catch (e) { console.error(e); }
    }

    /* DRAGGABLE SPLITTER */
    const resizer = document.getElementById('split-resizer');
    const leftCol = document.getElementById('split-left');
    let isDragging = false;

    if (resizer && leftCol) {
      resizer.addEventListener('mousedown', (e) => {
        isDragging = true;
        resizer.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
      });

      window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const containerRect = document.getElementById('split-container').getBoundingClientRect();
        let leftWidth = e.clientX - containerRect.left;
        leftWidth = Math.max(200, Math.min(containerRect.width - 200, leftWidth));
        leftCol.style.width = leftWidth + 'px';
      });

      window.addEventListener('mouseup', () => {
        if (isDragging) {
          isDragging = false;
          resizer.classList.remove('dragging');
          document.body.style.cursor = 'default';
        }
      });
    }

    // Tự động kiểm tra URL khi mở trang
    if (window.location.pathname === '/customer') {
      setRole('customer');
    } else {
      setRole('business');
    }

    fetchData();
  </script>
  <style>
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
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

        if path in ("/", "/index.html", "/business", "/customer"):
            self._set_headers(content_type="text/html")
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif path == "/diagram":
            diag_file = os.path.join(BASE_DIR, "workflow_diagram.html")
            if os.path.exists(diag_file):
                self._set_headers(content_type="text/html")
                with open(diag_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(status=404)
                self.wfile.write(b"Diagram not found")
        elif path == "/diagram.svg":
            svg_file = os.path.join(BASE_DIR, "workflow_diagram.svg")
            if os.path.exists(svg_file):
                self._set_headers(content_type="image/svg+xml")
                with open(svg_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(status=404)
                self.wfile.write(b"Diagram SVG not found")
        elif path == "/api/crm_records":
            self._set_headers()
            self.wfile.write(json.dumps(crm_records, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/catalog":
            self._set_headers()
            if os.path.exists(CATALOG_PATH):
                with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(b"[]")
        elif path == "/api/export_csv":
            csv_lines = [
                "Mã Cơ hội,Khách hàng,Người liên hệ,NVKD Phụ trách,Tổng Niêm Yết,Chiết khấu,Thành tiền,Trạng thái Phê duyệt,Thời gian Triển khai,Checkbox Tạo Báo Giá,Link Docs Báo Giá,Nhận định AI"
            ]
            for r in crm_records:
                warn = r.get("ai_assessment", "").replace('"', '""')
                csv_lines.append(
                    f'"{r["opp_id"]}","{r["customer_name"]}","{r["contact_person"]}","{r["assigned_rep"]}",'
                    f'{r["subtotal"]},{r["discount_pct"]}%,{r["final_total"]},"{r["approval_status"]}",'
                    f'"{r["lead_time_days"]} ngày",{r.get("checkbox_create_quote", False)},"{r.get("quote_doc_url","")}","{warn}"'
                )
            csv_data = "\\ufeff" + "\\n".join(csv_lines)
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

        if path == "/api/customer_chat":
            q = req_data.get("query", "")
            res = call_customer_consultant(q, user_gemini_api_key)
            self._set_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/ai_chat":
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
                "quote_doc_url": f"https://docs.google.com/document/d/minhan-{opp.opportunity_id.lower()}-official-quote/edit",
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
                    target["approval_status"] = "Hoàn tất (Từ chối)"
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
    load_sample_crm_data()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), MinhAnServerHandler) as httpd:
        print("=" * 75)
        print(" CÔNG TY CÔNG NGHỆ MINH AN - B2B AI AGENT STUDIO (DUAL PORTALS)")
        print(f" Web Dashboard (Doanh nghiệp): http://localhost:{PORT}")
        print(f" Cổng Khách hàng (Customer):   http://localhost:{PORT}/customer")
        print(" Đang phục vụ trên cổng 8080...")
        print("=" * 75)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nĐã dừng máy chủ localhost.")


if __name__ == "__main__":
    run()
'''

with open("d:/AGENT/server.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated d:/AGENT/server.py with separate Customer Portal and Mint Inner Background!")

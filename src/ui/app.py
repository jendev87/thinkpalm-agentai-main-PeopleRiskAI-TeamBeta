import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Ensure src can be imported
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.graph import create_graph
from src.agents.state import IntentEnum
from src.automation.reporter import create_mitigation_docx, create_mitigation_pdf
from src.automation.notifier import send_manager_email
from src.automation.slack import dispatch_critical_alert
from src.automation.report_engine import generate_executive_pdf

st.set_page_config(page_title="PeopleRisk AI", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

import uuid
if "threads" not in st.session_state:
    st.session_state.threads = {}
if "active_thread_id" not in st.session_state:
    st.session_state.active_thread_id = None
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

if "agent_graph" not in st.session_state:
    try:
        from src.agents.graph import create_graph
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            st.session_state.agent_graph = create_graph("groq", "llama-3.3-70b-versatile", groq_key)
            st.session_state.ai_provider = "Groq"
    except Exception:
        pass

def render_header():
    st.markdown("""
    <style>
    /* ========================================== */
    /* 1. TYPOGRAPHY */
    /* ========================================== */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #94A3B8 !important;
        font-weight: 600 !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #FFFFFF !important;
    }

    /* ========================================== */
    /* 2. LAYOUT & VARIABLES */
    /* ========================================== */
    :root {
        --header-height: 72px;
    }

    /* Premium Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        transition: background 0.3s ease;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.4);
    }

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #0B0E14 !important;
        height: 100vh !important;
        overflow: hidden !important;
    }

    footer, [data-testid="stToolbar"], [data-testid="stHeaderActionElements"], .stAppDeployButton, #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }

    .block-container {
        padding-left: 0px !important;
        padding-right: 0px !important;
        padding-top: 24px !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }

    /* ========================================== */
    /* 3. SIDEBAR REDESIGN (PERMANENTLY OPEN) */
    /* ========================================== */
    [data-testid="stSidebar"] {
        min-width: 226px !important;
        max-width: 226px !important;
        background-color: #111827 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.03) !important;
        transform: translateX(0px) !important;
        margin-left: 0px !important;
        position: relative !important;
        visibility: visible !important;
        display: block !important;
    }
    
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    .stApp [data-testid="stSidebar"] button[kind="secondary"][data-testid="stBaseButton-secondary"],
    .stApp [data-testid="stSidebar"] button[kind="primary"][data-testid="stBaseButton-primary"] {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        justify-content: flex-start !important;
        text-align: left !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: background 0.15s ease, color 0.15s ease !important;
        height: auto !important;
        min-height: 0 !important;
        margin-bottom: 2px !important;
        white-space: nowrap !important;
    }
    
    .stApp [data-testid="stSidebar"] button[kind="secondary"][data-testid="stBaseButton-secondary"] *,
    .stApp [data-testid="stSidebar"] button[kind="primary"][data-testid="stBaseButton-primary"] * {
        white-space: nowrap !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    .stApp [data-testid="stSidebar"] button[kind="secondary"][data-testid="stBaseButton-secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.04) !important;
        background: rgba(255, 255, 255, 0.04) !important;
    }
    
    .stApp [data-testid="stSidebar"] button[kind="primary"][data-testid="stBaseButton-primary"] {
        color: #F8FAFC !important;
        background-color: rgba(37, 99, 235, 0.15) !important;
        background: rgba(37, 99, 235, 0.15) !important;
        box-shadow: inset 3px 0 0 0 #3B82F6 !important;
    }
    
    @keyframes fadeUp {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .kpi-card {
        animation: fadeUp 0.4s ease-out forwards;
        transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease !important;
    }
    .kpi-card:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7) !important;
        filter: brightness(1.05);
    }
    
    [data-testid="stSidebar"] p {
        margin: 0 !important;
    }

    /* Give both columns a strict fixed height relative to viewport */
    div[data-testid="stColumn"]:has(.dashboard-scroll-anchor),
    div[data-testid="stColumn"]:has(.chat-scroll-anchor) {
        height: calc(100vh - var(--header-height)) !important;
        position: relative !important; 
        overflow: hidden !important;
    }

    /* Fixed width for chat */
    div[data-testid="stColumn"]:has(.chat-scroll-anchor) {
        flex: 0 0 400px !important;
        width: 400px !important;
        border-left: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Dashboard: Absolute fill with explicit scrolling */
    div[data-testid="stColumn"]:has(.dashboard-scroll-anchor) > div[data-testid="stVerticalBlock"] {
        position: absolute !important;
        top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important;
        height: 100% !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding: 12px 40px 32px 40px !important;
        gap: 24px !important;
    }

    /* Chat: Absolute fill with internal flex (history scrolls, input sticky) */
    div[data-testid="stColumn"]:has(.chat-scroll-anchor) > div[data-testid="stVerticalBlock"] {
        position: absolute !important;
        top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        overflow: hidden !important;
    }

    /* ========================================== */
    /* 4. HEADER */
    /* ========================================== */
    header[data-testid="stHeader"] {
        background: rgba(11, 14, 20, 0.7) !important;
        backdrop-filter: blur(20px) !important;
        height: 60px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
    }

    /* ========================================== */
    /* 5. CARDS */
    /* ========================================== */
    div[data-testid="stMetric"], div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(17, 24, 39, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.12) !important;
        padding: 32px !important;
        border-radius: 18px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4) !important;
    }

    /* ========================================== */
    /* 6. BUTTONS & INPUTS */
    /* ========================================== */
    div.stButton > button:not([key^="suggested_"]) {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease-in-out !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
    }
    div.stButton > button:not([key^="suggested_"]):hover {
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-1px) !important;
    }

    div.stButton > button[key^="fu"] {
        border-radius: 20px !important;
        padding: 4px 12px !important;
        font-size: 0.75rem !important;
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #94A3B8 !important;
    }
    div.stButton > button[key^="fu"]:hover {
        color: #FFFFFF !important;
        background: rgba(255,255,255,0.1) !important;
        border-color: rgba(255,255,255,0.2) !important;
    }

    div.stButton > button[key="btn_high_risk"] {
        margin-top: -15px !important;
        border-top-left-radius: 0px !important;
        border-top-right-radius: 0px !important;
        border-bottom-left-radius: 16px !important;
        border-bottom-right-radius: 16px !important;
        background: #141C2B !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-top: none !important;
        color: #60A5FA !important;
        font-size: 0.8rem !important;
        padding: 8px !important;
    }
    div.stButton > button[key="btn_high_risk"]:hover {
        background: rgba(59, 130, 246, 0.15) !important;
        color: #FFFFFF !important;
    }

    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div, 
    div.stChatInputContainer {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-baseweb="input"] > div:focus-within, 
    div[data-baseweb="select"] > div:focus-within,
    div.stChatInputContainer:focus-within {
        border-color: rgba(59, 130, 246, 0.5) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15) !important;
    }

    /* ========================================== */
    /* 7. CHAT */
    /* ========================================== */
    div.stButton > button[key^="suggested_"] {
        width: auto !important;
        text-align: left !important;
        justify-content: flex-start !important;
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 999px !important;
        padding: 6px 16px !important;
        color: #E2E8F0 !important;
        font-size: 0.82rem !important;
        transition: all 0.2s ease-in-out !important;
        margin-bottom: 6px !important;
    }
    div.stButton > button[key^="suggested_"]:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        transform: translateY(-1px) !important;
    }
    div.stButton > button[key="suggested_tenure"] p { color: #F97316 !important; }
    div.stButton > button[key="suggested_salary"] p { color: #3B82F6 !important; }
    div.stButton > button[key="suggested_risk"] p { color: #A855F7 !important; }

    div[data-testid="stVerticalBlock"]:has(.chat-history-anchor) {
        flex: 1 !important;
        overflow-y: auto !important;
        padding-right: 8px !important;
    }
    .recent-chat-row {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: #E2E8F0;
        font-size: 0.85rem;
        margin-bottom: 8px;
        transition: all 0.2s ease;
    }
    .recent-chat-row:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #FFFFFF;
    }

    div[data-testid="stChatMessage"] { margin-bottom: 32px !important; }
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { margin-top: 8px !important; }

    div[data-testid="stChatMessage"]:has(.assistant-marker) {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.8) 100%);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        padding: 16px 20px;
        border: 1px solid rgba(59, 130, 246, 0.15);
        border-top: 1px solid rgba(59, 130, 246, 0.3);
        position: relative;
        margin-top: 12px;
    }
    
    div[data-testid="stChatMessage"]:has(.assistant-marker)::before {
        content: '🤖 AI AGENT';
        position: absolute;
        top: -10px;
        left: 20px;
        background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 100%);
        color: white;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 12px;
        letter-spacing: 0.05em;
        box-shadow: 0 2px 10px rgba(59, 130, 246, 0.3);
    }
    div[data-testid="stChatMessage"]:has(.user-marker) {
        background-color: #0078D4 !important;
        border-radius: 16px !important;
        padding: 8px 12px !important;
        margin-left: auto !important;
        max-width: 85% !important;
        display: flex !important;
        flex-direction: row-reverse !important;
    }
    div[data-testid="stChatMessage"]:has(.user-marker) > div:first-child {
        margin-left: 1rem;
        margin-right: 0;
    }

    div[data-testid="stChatInput"] {
        position: sticky !important;
        bottom: 0 !important;
        z-index: 100 !important;
        background: inherit !important;
        margin-top: auto !important;
        padding-bottom: 24px !important;
        padding-top: 12px !important;
    }
    div[data-testid="stChatInput"] textarea {
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
        border-radius: 28px !important;
        transition: all 0.3s ease-in-out !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        padding-left: 16px !important;
    }
    div[data-testid="stChatInput"] textarea:focus {
        border: 1px solid rgba(59, 130, 246, 0.6) !important;
        background-color: rgba(30, 41, 59, 0.95) !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.15) !important;
    }
    div[data-testid="stChatInput"] button {
        background-color: transparent !important;
        color: #3B82F6 !important;
        transition: transform 0.2s ease !important;
    }
    div[data-testid="stChatInput"] button:hover {
        transform: scale(1.1) !important;
    }

    .copilot-grid-layout {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-bottom: 16px;
    }
    .context-pill {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.25);
        color: #60A5FA;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* ========================================== */
    /* 8. SCROLLBARS */
    /* ========================================== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
        background-color: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background-color: rgba(255, 255, 255, 0.2);
    }

    /* ========================================== */
    /* 9. CHARTS & ICONS */
    /* ========================================== */
    .icon-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 8px;
        margin-right: 10px;
        flex-shrink: 0;
    }
    .icon-blue { background: rgba(59, 130, 246, 0.15); color: #3B82F6; }
    .icon-orange { background: rgba(249, 115, 22, 0.15); color: #F97316; }
    .icon-green { background: rgba(34, 197, 94, 0.15); color: #4ADE80; }
    .icon-purple { background: rgba(168, 85, 247, 0.15); color: #A855F7; }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar(col_nav):
    with col_nav:
        # 1. Main Branding
        st.markdown('''
            <div style="padding: 10px 0 24px 0;">
                <h2 style="margin: 0; padding: 0; font-size: 1.3rem; color: #FFFFFF; letter-spacing: -0.02em;">🎯 PeopleRisk AI</h2>
                <p style="margin: 0; padding: 0; color: #94A3B8; font-size: 0.75rem; font-weight: 500;">Enterprise HR Intelligence</p>
            </div>
        ''', unsafe_allow_html=True)

        current_nav = st.session_state.get("active_navigation", "📊 Risk Overview")

        def nav_button(label, icon, target_state):
            is_active = (current_nav == target_state)
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, icon=icon, key=f"nav_{label}", type=btn_type, use_container_width=True):
                st.session_state.active_navigation = target_state
                st.rerun()

        # 2. Analytics Section
        st.markdown("<p style='color: #64748B; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; margin-top: 16px;'>Analytics</p>", unsafe_allow_html=True)
        nav_button("Risk Overview", ":material/bar_chart:", "📊 Risk Overview")
        nav_button("Top Drivers", ":material/trending_up:", "🎯 Top Drivers")
        nav_button("High Risk Roster", ":material/group:", "📋 High Risk Roster")
        nav_button("Executive Summary", ":material/description:", "⚙️ Executive Summary")

        # 3. System Section
        st.markdown("<p style='color: #64748B; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; margin-top: 24px;'>System</p>", unsafe_allow_html=True)
        nav_button("Configuration", ":material/settings:", "⚙️ Configuration")
        
        # 4. Bottom Utility Section
        st.markdown('''
            <div style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 24px; margin-top: auto; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 32px; height: 32px; border-radius: 50%; background: #1E293B; display: flex; align-items: center; justify-content: center; color: #94A3B8;">
                        <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                    </div>
                    <div>
                        <p style="margin: 0; font-size: 0.8rem; color: #F8FAFC; font-weight: 600;">HR Administrator</p>
                        <p style="margin: 0; font-size: 0.65rem; color: #64748B;">Enterprise Edition</p>
                    </div>
                </div>
                <div style="color: #64748B; cursor: pointer;">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"></path></svg>
                </div>
            </div>
        ''', unsafe_allow_html=True)

def render_risk_overview(df):
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    total_emp = len(df)
    high_risk = len(df[df['RiskPercentage'] > 75])
    avg_risk = df['RiskPercentage'].mean()

    # Column 1 Example (Total Employees)
    kpi_col1.markdown(f'''
    <div class="kpi-card" style="
        background: linear-gradient(145deg, rgba(17, 24, 39, 0.7) 0%, rgba(11, 14, 20, 0.9) 100%);
        backdrop-filter: blur(20px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 24px;
        position: relative;
        overflow: hidden;
    ">
        <div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(59, 130, 246, 0.03) 0%, transparent 50%); pointer-events: none;"></div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 40px; height: 40px; border-radius: 12px; background: rgba(59, 130, 246, 0.1); display: flex; align-items: center; justify-content: center; color: #3B82F6; border: 1px solid rgba(59, 130, 246, 0.2);">
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                </div>
                <span style="color: #94A3B8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Total Workforce</span>
            </div>
            <span style="background: rgba(16, 185, 129, 0.15); color: #10B981; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 20px; border: 1px solid rgba(16, 185, 129, 0.2);">+1.2% this month</span>
        </div>
        <div style="font-size: 2.5rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.04em; margin-bottom: 4px;">{total_emp:,}</div>
        <div style="color: #64748B; font-size: 0.8rem; font-weight: 400;">Active employees across all regions</div>
    </div>
    ''', unsafe_allow_html=True)

    # Column 2 Example (High Flight Risk)
    kpi_col2.markdown(f'''
    <div class="kpi-card" style="
        background: linear-gradient(145deg, rgba(17, 24, 39, 0.7) 0%, rgba(11, 14, 20, 0.9) 100%);
        backdrop-filter: blur(20px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 24px;
        position: relative;
        overflow: hidden;
    ">
        <div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(239, 68, 68, 0.04) 0%, transparent 50%); pointer-events: none;"></div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 40px; height: 40px; border-radius: 12px; background: rgba(239, 68, 68, 0.1); display: flex; align-items: center; justify-content: center; color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2);">
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                </div>
                <span style="color: #94A3B8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">High Flight Risk</span>
            </div>
            <span style="background: rgba(239, 68, 68, 0.15); color: #F87171; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 20px; border: 1px solid rgba(239, 68, 68, 0.2);">+4% this quarter</span>
        </div>
        <div style="font-size: 2.5rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.04em; margin-bottom: 4px;">{high_risk:,}</div>
        <div style="color: #64748B; font-size: 0.8rem; font-weight: 400;">Employees with risk score &gt; 75%</div>
    </div>
    ''', unsafe_allow_html=True)


    # Column 3 Example (Average Risk Score)
    kpi_col3.markdown(f'''
    <div class="kpi-card" style="
        background: linear-gradient(145deg, rgba(17, 24, 39, 0.7) 0%, rgba(11, 14, 20, 0.9) 100%);
        backdrop-filter: blur(20px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 24px;
        position: relative;
        overflow: hidden;
    ">
        <div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(168, 85, 247, 0.03) 0%, transparent 50%); pointer-events: none;"></div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 40px; height: 40px; border-radius: 12px; background: rgba(168, 85, 247, 0.1); display: flex; align-items: center; justify-content: center; color: #A855F7; border: 1px solid rgba(168, 85, 247, 0.2);">
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                </div>
                <span style="color: #94A3B8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Avg Risk Score</span>
            </div>
            <span style="background: rgba(239, 68, 68, 0.15); color: #F87171; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 20px; border: 1px solid rgba(239, 68, 68, 0.2);">+1.2% delta</span>
        </div>
        <div style="font-size: 2.5rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.04em; margin-bottom: 4px;">{avg_risk:.1f}%</div>
        <div style="color: #64748B; font-size: 0.8rem; font-weight: 400;">Global organizational risk average</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-bottom: 32px;"></div>', unsafe_allow_html=True)

    # Risk Stratification Bins
    bins = [0, 25, 50, 75, 100]
    labels = ['Low', 'Medium', 'High', 'Critical']
    df['RiskStratification'] = pd.cut(df['RiskPercentage'], bins=bins, labels=labels, include_lowest=True)

    st.markdown("#### **Risk Insights**")
    
    # -----------------------------
    # Information Hierarchy: Tabs
    # -----------------------------
    tab1, tab2, tab3 = st.tabs(["📊 Demographics & Trends", "⭕ Risk Composition", "🗺️ Organizational Heatmaps"])
    
    # Common layout update for charts to make them look premium
    chart_layout = dict(
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Outfit', color='#64748B'),
        title_font=dict(size=18, color='#F8FAFC', family='Outfit'),
        xaxis=dict(showgrid=False, zeroline=False, showline=False, color='#475569', title_font=dict(size=12, color='#64748B')),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.02)', zeroline=False, showline=False, color='#475569', title_font=dict(size=12, color='#64748B')),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#94A3B8'))
    )

    with tab1:
        row1_col1, row1_col2 = st.columns([0.6, 0.4])
        with row1_col1:
            with st.container(border=True):
                # Area Chart: Risk Progression by Tenure Band
                tenure_agg = df.groupby('Tenure', as_index=False)['RiskPercentage'].mean()
                fig_area = px.area(tenure_agg, x='Tenure', y='RiskPercentage', 
                                   title='Risk Progression by Tenure', 
                                   color_discrete_sequence=['#3B82F6'],
                                   template='plotly_dark')
                # Spline smoothing & gradient styling
                fig_area.update_traces(line_shape='spline', fillcolor='rgba(59, 130, 246, 0.2)', line=dict(width=4))
                fig_area.update_layout(**chart_layout, height=420, margin=dict(l=30, r=30, t=70, b=30))
                st.plotly_chart(fig_area, use_container_width=True)

        with row1_col2:
            with st.container(border=True):
                # Line Chart: Average Risk vs Monthly Hours
                hours_agg = df.groupby('MonthlyHours', as_index=False)['RiskPercentage'].mean()
                fig_line = px.line(hours_agg, x='MonthlyHours', y='RiskPercentage', 
                                   title='Avg Risk Trend vs Monthly Hours',
                                   color_discrete_sequence=['#F43F5E'],
                                   template='plotly_dark')
                fig_line.update_traces(line_shape='spline', line=dict(width=4))
                fig_line.update_layout(**chart_layout, height=420, margin=dict(l=30, r=30, t=70, b=30))
                st.plotly_chart(fig_line, use_container_width=True)

    with tab2:
        row2_col1, row2_col2 = st.columns([0.4, 0.6])
        with row2_col1:
            with st.container(border=True):
                # Donut Chart
                strat_counts = df['RiskStratification'].value_counts().reset_index()
                strat_counts.columns = ['Risk Level', 'Count']
                fig_donut = px.pie(strat_counts, values='Count', names='Risk Level', 
                                   title='Workforce Risk Distribution', hole=0.75,
                                   color='Risk Level',
                                   color_discrete_map={'Low':'#10B981', 'Medium':'#F59E0B', 'High':'#F97316', 'Critical':'#EF4444'},
                                   template='plotly_dark')
                fig_donut.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit', color='#94A3B8'),
                    showlegend=False, height=420, margin=dict(l=30, r=30, t=70, b=30),
                    annotations=[dict(text='Risk', x=0.5, y=0.5, font_size=24, showarrow=False, font_color='#FFFFFF')]
                )
                fig_donut.update_traces(textposition='outside', textinfo='percent+label')
                event_donut = st.plotly_chart(fig_donut, use_container_width=True, on_select="rerun")
                if event_donut and len(event_donut.get("selection", {}).get("points", [])) > 0:
                    pt = event_donut["selection"]["points"][0]
                    label = pt.get("label") or pt.get("point_label") or pt.get("pointNumber")
                    if label is None and isinstance(pt.get("pointNumber"), int):
                        label = strat_counts.iloc[pt["pointNumber"]]['Risk Level']
                    if label:
                        st.session_state.pending_query = f"Summarize the employees in the {label} risk tier."
                        st.rerun()

        with row2_col2:
            with st.container(border=True):
                # Histogram Density
                fig_hist = px.histogram(df, x='RiskPercentage', nbins=40, 
                                        title='Risk Score Distribution Density',
                                        marginal='box',
                                        color_discrete_sequence=['#8B5CF6'],
                                        template='plotly_dark')
                fig_hist.update_traces(marker=dict(line=dict(width=0)))
                fig_hist.update_layout(**chart_layout, height=420, margin=dict(l=30, r=30, t=70, b=30), bargap=0.1)
                st.plotly_chart(fig_hist, use_container_width=True)

    with tab3:
        row3_col1, row3_col2 = st.columns(2)
        with row3_col1:
            with st.container(border=True):
                # Heatmap: Department vs Role Risk
                heat_agg = df.groupby(['Department', 'Role'], as_index=False)['RiskPercentage'].mean()
                heat_pivot = heat_agg.pivot(index='Department', columns='Role', values='RiskPercentage').fillna(0)
                colorscale = [[0, '#0B0E14'], [0.5, '#6B21A8'], [1, '#EF4444']]
                fig_heat = px.imshow(heat_pivot, text_auto=".1f", aspect="auto", 
                                     title="Department vs. Role Risk Grid",
                                     color_continuous_scale=colorscale,
                                     template='plotly_dark')
                fig_heat.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit', color='#94A3B8'),
                    height=420, margin=dict(l=30, r=30, t=70, b=30)
                )
                fig_heat.update_xaxes(showgrid=False)
                fig_heat.update_yaxes(showgrid=False)
                event_heat = st.plotly_chart(fig_heat, use_container_width=True, on_select="rerun")
                if event_heat and len(event_heat.get("selection", {}).get("points", [])) > 0:
                    pt = event_heat["selection"]["points"][0]
                    y_val = pt.get("y")  # Department
                    if y_val:
                        st.session_state.pending_query = f"Analyze flight risk in the {y_val} department."
                        st.rerun()

        with row3_col2:
            with st.container(border=True):
                # Parallel Categories
                driver_dept = df[['Driver1', 'Department']].dropna()
                fig_parallel = px.parallel_categories(driver_dept, dimensions=['Driver1', 'Department'],
                                                      title="Top Driver Cascade to Business Unit",
                                                      color_continuous_scale="Purples",
                                                      template='plotly_dark')
                fig_parallel.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit', color='#94A3B8'),
                    height=420, margin=dict(l=30, r=30, t=70, b=30)
                )
                st.plotly_chart(fig_parallel, use_container_width=True)

def render_top_drivers(df):
    st.markdown("#### **Top Attrition Drivers Distribution**")

    drivers = pd.concat([df['Driver1'], df['Driver2'], df['Driver3']]).dropna()
    driver_counts = drivers.value_counts().reset_index()
    driver_counts.columns = ['Driver', 'Count']

    with st.container(border=True):
        fig = px.bar(driver_counts.head(10), x='Count', y='Driver', orientation='h', 
                     color='Count', color_continuous_scale="Reds")
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=30, b=0), height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', template='plotly_dark')
        event_drivers = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
        if event_drivers and len(event_drivers.get("selection", {}).get("points", [])) > 0:
            pt = event_drivers["selection"]["points"][0]
            driver = pt.get("y")
            if driver:
                st.session_state.pending_query = f"Why is {driver} a top attrition driver?"
                st.rerun()

def render_high_risk_roster(df):
    st.markdown("#### **High Risk Roster (Action Required)**")
    with st.container(border=True):
        high_risk_df = df[df['RiskPercentage'] > 75].sort_values('RiskPercentage', ascending=False).head(20)
        st.dataframe(
            high_risk_df[['EmployeeID', 'Department', 'Role', 'RiskPercentage', 'Driver1', 'MonthlyHours']],
            column_config={
                "EmployeeID": st.column_config.TextColumn("ID", max_chars=10),
                "RiskPercentage": st.column_config.ProgressColumn(
                    "Flight Risk",
                    help="Predicted probability of attrition",
                    format="%f%%",
                    min_value=0,
                    max_value=100,
                ),
                "Department": st.column_config.TextColumn("Department"),
                "Role": st.column_config.TextColumn("Role"),
                "Driver1": st.column_config.TextColumn("Primary Driver"),
                "MonthlyHours": st.column_config.NumberColumn("Hours/Mo", format="%d")
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )

def render_executive_summary(df, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email):
    st.markdown("#### **Departmental Macro Metrics**")

    def get_top_driver(series):
        return series.mode()[0] if not series.mode().empty else "N/A"

    macro_metrics = df.groupby('Department').agg(
        Average_Risk=('RiskPercentage', 'mean'),
        High_Risk_Count=('RiskPercentage', lambda x: (x > 75).sum()),
        Top_Driver=('Driver1', get_top_driver)
    ).reset_index()

    macro_metrics['Average_Risk'] = macro_metrics['Average_Risk'].round(1)

    with st.container(border=True):
        st.dataframe(
            macro_metrics, 
            column_config={
                "Department": st.column_config.TextColumn("Business Unit"),
                "Average_Risk": st.column_config.NumberColumn("Avg Risk Score", format="%.1f%%"),
                "High_Risk_Count": st.column_config.NumberColumn("Critical Employees", format="%d"),
                "Top_Driver": st.column_config.TextColumn("Leading Attrition Factor")
            },
            hide_index=True,
            use_container_width=True
        )

    highest_risk_dept = macro_metrics.loc[macro_metrics['Average_Risk'].idxmax()]

    inference_text = (
        f"The **{highest_risk_dept['Department']}** segment displays disproportionate "
        f"flight risk ({highest_risk_dept['Average_Risk']}% avg) primarily driven by **{highest_risk_dept['Top_Driver']}**."
    )

    st.markdown(f'''
    <div style="
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, rgba(11, 14, 20, 0.4) 100%);
        border-left: 4px solid #EF4444;
        padding: 20px;
        border-radius: 8px;
        margin-top: 16px;
        margin-bottom: 24px;
        display: flex;
        gap: 16px;
        align-items: center;
    ">
        <div style="font-size: 24px;">🤖</div>
        <div>
            <div style="color: #EF4444; font-weight: 600; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">AI Inference Alert</div>
            <div style="color: #E2E8F0; font-size: 1rem; line-height: 1.5;">{inference_text}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("---")
    exec_col1, exec_col2 = st.columns(2)

    pdf_bytes = generate_executive_pdf(macro_metrics, inference_text)

    with exec_col1:
        st.download_button(
            label="📄 Export Executive PDF",
            data=pdf_bytes,
            file_name="executive_summary.pdf",
            mime="application/pdf",
            key="export_exec_pdf"
        )
    with exec_col2:
        if st.button("📧 Email Report to HR Leads", key="email_exec_pdf"):
            success = send_manager_email(
                target_email=target_email,
                subject="Executive Summary: HR Attrition Risk",
                body="Please review the attached macro-level executive summary.",
                attachment_bytes=pdf_bytes,
                filename="executive_summary.pdf",
                smtp_host=smtp_host, smtp_port=smtp_port, smtp_user=smtp_user, smtp_pass=smtp_pass
            )
            if success:
                st.toast("Executive Report Emailed Successfully!", icon="✅")
            else:
                st.error("Failed to send email.")

def render_configuration(slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email):
    st.markdown("## ⚙️ System Configuration & Automation Settings")
    st.markdown("<p style='color: #64748B;'>Configure your enterprise AI models and platform communication parameters.</p>", unsafe_allow_html=True)

    # Nest all system form inputs cleanly into structured columns
    setup_col1, setup_col2 = st.columns(2)

    with setup_col1:
        st.markdown("#### **AI Provider Settings**")
        provider_options = {
            "Google GenAI": ("google_genai", "gemini-2.5-flash-lite"),
            "Groq": ("groq", "llama-3.3-70b-versatile"),
            "Anthropic": ("anthropic", "claude-3-5-sonnet")
        }

        selected_label = st.selectbox("Select AI Provider", list(provider_options.keys()), index=1, key="form_provider")
        provider, model_name = provider_options[selected_label]

        default_key = os.environ.get("GROQ_API_KEY", "") if provider == "groq" else ""
        api_key = st.text_input("API Key", type="password", value=default_key, help="Overrides local environment variables.", key="form_key")

        if st.button("Connect Agent Engine", use_container_width=True):
            if not api_key and not os.environ.get(f"{provider.upper()}_API_KEY") and provider != "google_genai":
                st.error("Please provide an API Key.")
            else:
                try:
                    st.session_state.agent_graph = create_graph(provider, model_name, api_key)
                    st.session_state.messages = [] # Reset chat history on new connection
                    st.session_state.ai_provider = selected_label
                    st.success("Agent Connected Successfully!")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    with setup_col2:
        st.markdown("#### **Automation & Action APIs**")
        st.markdown("<small><i>(Leave blank for simulated execution)</i></small>", unsafe_allow_html=True)
        st.text_input("Slack Webhook URL", type="password", key="form_slack")
        st.text_input("SMTP Host", key="form_smtp_host")
        st.number_input("SMTP Port", value=587, key="form_smtp_port")
        st.text_input("SMTP User Address", key="form_smtp_user")
        st.text_input("SMTP App Password", type="password", key="form_smtp_pass")
        st.text_input("Target Manager Email", value="manager@thinkpalm.com", key="form_target_email")

def render_dashboard(col_dash, df, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email):
    with col_dash:
        with st.container(border=False):
                st.markdown('<div style="padding-right: 20px;">', unsafe_allow_html=True)
                st.markdown("## **Organizational Risk Dashboard**")
                st.markdown("<p style='color: #94A3B8; font-size: 0.9rem; margin-bottom: 24px;'>Real-time insights and predictive flight risk metrics.</p>", unsafe_allow_html=True)
                
                # Toolbar
                tb_col1, tb_col2, tb_col3, tb_col4 = st.columns([0.4, 0.2, 0.2, 0.2])
                with tb_col1:
                    st.text_input("Search employees...", placeholder="🔍 Search...", label_visibility="collapsed")
                with tb_col2:
                    st.button("Filters", icon=":material/filter_list:", use_container_width=True, key="tb_filter")
                with tb_col3:
                    st.button("Export", icon=":material/download:", use_container_width=True, key="tb_export")
                with tb_col4:
                    st.button("Refresh", icon=":material/refresh:", use_container_width=True, key="tb_refresh")
                
                st.markdown("<div style='margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05);'></div>", unsafe_allow_html=True)

                if "active_navigation" not in st.session_state:
                    st.session_state.active_navigation = "📊 Risk Overview"

        if st.session_state.active_navigation == "📊 Risk Overview":
            render_risk_overview(df)
        elif st.session_state.active_navigation == "🎯 Top Drivers":
            render_top_drivers(df)
        elif st.session_state.active_navigation == "📋 High Risk Roster":
            render_high_risk_roster(df)
        elif st.session_state.active_navigation == "⚙️ Executive Summary":
            render_executive_summary(df, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email)
        elif st.session_state.active_navigation == "⚙️ Configuration":
            render_configuration(slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email)

def render_chat_history(slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email):
    user_queries = []
    for tid, msgs in st.session_state.threads.items():
        for m in msgs:
            if m["role"] == "user":
                user_queries.append(m["content"])

    if not user_queries:
        st.markdown('<div class="recent-chat-row"><span>No recent queries yet.</span></div>', unsafe_allow_html=True)
    else:
        for query in reversed(user_queries[-3:]):
            st.markdown(f'<div class="recent-chat-row"><span>💬 {query}</span></div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-bottom: 16px;"></div>', unsafe_allow_html=True)

    # Display chat messages from history
    if not st.session_state.active_thread_id:
        current_messages = [
            {"role": "assistant", "content": "Hello! I am PeopleRisk AI. How can I help you manage employee retention today?", "intent": None}
        ]
    else:
        current_messages = st.session_state.threads.get(st.session_state.active_thread_id, [])

    chat_container = st.container(border=False)
    with chat_container:
        st.markdown("<div class='chat-history-anchor'></div>", unsafe_allow_html=True)
        for idx, msg in enumerate(current_messages):
            avatar = "🤖" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                if msg["role"] == "assistant":
                    st.markdown("<span class='assistant-marker'></span>", unsafe_allow_html=True)
                elif msg["role"] == "user":
                    st.markdown("<span class='user-marker'></span>", unsafe_allow_html=True)
                st.markdown(msg["content"])

                if msg["role"] == "assistant" and idx > 0:
                    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                    btn_col1, btn_col2, btn_col3 = st.columns(3)

                    with btn_col1:
                        docx_bytes = create_mitigation_docx(msg["content"])
                        st.download_button(
                            label="📄 DOCX",
                            data=docx_bytes,
                            file_name=f"chat_export_{idx}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"docx_{idx}"
                        )
                    with btn_col2:
                        if st.button("📋 PDF", key=f"pdf_{idx}", help="Email to Manager"):
                            pdf_bytes = create_mitigation_pdf(msg["content"])
                            success = send_manager_email(
                                target_email=target_email,
                                subject="HR Copilot Action Plan",
                                body="Please review the attached plan from the HR Copilot.",
                                attachment_bytes=pdf_bytes,
                                filename=f"copilot_export_{idx}.pdf",
                                smtp_host=smtp_host, smtp_port=smtp_port, smtp_user=smtp_user, smtp_pass=smtp_pass
                            )
                            if success:
                                st.toast("Email Dispatched Successfully!", icon="✅")
                            else:
                                st.error("Failed to send email.")
                    with btn_col3:
                        if st.button("🚨 Alert", key=f"alert_{idx}", help="Send Slack Alert"):
                            success = dispatch_critical_alert(
                                webhook_url=slack_url,
                                employee_id="EMP-ALERT",
                                risk_score=90.0,
                                mitigation_note=msg["content"][:200] + "..."
                            )
                            if success:
                                st.toast("Slack Alert Triggered!", icon="✅")
                            else:
                                st.error("Failed to send Slack alert.")

                    # Follow-up Chips
                    st.markdown("<div style='margin-top: 16px; margin-bottom: 8px; color: #94A3B8; font-size: 0.8rem; font-weight: 500;'>✨ Suggested Follow-up</div>", unsafe_allow_html=True)
                    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                    if f_col1.button("Show Employees", key=f"fu1_{idx}", use_container_width=True):
                        st.session_state.pending_query = "Show the employees for this analysis"
                        st.rerun()
                    if f_col2.button("Compare Depts", key=f"fu2_{idx}", use_container_width=True):
                        st.session_state.pending_query = "Compare risk across departments"
                        st.rerun()
                    if f_col3.button("Email Manager", key=f"fu3_{idx}", use_container_width=True):
                        st.session_state.pending_query = "Draft an email to the manager"
                        st.rerun()
                    if f_col4.button("Generate PDF", key=f"fu4_{idx}", use_container_width=True):
                        st.session_state.pending_query = "Generate a PDF report"
                        st.rerun()

    if st.button("➕ New Conversation Thread", key="btn_new_thread", use_container_width=True):
        st.session_state.active_thread_id = None
        st.session_state.pending_query = None
        st.rerun()

    st.markdown("<p style='color: #64748B; font-size: 0.85rem; font-weight: 500; margin-bottom: 8px;'>Suggested Questions</p>", unsafe_allow_html=True)
    return chat_container



    q1 = "⚠ Tenure drivers"
    q2 = "💵 Salary queries"
    q3 = "🚨 High Risk summaries"
    q4 = "📈 Engineering risk"

    grid_col1, grid_col2 = st.columns(2)
    with grid_col1:
        if st.button(q1, key="suggested_tenure", use_container_width=True):
            st.session_state.pending_query = "What are the primary tenure drivers for attrition?"
            st.rerun()
        if st.button(q3, key="suggested_risk", use_container_width=True):
            st.session_state.pending_query = "Summarize the high flight risk employees."
            st.rerun()
    with grid_col2:
        if st.button(q2, key="suggested_salary", use_container_width=True):
            st.session_state.pending_query = "Are salary levels impacting the flight risk?"
            st.rerun()
        if st.button(q4, key="suggested_eng", use_container_width=True):
            st.session_state.pending_query = "Why is Engineering high risk?"
            st.rerun()

def render_chat_input(chat_container):
    prompt = st.chat_input("Ask about employee risk data...")
    if "pending_query" in st.session_state and st.session_state.pending_query:
        prompt = st.session_state.pending_query
        st.session_state.pending_query = None

    if prompt:
        with chat_container:
            if not st.session_state.active_thread_id:
                st.session_state.active_thread_id = str(uuid.uuid4())
                st.session_state.threads[st.session_state.active_thread_id] = [
                    {"role": "assistant", "content": "Hello! I am PeopleRisk AI. How can I help you manage employee retention today?", "intent": None}
                ]

            st.chat_message("user", avatar="👤").markdown(f"<span class='user-marker'></span>{prompt}", unsafe_allow_html=True)
            st.session_state.threads[st.session_state.active_thread_id].append({"role": "user", "content": prompt})

            with st.chat_message("assistant", avatar="🤖"):
                message_placeholder = st.empty()
                with st.spinner("🤖 Thinking... Analyzing HR Graph Metrics..."):
                    config = {"configurable": {"thread_id": st.session_state.active_thread_id}}
                    input_state = {"messages": [("user", prompt)]}

                    try:
                        final_state = None
                        for event in st.session_state.agent_graph.stream(input_state, config=config):
                            for node_name, node_state in event.items():
                                final_state = node_state

                        if final_state and "messages" in final_state:
                            ai_message = final_state["messages"][-1].content
                            intent = final_state.get("current_intent")

                            message_placeholder.markdown(ai_message)

                            st.session_state.threads[st.session_state.active_thread_id].append({
                                "role": "assistant", 
                                "content": ai_message,
                                "intent": intent
                            })

                            st.rerun()
                        else:
                            st.error("The agent did not return a valid response.")
                    except Exception as e:
                        st.error(f"Error during execution: {e}")

def render_chat_panel(col_chat, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email):
    with col_chat:
        with st.container(border=False):
            if "agent_graph" not in st.session_state:
                st.markdown('''
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
                    <h3 style="margin: 0; color: #FFFFFF; font-size: 1.25rem; font-weight: 600;">🤖 HR Copilot</h3>
                    <span style="background: rgba(239, 68, 68, 0.12); color: #F87171; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 12px; display: inline-flex; align-items: center; gap: 6px;">
                        <span style="width: 6px; height: 6px; background-color: #F87171; border-radius: 50%; display: inline-block;"></span> Disconnected
                    </span>
                </div>
                ''', unsafe_allow_html=True)
                st.markdown('''
                <div style="
                    background: rgba(255, 255, 255, 0.02);
                    backdrop-filter: blur(16px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 16px;
                    padding: 24px;
                    text-align: center;
                    margin-top: 20px;
                ">
                    <h4 style="color: #FFFFFF; margin-bottom: 8px;">Agent Offline</h4>
                    <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">Please connect an AI provider via the <b>System Configuration & Settings</b> popover in the top right to enable the conversational copilot.</p>
                </div>
                ''', unsafe_allow_html=True)
            else:
                active_provider = st.session_state.get("ai_provider", "Google Gemini")
                st.markdown(f'''
                <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 14px 18px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #FFFFFF; font-weight: 600; font-size: 0.95rem; letter-spacing: -0.01em;">✨ {active_provider}</span>
                        <span style="background: rgba(34, 197, 94, 0.15); color: #4ADE80; font-size: 0.65rem; font-weight: 700; padding: 2px 6px; border-radius: 12px; display: inline-flex; align-items: center; gap: 4px; text-transform: uppercase; letter-spacing: 0.05em;">
                            <span style="width: 4px; height: 4px; background-color: #4ADE80; border-radius: 50%;"></span> Active
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px; font-size: 0.75rem; color: #64748B;">
                        <span>System Gateway: Verified</span>
                        <span style="font-family: monospace; color: #94A3B8;">Latency: 0.8s</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

                st.markdown('''
                <div style="margin-bottom: 16px;">
                    <div class="context-pill">
                        <span>📍 Global Dashboard</span>
                        <span style="opacity: 0.5;">|</span>
                        <span>June 2026</span>
                        <span style="margin-left: 4px; cursor: pointer;">✕</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

                st.markdown('''
                <h3 style="color: #FFFFFF; font-size: 1rem; font-weight: 600; margin-bottom: 12px;">🕒 Recent Sessions</h3>
                ''', unsafe_allow_html=True)
        chat_container = render_chat_history(slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email)
        render_chat_input(chat_container)

def load_risk_data():
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / 'hr_data.db'
    if not db_path.exists():
        return pd.DataFrame()
    
    with sqlite3.connect(db_path) as conn:
        query = """
            SELECT e.*, a.RiskPercentage, a.Driver1, a.Driver2, a.Driver3 
            FROM employees e 
            LEFT JOIN attrition_scores a ON e.EmployeeID = a.EmployeeID
        """
        df = pd.read_sql_query(query, conn)
    return df

def main():
    render_header()
    
    # Extract config variables to pass down
    slack_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    target_email = "manager@thinkpalm.com"
    


    df = load_risk_data()
    
    if df.empty or 'RiskPercentage' not in df.columns:
        st.warning("No data found. Ensure the ML pipeline (Phase 2) has run.")
        st.stop()
        
    # Main layout matching implementation_plan.md
    col_dash, col_chat = st.columns([1, 0.4], gap="small")
    
    # Inject CSS anchors directly into the columns for bulletproof targeting
    with col_dash:
        st.markdown('<span class="dashboard-scroll-anchor" style="display:none;"></span>', unsafe_allow_html=True)
    with col_chat:
        st.markdown('<span class="chat-scroll-anchor" style="display:none;"></span>', unsafe_allow_html=True)
    
    render_sidebar(st.sidebar)
    render_dashboard(col_dash, df, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email)
    render_chat_panel(col_chat, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email)

if __name__ == "__main__":
    main()

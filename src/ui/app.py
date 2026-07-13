import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path
import os
import sys
import json
from io import StringIO
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
if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = True

if "agent_graph" not in st.session_state:
    try:
        from src.agents.graph import create_graph
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            st.session_state.agent_graph = create_graph("groq", "llama-3.3-70b-versatile", groq_key)
            st.session_state.ai_provider = "Groq"
    except Exception:
        pass

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}

@st.cache_data(show_spinner=False)
def _cached_docx(content: str) -> bytes:
    return create_mitigation_docx(content)

@st.cache_data(show_spinner=False)
def _cached_exec_pdf(metrics_json: str, inference_text: str) -> bytes:
    metrics = pd.read_json(StringIO(metrics_json))
    return generate_executive_pdf(metrics, inference_text)

def _build_macro_metrics(df: pd.DataFrame):
    def get_top_driver(series):
        return series.mode()[0] if not series.mode().empty else "N/A"
    metrics = df.groupby("Department").agg(
        Average_Risk=("RiskPercentage", "mean"),
        High_Risk_Count=("RiskPercentage", lambda x: (x > 75).sum()),
        Top_Driver=("Driver1", get_top_driver),
    ).reset_index()
    metrics["Average_Risk"] = metrics["Average_Risk"].round(1)
    highest = metrics.loc[metrics["Average_Risk"].idxmax()]
    inference = (
        f"The **{highest['Department']}** segment displays disproportionate "
        f"risk exposure (Avg: {highest['Average_Risk']}%), driven primarily by "
        f"{highest['Top_Driver']}. We recommend immediate qualitative assessments "
        f"for the {highest['High_Risk_Count']} high-risk individuals."
    )
    return metrics, inference

@st.cache_data(show_spinner=False)
def _chart_aggregates(df: pd.DataFrame):
    """Precompute chart aggregates once per dataset fingerprint."""
    bins = [0, 25, 50, 75, 100]
    labels = ["Low", "Medium", "High", "Critical"]
    risk_strat = pd.cut(df["RiskPercentage"], bins=bins, labels=labels, include_lowest=True)
    tenure_agg = df.groupby("Tenure", as_index=False)["RiskPercentage"].mean()
    hours_agg = df.groupby("MonthlyHours", as_index=False)["RiskPercentage"].mean()
    strat_counts = risk_strat.value_counts().reset_index()
    strat_counts.columns = ["Risk Level", "Count"]
    heat_agg = df.groupby(["Department", "Role"], as_index=False)["RiskPercentage"].mean()
    heat_pivot = heat_agg.pivot(index="Department", columns="Role", values="RiskPercentage").fillna(0)
    driver_dept = df[["Driver1", "Department"]].dropna()
    # Cap parallel-categories rows for speed on large rosters
    if len(driver_dept) > 400:
        driver_dept = driver_dept.sample(400, random_state=42)
    return tenure_agg, hours_agg, strat_counts, heat_pivot, driver_dept, risk_strat

def render_header():
    st.markdown("""
    <style>
    /* ========================================== */
    /* 1. TYPOGRAPHY */
    /* ========================================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stSidebar"], .stMarkdown, button, input, textarea, select, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }

    .stApp h2,
    [data-testid="stMarkdownContainer"] h2,
    .stMarkdown h2 {
        font-size: 1.575rem !important; /* ~10% smaller than default 1.75rem */
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
        --header-height: 0px;
        --sidebar-anim-dur: 0.32s;
        --sidebar-anim-ease: cubic-bezier(0.22, 1, 0.36, 1);
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

    /* Hide empty Streamlit top bar so it doesn't blur/clip the AI Assistant heading */
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        background: transparent !important;
        backdrop-filter: none !important;
        border: none !important;
        box-shadow: none !important;
    }

    .block-container {
        padding-left: 24px !important;
        padding-right: 24px !important;
        padding-top: 24px !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }
    /* Remove right-side gutter so AI Assistant aligns to page edge */
    .block-container:has(.chat-scroll-anchor) {
        padding-right: 0 !important;
    }

    /* ========================================== */
    /* 3. SIDEBAR REDESIGN (PERMANENTLY OPEN) */
    /* ========================================== */
    [data-testid="stSidebar"] {
        min-width: 250px !important;
        max-width: 250px !important;
        width: 250px !important;
        background-color: #111827 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.03) !important;
        transform: translateX(0px) !important;
        margin-left: 0px !important;
        position: relative !important;
        visibility: visible !important;
        display: block !important;
        transition: width var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    min-width var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    max-width var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    border-color var(--sidebar-anim-dur) var(--sidebar-anim-ease) !important;
        overflow-x: hidden !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
    [data-testid="stSidebar"] .block-container,
    [data-testid="stSidebar"] [data-testid="stSidebarHeader"],
    [data-testid="stSidebar"] [data-testid="stLogoSpacer"],
    [data-testid="stSidebar"] .st-key-sidebar_toggle {
        transition: padding var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    margin var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    justify-content var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    align-items var(--sidebar-anim-dur) var(--sidebar-anim-ease) !important;
    }
    
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Logo + caption in native stLogoSpacer */
    [data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
        align-items: flex-start !important;
        padding: 4px 12px 6px 12px !important;
    }
    [data-testid="stSidebar"] [data-testid="stLogoSpacer"] {
        display: flex !important;
        flex: 1 1 auto !important;
        width: 100% !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
    }
    [data-testid="stSidebar"] [data-testid="stLogoSpacer"] .pr-sidebar-brand__title {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 1.17rem !important;
        color: #FFFFFF !important;
        letter-spacing: -0.02em !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
    }
    [data-testid="stSidebar"] [data-testid="stLogoSpacer"] .pr-sidebar-brand__caption {
        margin: 2px 0 0 0 !important;
        padding: 0 !important;
        color: #94A3B8 !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] [data-testid="stLogoSpacer"] .pr-sidebar-brand--collapsed {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] [data-testid="stLogoSpacer"] .pr-sidebar-brand__icon {
        font-size: 1.6rem !important;
        line-height: 1 !important;
    }

    /* Sidebar toggle button sizing (position set per open/closed state) */
    [data-testid="stSidebar"] .st-key-sidebar_toggle {
        margin: 0 0 12px 0 !important;
        padding: 0 !important;
        width: 100% !important;
        z-index: 50 !important;
        pointer-events: auto !important;
        display: flex !important;
        justify-content: center !important;
    }
    [data-testid="stSidebar"] .st-key-sidebar_toggle button {
        min-width: 35px !important;
        min-height: 35px !important;
        width: 35px !important;
        max-width: 35px !important;
        height: 35px !important;
        padding: 8px !important;
        box-sizing: border-box !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 6px !important;
        pointer-events: auto !important;
    }
    [data-testid="stSidebar"] .st-key-sidebar_toggle button [data-testid="stMarkdownContainer"] {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
    }
    [data-testid="stSidebar"] .st-key-sidebar_toggle button [data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 1.1rem !important;
        line-height: 1 !important;
    }

    .st-emotion-cache-tn0cau {
        display: flex;
        gap: 1rem;
        width: 100%;
        max-width: 100%;
        height: auto;
        min-width: 1.6rem;
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
        transition: background 0.18s ease,
                    color 0.18s ease,
                    padding var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    margin var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    justify-content var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    min-width var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    max-width var(--sidebar-anim-dur) var(--sidebar-anim-ease),
                    width var(--sidebar-anim-dur) var(--sidebar-anim-ease) !important;
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

    /* Keep all expanded nav items start-aligned with icons on one vertical line */
    .stApp [data-testid="stSidebar"] .st-key-nav_risk_overview button,
    .stApp [data-testid="stSidebar"] .st-key-nav_top_drivers button,
    .stApp [data-testid="stSidebar"] .st-key-nav_high_risk_roster button,
    .stApp [data-testid="stSidebar"] .st-key-nav_executive_summary button,
    .stApp [data-testid="stSidebar"] .st-key-nav_configuration button {
        width: 100% !important;
        min-width: 100% !important;
        justify-content: flex-start !important;
        align-items: center !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
        gap: 10px !important;
    }
    .stApp [data-testid="stSidebar"] .st-key-nav_risk_overview button [data-testid="stIconMaterial"],
    .stApp [data-testid="stSidebar"] .st-key-nav_top_drivers button [data-testid="stIconMaterial"],
    .stApp [data-testid="stSidebar"] .st-key-nav_high_risk_roster button [data-testid="stIconMaterial"],
    .stApp [data-testid="stSidebar"] .st-key-nav_executive_summary button [data-testid="stIconMaterial"],
    .stApp [data-testid="stSidebar"] .st-key-nav_configuration button [data-testid="stIconMaterial"] {
        width: 18px !important;
        min-width: 18px !important;
        display: inline-flex !important;
        justify-content: center !important;
    }

    /* Streamlit button inner flex wrapper — keep icon + label start-aligned */
    [data-testid="stSidebar"] .st-emotion-cache-1lads1q,
    .stApp [data-testid="stSidebar"] .st-key-nav_risk_overview button > div,
    .stApp [data-testid="stSidebar"] .st-key-nav_top_drivers button > div,
    .stApp [data-testid="stSidebar"] .st-key-nav_high_risk_roster button > div,
    .stApp [data-testid="stSidebar"] .st-key-nav_executive_summary button > div,
    .stApp [data-testid="stSidebar"] .st-key-nav_configuration button > div {
        display: flex !important;
        align-items: start !important;
        justify-content: start !important;
        width: 100% !important;
    }
    
    @keyframes fadeUp {
        0% { opacity: 0; transform: translateY(6px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .kpi-card {
        animation: fadeUp 0.25s ease-out forwards;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    .kpi-card:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5) !important;
    }
    
    [data-testid="stSidebar"] p {
        margin: 0 !important;
    }

    /* Keep dashboard + assistant visible together on wide screens */
    div[data-testid="stHorizontalBlock"]:has(.chat-scroll-anchor) {
        flex-wrap: nowrap !important;
        align-items: stretch !important;
    }

    /* Give both columns a strict fixed height relative to viewport */
    div[data-testid="stColumn"]:has(.dashboard-scroll-anchor),
    div[data-testid="stColumn"]:has(.chat-scroll-anchor) {
        height: calc(100vh - var(--header-height)) !important;
        position: relative !important;
        overflow: hidden !important;
    }

    /* Let dashboard shrink so fixed chat column doesn't get pushed off-screen */
    div[data-testid="stColumn"]:has(.dashboard-scroll-anchor) {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }

    /* Chat column width adapts by screen size */
    div[data-testid="stColumn"]:has(.chat-scroll-anchor) {
        flex: 0 0 380px !important;
        width: 380px !important;
        min-width: 320px !important;
        margin-right: 0 !important;
        background-color: #0F1117 !important;
        border-radius: 24px !important;
        box-shadow: -4px 0 24px rgba(0,0,0,0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    div[data-testid="stColumn"]:has(.chat-scroll-anchor) > div[data-testid="stVerticalBlock"] {
        padding: 16px 24px 28px 24px !important;
    }

    @media (max-width: 1400px) {
        div[data-testid="stColumn"]:has(.chat-scroll-anchor) {
            flex: 0 0 340px !important;
            width: 340px !important;
            min-width: 300px !important;
        }
    }

    @media (max-width: 1200px) {
        div[data-testid="stColumn"]:has(.chat-scroll-anchor) {
            flex: 0 0 300px !important;
            width: 300px !important;
            min-width: 280px !important;
        }
    }

    /* Tablets/phones: stack assistant below dashboard so it's always visible */
    @media (max-width: 992px) {
        div[data-testid="stHorizontalBlock"]:has(.chat-scroll-anchor) {
            flex-wrap: wrap !important;
        }
        div[data-testid="stColumn"]:has(.dashboard-scroll-anchor),
        div[data-testid="stColumn"]:has(.chat-scroll-anchor) {
            flex: 1 1 100% !important;
            width: 100% !important;
            min-width: 100% !important;
            height: auto !important;
            overflow: visible !important;
        }
        div[data-testid="stColumn"]:has(.dashboard-scroll-anchor) > div[data-testid="stVerticalBlock"],
        div[data-testid="stColumn"]:has(.chat-scroll-anchor) > div[data-testid="stVerticalBlock"] {
            position: relative !important;
            top: auto !important;
            right: auto !important;
            bottom: auto !important;
            left: auto !important;
            height: auto !important;
            overflow: visible !important;
        }
        div[data-testid="stColumn"]:has(.dashboard-scroll-anchor) > div[data-testid="stVerticalBlock"] {
            padding: 12px 12px 20px 12px !important;
        }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            height: auto !important;
            overflow-y: auto !important;
        }
    }

    /* Native avatars re-enabled for chat messages */
    
    /* Chat Bubble CSS moved and consolidated below */
    
    /* Unified Assistant Bubble Action Buttons (DOCX/PDF/Alert and Follow-up Chips) */
    div[data-testid="stChatMessage"]:has(.assistant-marker) button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
        padding: 6px 8px !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
        white-space: nowrap !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        min-height: 34px !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        transform: none !important;
    }
    
    div[data-testid="stChatMessage"]:has(.assistant-marker) button:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
        transform: none !important;
    }

    /* Prevent nested columns from overlapping inside narrow chat bubbles */
    div[data-testid="stChatMessage"] div[data-testid="stHorizontalBlock"] {
        gap: 8px !important;
        width: 100% !important;
        max-width: 100% !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        margin: 0 !important;
    }
    div[data-testid="stChatMessage"] div[data-testid="stColumn"] {
        min-width: 0 !important;
        flex: 1 1 0 !important;
        width: auto !important;
        overflow: hidden !important;
    }
    div[data-testid="stChatMessage"] div[data-testid="stColumn"] > div {
        width: 100% !important;
        min-width: 0 !important;
    }
    div[data-testid="stChatMessage"] .stButton,
    div[data-testid="stChatMessage"] .stDownloadButton {
        width: 100% !important;
        min-width: 0 !important;
    }
    div[data-testid="stChatMessage"] .stButton > button,
    div[data-testid="stChatMessage"] .stDownloadButton > button {
        width: 100% !important;
    }
    
    /* Chat Input */
    div[data-testid="stChatInput"] {
        background: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        padding-right: 4px !important;
    }
    div[data-testid="stChatInput"] textarea {
        color: #F8FAFC !important;
        background: transparent !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #64748B !important;
    }
    div[data-testid="stChatInput"] button {
        background: #7C3AED !important;
        color: #FFFFFF !important;
        border-radius: 50% !important;
        padding: 8px !important;
        width: 36px !important;
        height: 36px !important;
        margin-top: 4px !important;
    }
    div[data-testid="stChatInput"] button svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* Dashboard: Absolute fill with explicit scrolling */
    div[data-testid="stColumn"]:has(.dashboard-scroll-anchor) > div[data-testid="stVerticalBlock"] {
        position: absolute !important;
        top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important;
        height: 100% !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding: 12px 10px 32px 10px !important;
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
        padding: 16px 24px 28px 24px !important;
        box-sizing: border-box !important;
    }

    /* ========================================== */
    /* 4. HEADER (hidden — empty Streamlit bar was clipping AI Assistant) */
    /* ========================================== */
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        background: transparent !important;
        backdrop-filter: none !important;
        border: none !important;
        box-shadow: none !important;
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
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
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
        backdrop-filter: blur(6px) !important;
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
        backdrop-filter: blur(6px) !important;
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

    /* Make the marker invisible */
    div[data-testid="stColumn"]:has(.chat-scroll-anchor) > div[data-testid="stVerticalBlock"] > div:has(.history-marker) {
        display: none !important;
    }
    
    /* Target the exact wrapper that follows the marker (the chat history container) */
    div[data-testid="stColumn"]:has(.chat-scroll-anchor) > div[data-testid="stVerticalBlock"] > div:has(.history-marker) + div {
        flex: 1 1 0% !important;
        min-height: 0 !important;
        overflow-y: auto !important;
        display: flex !important;
        flex-direction: column !important;
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

    /* Modern ChatGPT / Claude Single-Column Stack */
    div[data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 24px !important;
        box-shadow: none !important;
        
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        align-items: flex-start !important;
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        overflow: hidden !important;
        box-sizing: border-box !important;
    }
    
    /* Align User Bubbles to the Right */
    div[data-testid="stChatMessage"]:has(.user-marker) {
        align-items: flex-end !important;
    }
    
    /* Headers (Avatar + Name) - Avatar is ALWAYS the first child */
    div[data-testid="stChatMessage"] > div:first-child {
        background: transparent !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: auto !important;
        height: auto !important;
        padding: 0 4px !important;
        color: #94A3B8 !important;
        font-size: 1rem !important;
        flex-direction: row !important;
    }

    /* Add Header Text Next to Avatars */
    div[data-testid="stChatMessage"]:has(.assistant-marker) > div:first-child::after {
        content: "AI Assistant";
        margin-left: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        color: #E2E8F0;
        letter-spacing: 0.02em;
    }

    div[data-testid="stChatMessage"]:has(.user-marker) > div:first-child::after {
        content: "You";
        margin-left: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        color: #94A3B8;
        letter-spacing: 0.02em;
    }

    /* Message Content Cards - Content is ALWAYS the second child */
    div[data-testid="stChatMessage"] > div:nth-child(2) {
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        padding: 12px !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        box-sizing: border-box !important;
        min-width: 0 !important;
    }
    
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        margin-top: 0 !important;
    }

    /* AI Message Card styling — full width so action rows fit */
    div[data-testid="stChatMessage"]:has(.assistant-marker) > div:nth-child(2) {
        background: #151B26 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        color: #E2E8F0 !important;
        max-width: 100% !important;
        width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
        border-radius: 4px 12px 12px 12px !important;
    }

    /* User Message Card styling */
    div[data-testid="stChatMessage"]:has(.user-marker) > div:nth-child(2) {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        color: #FFFFFF !important;
        border-radius: 12px 4px 12px 12px !important;
        max-width: 75% !important;
        padding: 12px 16px !important;
    }

    div[data-testid="stChatInput"] {
        position: sticky !important;
        bottom: 0 !important;
        z-index: 100 !important;
        background: transparent !important;
        margin-top: auto !important;
        padding-bottom: 8px !important;
        padding-top: 12px !important;
        border: none !important;
        flex-shrink: 0 !important;
    }

    /* Keep disclaimer fully visible below chat input */
    .chat-disclaimer-footer {
        flex-shrink: 0 !important;
        margin-top: 8px !important;
        margin-bottom: 8px !important;
        overflow: visible !important;
        line-height: 1.45 !important;
    }
    .chat-disclaimer-footer span {
        display: block !important;
        white-space: normal !important;
        overflow: visible !important;
        color: #94A3B8 !important;
        font-size: 0.75rem !important;
        line-height: 1.45 !important;
    }
    
    /* Target Streamlit's actual input box wrapper instead of just the textarea */
    div[data-testid="stChatInput"] > div {
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
        border-radius: 28px !important;
        transition: all 0.3s ease-in-out !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        padding: 2px 8px !important;
    }
    
    div[data-testid="stChatInput"] > div:focus-within {
        border: 1px solid rgba(59, 130, 246, 0.6) !important;
        background-color: rgba(30, 41, 59, 0.95) !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.15) !important;
    }

    /* Make the inner textarea completely invisible so it doesn't double-box */
    div[data-testid="stChatInput"] textarea {
        border: none !important;
        background-color: transparent !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
        padding-left: 8px !important;
    }
    
    div[data-testid="stChatInput"] textarea:focus {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
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

def inject_sidebar_brand(collapsed: bool) -> None:
    """Place logo + caption inside Streamlit's stLogoSpacer at the top."""
    if collapsed:
        brand_html = (
            '<div class="pr-sidebar-brand pr-sidebar-brand--collapsed">'
            '<span class="pr-sidebar-brand__icon">🎯</span></div>'
        )
    else:
        brand_html = (
            '<div class="pr-sidebar-brand">'
            '<h2 class="pr-sidebar-brand__title">🎯 PeopleRisk AI</h2>'
            '<p class="pr-sidebar-brand__caption">Enterprise HR Intelligence</p>'
            '</div>'
        )

    components.html(
        f"""
        <script>
        (function () {{
            const brandHtml = {json.dumps(brand_html)};
            const mode = {json.dumps("collapsed" if collapsed else "expanded")};

            function getDoc() {{
                try {{ return window.parent.document; }} catch (e) {{ return document; }}
            }}

            function applyBrand() {{
                const doc = getDoc();
                const spacer = doc.querySelector('[data-testid="stSidebar"] [data-testid="stLogoSpacer"]');
                if (!spacer) return false;
                if (spacer.dataset.prBrandMode === mode && spacer.innerHTML === brandHtml) return true;
                spacer.innerHTML = brandHtml;
                spacer.dataset.prBrandMode = mode;
                return true;
            }}

            // Apply immediately, then sync on next paint frames.
            applyBrand();
            let attempts = 0;
            function syncBrand() {{
                attempts += 1;
                if (!applyBrand() && attempts <= 20) {{
                    requestAnimationFrame(syncBrand);
                }}
            }}
            requestAnimationFrame(syncBrand);

            const doc = getDoc();
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {{
                if (window.__prBrandObserver) {{
                    try {{ window.__prBrandObserver.disconnect(); }} catch (e) {{}}
                }}
                window.__prBrandObserver = new MutationObserver(function () {{
                    applyBrand();
                }});
                window.__prBrandObserver.observe(sidebar, {{ childList: true, subtree: false }});
            }}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )

def render_sidebar(col_nav):
    collapsed = st.session_state.get("sidebar_collapsed", True)

    with col_nav:
        if st.button(
            ":material/side_navigation:",
            key="sidebar_toggle",
            use_container_width=False,
            help="Open sidebar" if collapsed else "Close sidebar",
        ):
            collapsed = not collapsed
            st.session_state.sidebar_collapsed = collapsed

    inject_sidebar_brand(collapsed)

    if collapsed:
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            min-width: 74px !important;
            max-width: 74px !important;
            width: 74px !important;
        }
        [data-testid="stSidebar"] .block-container,
        [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding-left: 2px !important;
            padding-right: 8px !important;
            padding-top: 4px !important;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
            padding: 4px 8px 4px 8px !important;
            justify-content: center !important;
        }
        [data-testid="stSidebar"] [data-testid="stLogoSpacer"] {
            align-items: center !important;
            justify-content: center !important;
        }
        [data-testid="stSidebar"] .st-key-sidebar_toggle {
            position: static !important;
            justify-content: center !important;
            margin-bottom: 10px !important;
        }
        .stApp [data-testid="stSidebar"] .st-key-nav_risk_overview button [data-testid="stMarkdownContainer"],
        .stApp [data-testid="stSidebar"] .st-key-nav_top_drivers button [data-testid="stMarkdownContainer"],
        .stApp [data-testid="stSidebar"] .st-key-nav_high_risk_roster button [data-testid="stMarkdownContainer"],
        .stApp [data-testid="stSidebar"] .st-key-nav_executive_summary button [data-testid="stMarkdownContainer"],
        .stApp [data-testid="stSidebar"] .st-key-nav_configuration button [data-testid="stMarkdownContainer"] {
            display: none !important;
        }
        .stApp [data-testid="stSidebar"] .st-key-nav_risk_overview button,
        .stApp [data-testid="stSidebar"] .st-key-nav_top_drivers button,
        .stApp [data-testid="stSidebar"] .st-key-nav_high_risk_roster button,
        .stApp [data-testid="stSidebar"] .st-key-nav_executive_summary button,
        .stApp [data-testid="stSidebar"] .st-key-nav_configuration button {
            justify-content: center !important;
            padding: 8px 0 !important;
            min-width: 35px !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Opened sidebar only: pin close button to the right of the logo (logo stays put)
        st.markdown("""
        <style>
        [data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
            position: relative !important;
        }
        [data-testid="stSidebar"] div:has(> .st-key-sidebar_toggle) {
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
        }
        [data-testid="stSidebar"] .st-key-sidebar_toggle {
            position: absolute !important;
            top: 8px !important;
            right: 10px !important;
            left: auto !important;
            width: 35px !important;
            max-width: 35px !important;
            height: 35px !important;
            margin: 0 !important;
            padding: 0 !important;
            z-index: 1000 !important;
            justify-content: center !important;
            pointer-events: auto !important;
        }
        [data-testid="stSidebar"] .st-key-sidebar_toggle button {
            margin: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    with col_nav:
        current_nav = st.session_state.get("active_navigation", "📊 Risk Overview")

        def nav_button(label, icon, target_state):
            is_active = (current_nav == target_state)
            btn_type = "primary" if is_active else "secondary"
            slug = "nav_" + label.lower().replace(" ", "_")
            if st.button(
                label,
                icon=icon,
                key=slug,
                type=btn_type,
                use_container_width=True,
                help=None,
            ):
                st.session_state.active_navigation = target_state

        # 2. Analytics Section
        if not collapsed:
            st.markdown("<p style='color: #64748B; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; margin-top: 8px;'>Analytics</p>", unsafe_allow_html=True)
        nav_button("Risk Overview", ":material/bar_chart:", "📊 Risk Overview")
        nav_button("Top Drivers", ":material/trending_up:", "🎯 Top Drivers")
        nav_button("High Risk Roster", ":material/group:", "📋 High Risk Roster")
        nav_button("Executive Summary", ":material/description:", "⚙️ Executive Summary")

        # 3. System Section
        if not collapsed:
            st.markdown("<p style='color: #64748B; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; margin-top: 24px;'>System</p>", unsafe_allow_html=True)
        nav_button("Configuration", ":material/settings:", "⚙️ Configuration")
        
        # 4. Bottom Utility Section
        if collapsed:
            st.markdown('''
                <div style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; margin-top: 16px; display: flex; justify-content: center;">
                    <div style="width: 35px; height: 35px; min-width: 35px; padding: 8px; box-sizing: border-box; border-radius: 50%; background: #1E293B; display: flex; align-items: center; justify-content: center; color: #94A3B8;">
                        <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
        else:
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
        backdrop-filter: blur(8px);
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
        backdrop-filter: blur(8px);
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
        backdrop-filter: blur(8px);
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

    tenure_agg, hours_agg, strat_counts, heat_pivot, driver_dept, _risk_strat = _chart_aggregates(df)

    st.markdown("#### **Risk Insights**")

    insight_tab = st.radio(
        "Insight view",
        ["📊 Demographics & Trends", "⭕ Risk Composition", "🗺️ Organizational Heatmaps"],
        horizontal=True,
        label_visibility="collapsed",
        key="risk_insight_tab",
    )

    chart_layout = dict(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#64748B'),
        title_font=dict(size=18, color='#F8FAFC', family='Inter'),
        xaxis=dict(showgrid=False, zeroline=False, showline=False, color='#475569', title_font=dict(size=12, color='#64748B')),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.02)', zeroline=False, showline=False, color='#475569', title_font=dict(size=12, color='#64748B')),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#94A3B8'))
    )

    if insight_tab == "📊 Demographics & Trends":
        row1_col1, row1_col2 = st.columns([0.6, 0.4])
        with row1_col1:
            with st.container(border=True):
                fig_area = px.area(tenure_agg, x='Tenure', y='RiskPercentage',
                                   title='Risk Progression by Tenure',
                                   color_discrete_sequence=['#3B82F6'],
                                   template='plotly_dark')
                fig_area.update_traces(line_shape='spline', fillcolor='rgba(59, 130, 246, 0.2)', line=dict(width=4))
                fig_area.update_layout(**chart_layout, height=420, margin=dict(l=30, r=30, t=70, b=30))
                st.plotly_chart(fig_area, use_container_width=True, config=PLOTLY_CONFIG)

        with row1_col2:
            with st.container(border=True):
                fig_line = px.line(hours_agg, x='MonthlyHours', y='RiskPercentage',
                                   title='Avg Risk Trend vs Monthly Hours',
                                   color_discrete_sequence=['#F43F5E'],
                                   template='plotly_dark')
                fig_line.update_traces(line_shape='spline', line=dict(width=4))
                fig_line.update_layout(**chart_layout, height=420, margin=dict(l=30, r=30, t=70, b=30))
                st.plotly_chart(fig_line, use_container_width=True, config=PLOTLY_CONFIG)

    elif insight_tab == "⭕ Risk Composition":
        row2_col1, row2_col2 = st.columns([0.4, 0.6])
        with row2_col1:
            with st.container(border=True):
                fig_donut = px.pie(strat_counts, values='Count', names='Risk Level',
                                   title='Workforce Risk Distribution', hole=0.75,
                                   color='Risk Level',
                                   color_discrete_map={'Low':'#10B981', 'Medium':'#F59E0B', 'High':'#F97316', 'Critical':'#EF4444'},
                                   template='plotly_dark')
                fig_donut.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter', color='#94A3B8'),
                    showlegend=False, height=420, margin=dict(l=30, r=30, t=70, b=30),
                    annotations=[dict(text='Risk', x=0.5, y=0.5, font_size=24, showarrow=False, font_color='#FFFFFF')]
                )
                fig_donut.update_traces(textposition='outside', textinfo='percent+label')
                event_donut = st.plotly_chart(fig_donut, use_container_width=True, on_select="rerun", config=PLOTLY_CONFIG)
                if event_donut and len(event_donut.get("selection", {}).get("points", [])) > 0:
                    pt = event_donut["selection"]["points"][0]
                    label = pt.get("label") or pt.get("point_label") or pt.get("pointNumber")
                    if label is None and isinstance(pt.get("pointNumber"), int):
                        label = strat_counts.iloc[pt["pointNumber"]]['Risk Level']
                    if label:
                        st.session_state.pending_query = f"Summarize the employees in the {label} risk tier."

        with row2_col2:
            with st.container(border=True):
                fig_hist = px.histogram(df, x='RiskPercentage', nbins=30,
                                        title='Risk Score Distribution Density',
                                        color_discrete_sequence=['#8B5CF6'],
                                        template='plotly_dark')
                fig_hist.update_traces(marker=dict(line=dict(width=0)))
                fig_hist.update_layout(**chart_layout, height=420, margin=dict(l=30, r=30, t=70, b=30), bargap=0.1)
                st.plotly_chart(fig_hist, use_container_width=True, config=PLOTLY_CONFIG)

    else:
        row3_col1, row3_col2 = st.columns(2)
        with row3_col1:
            with st.container(border=True):
                colorscale = [[0, '#0B0E14'], [0.5, '#6B21A8'], [1, '#EF4444']]
                fig_heat = px.imshow(heat_pivot, text_auto=".1f", aspect="auto",
                                     title="Department vs. Role Risk Grid",
                                     color_continuous_scale=colorscale,
                                     template='plotly_dark')
                fig_heat.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter', color='#94A3B8'),
                    height=420, margin=dict(l=30, r=30, t=70, b=30)
                )
                fig_heat.update_xaxes(showgrid=False)
                fig_heat.update_yaxes(showgrid=False)
                event_heat = st.plotly_chart(fig_heat, use_container_width=True, on_select="rerun", config=PLOTLY_CONFIG)
                if event_heat and len(event_heat.get("selection", {}).get("points", [])) > 0:
                    pt = event_heat["selection"]["points"][0]
                    y_val = pt.get("y")
                    if y_val:
                        st.session_state.pending_query = f"Analyze flight risk in the {y_val} department."

        with row3_col2:
            with st.container(border=True):
                fig_parallel = px.parallel_categories(driver_dept, dimensions=['Driver1', 'Department'],
                                                      title="Top Driver Cascade to Business Unit",
                                                      color_continuous_scale="Purples",
                                                      template='plotly_dark')
                fig_parallel.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter', color='#94A3B8'),
                    height=420, margin=dict(l=30, r=30, t=70, b=30)
                )
                st.plotly_chart(fig_parallel, use_container_width=True, config=PLOTLY_CONFIG)

def render_top_drivers(df):
    st.markdown("#### **Top Attrition Drivers Distribution**")

    drivers = pd.concat([df['Driver1'], df['Driver2'], df['Driver3']]).dropna()
    driver_counts = drivers.value_counts().reset_index()
    driver_counts.columns = ['Driver', 'Count']

    with st.container(border=True):
        fig = px.bar(driver_counts.head(10), x='Count', y='Driver', orientation='h', 
                     color='Count', color_continuous_scale="Reds")
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=30, b=0), height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', template='plotly_dark')
        event_drivers = st.plotly_chart(fig, use_container_width=True, on_select="rerun", config=PLOTLY_CONFIG)
        if event_drivers and len(event_drivers.get("selection", {}).get("points", [])) > 0:
            pt = event_drivers["selection"]["points"][0]
            driver = pt.get("y")
            if driver:
                st.session_state.pending_query = f"Why is {driver} a top attrition driver?"

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

    macro_metrics, inference_text = _build_macro_metrics(df)

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

    metrics_json = macro_metrics.to_json(orient="records")

    with exec_col1:
        if st.button("📄 Prepare Executive PDF", key="prep_exec_pdf", use_container_width=True):
            st.session_state["_exec_pdf_bytes"] = _cached_exec_pdf(metrics_json, inference_text)
        if st.session_state.get("_exec_pdf_bytes"):
            st.download_button(
                label="⬇️ Download Executive PDF",
                data=st.session_state["_exec_pdf_bytes"],
                file_name="executive_summary.pdf",
                mime="application/pdf",
                key="export_exec_pdf",
                use_container_width=True,
            )
    with exec_col2:
        if st.button("📧 Email Report to HR Leads", key="email_exec_pdf", use_container_width=True):
            if not smtp_host or smtp_host == "smtp.example.com":
                st.toast("⚠️ Please configure SMTP settings in the Configuration popover to send emails.", icon="⚠️")
            else:
                pdf_bytes = _cached_exec_pdf(metrics_json, inference_text)
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
        slack = st.text_input("Slack Webhook URL", type="password", value=slack_url)
        host = st.text_input("SMTP Host", value=smtp_host)
        port = st.number_input("SMTP Port", value=smtp_port)
        user = st.text_input("SMTP User Address", value=smtp_user)
        pw = st.text_input("SMTP App Password", type="password", value=smtp_pass)
        target = st.text_input("Target Manager Email", value=target_email)
        st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
        if st.button("💾 Save Automation Settings", use_container_width=True):
            st.session_state["saved_slack"] = slack
            st.session_state["saved_smtp_host"] = host
            st.session_state["saved_smtp_port"] = port
            st.session_state["saved_smtp_user"] = user
            st.session_state["saved_smtp_pass"] = pw
            st.session_state["saved_target_email"] = target
            st.success("Automation Settings Saved Successfully!")

def render_dashboard(col_dash, df, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email):
    with col_dash:
        with st.container(border=False):
                st.markdown('<div style="padding-right: 20px;">', unsafe_allow_html=True)
                st.markdown("## **Organizational Risk Dashboard**")
                st.markdown("<p style='color: #94A3B8; font-size: 0.9rem; margin-bottom: 24px;'>Real-time insights and predictive flight risk metrics.</p>", unsafe_allow_html=True)
                
                # Toolbar
                tb_col1, tb_col2, tb_col3, tb_col4 = st.columns([4, 1.2, 1.8, 1.2], gap="small")
                with tb_col1:
                    st.text_input("Search...", label_visibility="collapsed", placeholder="🔍 Search employee database...", key="dash_search")
                with tb_col2:
                    st.button("🎛 Filters", use_container_width=True)
                with tb_col3:
                    with st.popover("📥 Ingest Roster Data", use_container_width=True):
                        st.markdown("### **Upload Fresh HR Records**")
                        st.markdown("<p style='color: #64748B; font-size: 0.85rem;'>Select a CSV or Excel file to update the platform core analytics database schema.</p>", unsafe_allow_html=True)
                        uploaded_file = st.file_uploader("Choose file", type=["csv", "xlsx"], label_visibility="collapsed")
                        
                        if uploaded_file is not None:
                            file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                            if st.session_state.get("last_uploaded") != file_key:
                                try:
                                    if uploaded_file.name.endswith('.csv'):
                                        new_df = pd.read_csv(uploaded_file)
                                    else:
                                        new_df = pd.read_excel(uploaded_file)
                                    
                                    with st.spinner("Syncing to core database..."):
                                        project_root = Path(__file__).parent.parent.parent
                                        db_path = project_root / 'hr_data.db'
                                        with sqlite3.connect(db_path) as conn:
                                            core_cols = ['EmployeeID', 'Tenure', 'Department', 'Role', 'MonthlyHours', 'LastPromotion', 'Salary', 'Attrition']
                                            emp_df = new_df[[c for c in core_cols if c in new_df.columns]]
                                            emp_df.to_sql('employees', conn, if_exists='replace', index=False)
                                            
                                            ml_cols = ['EmployeeID', 'RiskPercentage', 'Driver1', 'Driver2', 'Driver3']
                                            if 'RiskPercentage' in new_df.columns:
                                                ml_df = new_df[[c for c in ml_cols if c in new_df.columns]]
                                                ml_df.to_sql('attrition_scores', conn, if_exists='replace', index=False)
                                        
                                        # Clear only data cache (not all caches)
                                        load_risk_data.clear()
                                        _chart_aggregates.clear()
                                        _cached_exec_pdf.clear()
                                        
                                    st.session_state.last_uploaded = file_key
                                    st.session_state.pop("_dash_pdf_bytes", None)
                                    st.session_state.pop("_exec_pdf_bytes", None)
                                    st.success("Database synced successfully! 🚀")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to ingest data: {e}")
                            else:
                                st.success("Database synced successfully! 🚀")
                
                with tb_col4:
                    if st.button("📤 Export", use_container_width=True, key="tb_export_gen"):
                        try:
                            metrics, inf_text = _build_macro_metrics(df)
                            st.session_state["_dash_pdf_bytes"] = _cached_exec_pdf(
                                metrics.to_json(orient="records"), inf_text
                            )
                            st.session_state.pop("_dash_pdf_error", None)
                        except Exception as e:
                            st.session_state["_dash_pdf_error"] = str(e)
                    if st.session_state.get("_dash_pdf_bytes"):
                        st.download_button(
                            "⬇️ PDF",
                            data=st.session_state["_dash_pdf_bytes"],
                            file_name="dashboard_export.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="tb_export_dl",
                        )
                    elif st.session_state.get("_dash_pdf_error"):
                        st.caption("Export unavailable")
                
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

def render_chat_panel(col_chat, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email):
    with col_chat:
        # Render Header and Tabs
        has_recent = "threads" in st.session_state and len(st.session_state.threads) > 1
        recent_style = "color: #94A3B8; cursor: pointer;" if has_recent else "color: #475569; cursor: not-allowed; opacity: 0.5;"
        recent_title_attr = "" if has_recent else 'title="No recent conversations..."'

        st.markdown(f'''
        <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 4px; padding-bottom: 12px; margin-bottom: 16px; flex-shrink: 0;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="background: rgba(124, 58, 237, 0.2); width: 32px; height: 32px; min-height: 32px; border-radius: 50%; color: #A78BFA; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                </div>
                <h3 style="margin: 0; padding: 0; color: #F8FAFC; font-size: 1.1rem; font-weight: 700; line-height: 1.3; white-space: nowrap;">AI Assistant</h3>
                <span style="background: #7C3AED; color: #FFFFFF; font-size: 0.6rem; font-weight: 700; padding: 2px 8px; border-radius: 12px; line-height: 1.2;">BETA</span>
            </div>
            <span style="color: #64748B; cursor: pointer; font-size: 1.2rem;">✕</span>
        </div>
        
        <div style="display: flex; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 24px;">
            <div style="flex: 1; text-align: center; padding: 8px 12px; color: #A78BFA; font-weight: 600; border-bottom: 2px solid #A78BFA; cursor: pointer; font-size: 0.9rem;">Chat</div>
            <div {recent_title_attr} style="flex: 1; text-align: center; padding: 8px 12px; {recent_style} font-weight: 500; font-size: 0.9rem;">Recent Chats</div>
        </div>
        ''', unsafe_allow_html=True)
        
        if "agent_graph" not in st.session_state:
            st.markdown('''
            <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 24px; text-align: center; margin-top: 20px;">
                <h4 style="color: #F8FAFC; margin-bottom: 8px;">Agent Offline</h4>
                <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">Please connect an AI provider via the <b>Configuration</b> tab in the left sidebar.</p>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('<div class="history-marker" style="display:none"></div>', unsafe_allow_html=True)
            chat_container = render_chat_history(slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email)
            # Disclaimer above input so it is never clipped by the panel bottom edge
            st.markdown('''
            <div class="chat-disclaimer-footer" style="background: rgba(30, 41, 59, 0.4); border-radius: 8px; padding: 10px 12px; display: flex; align-items: flex-start; gap: 8px; color: #94A3B8; font-size: 0.75rem;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; margin-top: 1px;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="M12 8v4"></path><path d="M12 16h.01"></path></svg>
                <span>AI responses may not be 100% accurate. Please verify important insights.</span>
            </div>
            ''', unsafe_allow_html=True)
            render_chat_input(chat_container)

def render_chat_history(slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email):
    # Display chat messages from history
    if not st.session_state.active_thread_id:
        current_messages = []
    else:
        current_messages = st.session_state.threads.get(st.session_state.active_thread_id, [])

    chat_container = st.container(border=False)
    with chat_container:
        for idx, msg in enumerate(current_messages):
            avatar = "✨" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                if msg["role"] == "assistant":
                    st.markdown("<span class='assistant-marker' style='display:none'></span>", unsafe_allow_html=True)
                elif msg["role"] == "user":
                    st.markdown("<span class='user-marker' style='display:none'></span>", unsafe_allow_html=True)
                
                st.markdown(msg["content"])

                # Action buttons only on the latest assistant message (cuts widget/DOCX cost)
                is_last_assistant = (
                    msg["role"] == "assistant"
                    and idx == max((i for i, m in enumerate(current_messages) if m["role"] == "assistant"), default=-1)
                )
                if is_last_assistant and idx > 0:
                    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)

                    # Action row — short labels, small gap (fits narrow chat column)
                    btn_col1, btn_col2, btn_col3 = st.columns(3, gap="small")
                    with btn_col1:
                        docx_bytes = _cached_docx(msg["content"])
                        st.download_button(
                            label="DOCX",
                            data=docx_bytes,
                            file_name=f"chat_export_{idx}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"docx_{idx}",
                            use_container_width=True,
                            icon=":material/description:",
                        )
                    with btn_col2:
                        if st.button("Email", key=f"pdf_{idx}", use_container_width=True, icon=":material/mail:"):
                            if not smtp_host or smtp_host == "smtp.example.com":
                                st.toast("⚠️ Please configure SMTP settings in the Configuration popover to send emails.", icon="⚠️")
                            else:
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
                        if st.button("Slack", key=f"alert_{idx}", use_container_width=True, icon=":material/chat:"):
                            if not slack_url or not slack_url.startswith("https://hooks.slack.com"):
                                st.toast("⚠️ Please configure your Slack Webhook URL in settings.", icon="⚠️")
                            else:
                                import re
                                emp_match = re.search(r'EMP\d{4}', msg["content"])
                                employee_id = emp_match.group(0) if emp_match else "Multiple / General Insights"

                                risk_match = re.search(r'(\d{2,3}\.\d)%', msg["content"])
                                risk_score = float(risk_match.group(1)) if risk_match else "N/A"

                                content_clean = msg["content"].replace("*", "")
                                note_snippet = content_clean[:800] + ("..." if len(content_clean) > 800 else "")

                                success = dispatch_critical_alert(
                                    webhook_url=slack_url,
                                    employee_id=employee_id,
                                    risk_score=risk_score,
                                    mitigation_note=note_snippet
                                )
                                if success:
                                    st.toast("Slack Alert Triggered!", icon="✅")
                                else:
                                    st.error("Failed to send Slack alert.")

                    # Follow-ups: one button per cell (avoids stacked-column overlap)
                    st.markdown(
                        "<div style='margin-top: 12px; margin-bottom: 6px; color: #94A3B8; font-size: 0.8rem; font-weight: 500;'>✨ Suggested Follow-up</div>",
                        unsafe_allow_html=True,
                    )
                    fu_r1c1, fu_r1c2 = st.columns(2, gap="small")
                    with fu_r1c1:
                        if st.button("Show Employees", key=f"fu1_{idx}", use_container_width=True):
                            st.session_state.pending_query = "Show the employees for this analysis"
                    with fu_r1c2:
                        if st.button("Compare Depts", key=f"fu2_{idx}", use_container_width=True):
                            st.session_state.pending_query = "Compare risk across departments"
                    fu_r2c1, fu_r2c2 = st.columns(2, gap="small")
                    with fu_r2c1:
                        if st.button("Email Manager", key=f"fu3_{idx}", use_container_width=True):
                            st.session_state.pending_query = "Draft an email to the manager"
                    with fu_r2c2:
                        if st.button("Create Plan", key=f"fu4_{idx}", use_container_width=True):
                            st.session_state.pending_query = "Create a retention action plan"

        # Empty state / Suggested Questions
        if not current_messages:
            q1 = "💬 How does attrition risk vary by department?"
            q2 = "💬 Show high risk employees with low tenure"
            q3 = "💬 What impact will attrition have on our business?"
            q4 = "💬 Compare risk trends with previous quarter"
            
            if st.button(q1, key="suggested_1", use_container_width=True):
                st.session_state.pending_query = q1.replace("💬 ", "")
            if st.button(q2, key="suggested_2", use_container_width=True):
                st.session_state.pending_query = q2.replace("💬 ", "")
            if st.button(q3, key="suggested_3", use_container_width=True):
                st.session_state.pending_query = q3.replace("💬 ", "")
            if st.button(q4, key="suggested_4", use_container_width=True):
                st.session_state.pending_query = q4.replace("💬 ", "")

    return chat_container

def render_chat_input(chat_container):
    prompt = st.chat_input("Ask anything about attrition...")
    if "pending_query" in st.session_state and st.session_state.pending_query:
        prompt = st.session_state.pending_query
        st.session_state.pending_query = None

    if prompt:
        with chat_container:
            if not st.session_state.active_thread_id:
                st.session_state.active_thread_id = str(uuid.uuid4())
                st.session_state.threads[st.session_state.active_thread_id] = []

            st.chat_message("user", avatar="👤").markdown(f"<span class='user-marker' style='display:none'></span>{prompt}", unsafe_allow_html=True)
            st.session_state.threads[st.session_state.active_thread_id].append({"role": "user", "content": prompt})

            with st.chat_message("assistant", avatar="✨"):
                st.markdown("<span class='assistant-marker' style='display:none'></span>", unsafe_allow_html=True)
                message_placeholder = st.empty()
                with st.spinner("Analyzing..."):
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

@st.cache_data(show_spinner=False)
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
    slack_url = st.session_state.get("saved_slack", os.environ.get("SLACK_WEBHOOK_URL", ""))
    smtp_host = st.session_state.get("saved_smtp_host", os.environ.get("SMTP_HOST", ""))
    smtp_port = int(st.session_state.get("saved_smtp_port", os.environ.get("SMTP_PORT", 587)))
    smtp_user = st.session_state.get("saved_smtp_user", os.environ.get("SMTP_USER", ""))
    smtp_pass = st.session_state.get("saved_smtp_pass", os.environ.get("SMTP_PASS", ""))
    target_email = st.session_state.get("saved_target_email", "manager@thinkpalm.com")
    


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

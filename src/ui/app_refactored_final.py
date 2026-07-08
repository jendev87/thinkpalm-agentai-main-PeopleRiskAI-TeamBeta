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

st.set_page_config(page_title="PeopleRisk AI", page_icon="🎯", layout="wide")

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
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
    /* 2. LAYOUT */
    /* ========================================== */
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
        padding-left: 10px !important;
        padding-right: 5px !important;
        height: calc(100vh - 60px) !important;
        padding-top: 60px !important;
        display: flex !important;
        flex-direction: column !important;
        padding-bottom: 0 !important;
    }

    [data-testid="stHorizontalBlock"] {
        flex: 1 !important;
        height: 100% !important;
        align-items: stretch !important;
    }

    /* Dashboard Column */
    div[data-testid="column"]:nth-of-type(2) {
        height: 100% !important;
        overflow-y: auto !important;
        padding: 32px 40px !important;
    }
    div[data-testid="column"]:nth-of-type(2) > div[data-testid="stVerticalBlock"] {
        gap: 24px !important;
    }

    /* Chat Column */
    div[data-testid="column"]:nth-of-type(3) {
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        overflow: hidden !important;
    }
    div[data-testid="column"]:nth-of-type(3) > div[data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        flex: 1 !important;
    }

    /* ========================================== */
    /* 3. SIDEBAR (NAV) */
    /* ========================================== */
    div[data-testid="column"]:nth-of-type(1) {
        height: 100% !important;
        overflow-y: hidden !important;
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
        background: rgba(28, 33, 48, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 20px 24px !important;
        border-radius: 16px !important;
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
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 8px 12px;
        border: 1px solid rgba(255,255,255,0.06);
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
        position: static !important;
        margin-top: auto !important;
        padding-bottom: 24px !important;
        padding-top: 12px !important;
    }
    div[data-testid="stChatInput"] textarea {
        border: 1px solid rgba(59, 130, 246, 0.25) !important;
        background-color: #161C2A !important;
        border-radius: 28px !important;
        transition: all 0.25s ease-in-out !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stChatInput"] textarea:focus {
        border: 1px solid rgba(59, 130, 246, 0.6) !important;
        background-color: #1A2337 !important;
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
        with st.container(border=False):
            st.markdown("<h3 style='color: #FFFFFF; margin-bottom: 20px;'>Navigation</h3>", unsafe_allow_html=True)

            # Render vertical workspace links
            if st.button("📊 Risk Overview", use_container_width=True):
                st.session_state.active_navigation = "📊 Risk Overview"
                st.rerun()
            if st.button("🎯 Top Drivers", use_container_width=True):
                st.session_state.active_navigation = "🎯 Top Drivers"
                st.rerun()
            if st.button("📋 High Risk Roster", use_container_width=True):
                st.session_state.active_navigation = "📋 High Risk Roster"
                st.rerun()
            if st.button("⚙️ Executive Summary", use_container_width=True):
                st.session_state.active_navigation = "⚙️ Executive Summary"
                st.rerun()
            if st.button("⚙️ Configuration", use_container_width=True):
                st.session_state.active_navigation = "⚙️ Configuration"
                st.rerun()

def render_risk_overview(df):
    st.markdown("#### **Core KPIs**")
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    total_emp = len(df)
    high_risk = len(df[df['RiskPercentage'] > 75])
    avg_risk = df['RiskPercentage'].mean()

    # Column 1 Example (Total Employees)
    kpi_col1.markdown(f'''
    <div style="
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 22px 24px;
        transition: transform 0.2s ease-in-out;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="color: #94A3B8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">👥 Employees</span>
            <span style="background: rgba(34, 197, 94, 0.15); color: #4ADE80; font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 20px;">+12 this week</span>
        </div>
        <div style="font-size: 2.25rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.03em;">{total_emp:,}</div>
    </div>
    ''', unsafe_allow_html=True)

    # Column 2 Example (High Flight Risk)
    kpi_col2.markdown(f'''
    <div style="
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 22px 24px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="color: #94A3B8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">🚨 High Flight Risk</span>
            <span style="background: rgba(239, 68, 68, 0.15); color: #F87171; font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 20px;">+4% from May</span>
        </div>
        <div style="font-size: 2.25rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.03em;">{high_risk:,}</div>
    </div>
    ''', unsafe_allow_html=True)


    # Column 3 Example (Average Risk Score)
    kpi_col3.markdown(f'''
    <div style="
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 22px 24px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="color: #94A3B8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">📈 Average Risk Score</span>
            <span style="background: rgba(239, 68, 68, 0.15); color: #F87171; font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 20px;">+1.2% delta</span>
        </div>
        <div style="font-size: 2.25rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.03em;">{avg_risk:.1f}%</div>
    </div>
    ''', unsafe_allow_html=True)

    # Risk Stratification Bins
    bins = [0, 25, 50, 75, 100]
    labels = ['Low', 'Medium', 'High', 'Critical']
    df['RiskStratification'] = pd.cut(df['RiskPercentage'], bins=bins, labels=labels, include_lowest=True)

    st.markdown("#### **Comprehensive Risk Insights**")
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    row3_col1, row3_col2 = st.columns(2)

    with row1_col1:
        with st.container(border=True):
            # Area Chart: Risk Progression by Tenure Band
            tenure_agg = df.groupby('Tenure', as_index=False)['RiskPercentage'].mean()
            fig_area = px.area(tenure_agg, x='Tenure', y='RiskPercentage', 
                               title='Risk Progression by Tenure', 
                               color_discrete_sequence=['#FF3366'],
                               template='plotly_dark')
            fig_area.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_area, use_container_width=True)

    with row1_col2:
        with st.container(border=True):
            # Line Chart: Average Risk vs Monthly Hours
            hours_agg = df.groupby('MonthlyHours', as_index=False)['RiskPercentage'].mean()
            fig_line = px.line(hours_agg, x='MonthlyHours', y='RiskPercentage', 
                               title='Avg Risk Trend vs Monthly Hours',
                               color_discrete_sequence=['#38BDF8'],
                               template='plotly_dark')
            fig_line.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_line, use_container_width=True)

    with row2_col1:
        with st.container(border=True):
            # Donut Chart
            strat_counts = df['RiskStratification'].value_counts().reset_index()
            strat_counts.columns = ['Risk Level', 'Count']
            fig_donut = px.pie(strat_counts, values='Count', names='Risk Level', 
                               title='Workforce Risk Distribution', hole=0.6,
                               color='Risk Level',
                               color_discrete_map={'Low':'#10B981', 'Medium':'#FBBF24', 'High':'#F97316', 'Critical':'#EF4444'},
                               template='plotly_dark')
            fig_donut.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            event_donut = st.plotly_chart(fig_donut, use_container_width=True, on_select="rerun")
            if event_donut and len(event_donut.get("selection", {}).get("points", [])) > 0:
                pt = event_donut["selection"]["points"][0]
                label = pt.get("label") or pt.get("point_label") or pt.get("pointNumber")
                # Using pointNumber to look up from strat_counts if label is missing
                if label is None and isinstance(pt.get("pointNumber"), int):
                    label = strat_counts.iloc[pt["pointNumber"]]['Risk Level']
                if label:
                    st.session_state.pending_query = f"Summarize the employees in the {label} risk tier."
                    st.rerun()

    with row2_col2:
        with st.container(border=True):
            # Histogram Density
            fig_hist = px.histogram(df, x='RiskPercentage', nbins=30, 
                                    title='Risk Score Distribution Density',
                                    marginal='box',
                                    color_discrete_sequence=['#8B5CF6'],
                                    template='plotly_dark')
            fig_hist.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_hist, use_container_width=True)

    with row3_col1:
        with st.container(border=True):
            # Heatmap: Department vs Role Risk
            heat_agg = df.groupby(['Department', 'Role'], as_index=False)['RiskPercentage'].mean()
            heat_pivot = heat_agg.pivot(index='Department', columns='Role', values='RiskPercentage').fillna(0)
            fig_heat = px.imshow(heat_pivot, text_auto=".1f", aspect="auto", 
                                 title="Department vs. Role Risk Grid",
                                 color_continuous_scale="Reds",
                                 template='plotly_dark')
            fig_heat.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            event_heat = st.plotly_chart(fig_heat, use_container_width=True, on_select="rerun")
            if event_heat and len(event_heat.get("selection", {}).get("points", [])) > 0:
                pt = event_heat["selection"]["points"][0]
                y_val = pt.get("y")  # Department
                if y_val:
                    st.session_state.pending_query = f"Analyze flight risk in the {y_val} department."
                    st.rerun()

    with row3_col2:
        with st.container(border=True):
            # Parallel Categories (Flow breakdown) for Top Driver to Department
            driver_dept = df[['Driver1', 'Department']].dropna()
            fig_parallel = px.parallel_categories(driver_dept, dimensions=['Driver1', 'Department'],
                                                  title="Top Driver Cascade to Business Unit",
                                                  color_continuous_scale="Reds",
                                                  template='plotly_dark')
            fig_parallel.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
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
    st.markdown("#### **High Risk Roster**")
    with st.container(border=True):
        st.dataframe(df[df['RiskPercentage'] > 75].sort_values('RiskPercentage', ascending=False).head(10), use_container_width=True, height=400)

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
        st.dataframe(macro_metrics, use_container_width=True)

    highest_risk_dept = macro_metrics.loc[macro_metrics['Average_Risk'].idxmax()]

    inference_text = (
        f"Critical Alert: The **{highest_risk_dept['Department']}** segment displays disproportionate "
        f"flight risk ({highest_risk_dept['Average_Risk']}% avg) primarily driven by **{highest_risk_dept['Top_Driver']}**."
    )

    st.info(f"💡 **AI Inference:** {inference_text}", icon="🤖")

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
                st.markdown("### **Organizational Risk Dashboard**")
                st.markdown("*Real-time insights and predictive flight risk metrics.*")

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
    
    # Render the actual header title
    head_col1, head_col2 = st.columns([0.8, 0.2])
    with head_col1:
        st.markdown("# 🎯 **PeopleRisk AI Workspace**")
        st.markdown("*Enterprise HR Attrition Prediction & Conversational Intelligence*")
    
    # Extract config variables to pass down
    slack_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    target_email = "manager@thinkpalm.com"
    
    st.divider()

    df = load_risk_data()
    
    if df.empty or 'RiskPercentage' not in df.columns:
        st.warning("No data found. Ensure the ML pipeline (Phase 2) has run.")
        st.stop()
        
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    
    # Main layout matching implementation_plan.md
    col_nav, col_dash, col_chat = st.columns([1.5, 6.0, 2.5], gap="small")
    
    render_sidebar(col_nav)
    render_dashboard(col_dash, df, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email)
    render_chat_panel(col_chat, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email)

if __name__ == "__main__":
    main()

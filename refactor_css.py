import re

with open("src/ui/app.py", "r") as f:
    content = f.read()

# We need to extract everything between <style> and </style> and replace it with the clean architecture.
style_pattern = re.compile(r'<style>.*?</style>', re.DOTALL)

clean_css = """<style>
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
</style>"""

new_content = style_pattern.sub(clean_css, content)

with open("src/ui/app.py", "w") as f:
    f.write(new_content)

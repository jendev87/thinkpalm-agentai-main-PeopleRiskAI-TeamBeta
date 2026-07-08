with open("src/ui/app.py", "r") as f:
    content = f.read()

# 1. Revert header hiding and overflow hidden
css_target_1 = """/* Apply font across the entire layout container */
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    background-color: #0B0E14 !important;
}
[data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp {
    overflow: hidden !important; /* Kill the outer main page scrollbar */
}

/* Remove default heavy left padding to align dashboard with sidebar */
.block-container {
    padding-left: 10px !important;
    padding-right: 5px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}

/* Hide the empty Streamlit top header bar to reclaim vertical real estate */
header[data-testid="stHeader"] {
    display: none !important;
}"""

css_replace_1 = """/* Apply font across the entire layout container */
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    background-color: #0B0E14 !important;
}

/* Remove default heavy left padding to align dashboard with sidebar */
.block-container {
    padding-left: 10px !important;
    padding-right: 5px !important;
}"""

content = content.replace(css_target_1, css_replace_1)

# 2. Revert the scrollable pane anchor CSS to the original sticky right column
css_target_2 = """/* Responsive Scrollable Main Panes (using anchor class to perfectly target) */
div[data-testid="column"]:has(.scrollable-pane-anchor) {
    height: calc(100vh - 80px) !important;
    overflow-y: auto !important;
    padding-right: 12px !important;
}

/* Force visible custom scrollbar so it never disappears on Mac */
div[data-testid="column"]:has(.scrollable-pane-anchor)::-webkit-scrollbar {
    display: block !important;
    width: 6px !important;
    background-color: transparent !important;
}
div[data-testid="column"]:has(.scrollable-pane-anchor)::-webkit-scrollbar-thumb {
    background-color: rgba(255, 255, 255, 0.2) !important;
    border-radius: 10px !important;
}
div[data-testid="column"]:has(.scrollable-pane-anchor)::-webkit-scrollbar-thumb:hover {
    background-color: rgba(255, 255, 255, 0.4) !important;
}"""

css_replace_2 = """/* Sticky Right Column (ChatGPT Style) */
div[data-testid="column"]:nth-of-type(2) {
    position: sticky !important;
    top: 40px !important;
    height: calc(100vh - 40px) !important;
    overflow-y: hidden !important;
}"""

content = content.replace(css_target_2, css_replace_2)

# 3. Revert Python code anchors and restore height=820 containers
dash_target = """# --- PANEL: Interactive Dashboard ---
with col_dash:
    st.markdown('<div class="scrollable-pane-anchor"></div>', unsafe_allow_html=True)
    with st.container(border=False):"""

dash_replace = """# --- PANEL: Interactive Dashboard ---
with col_dash:
    with st.container(height=820, border=False):"""
    
content = content.replace(dash_target, dash_replace)

chat_target = """    # --- PANEL 3: Conversation Copilot ---
with col_chat:
    st.markdown('<div class="scrollable-pane-anchor"></div>', unsafe_allow_html=True)
    with st.container(border=False):"""

chat_replace = """    # --- PANEL 3: Conversation Copilot ---
with col_chat:
    with st.container(height=820, border=False):"""

content = content.replace(chat_target, chat_replace)

with open("src/ui/app.py", "w") as f:
    f.write(content)


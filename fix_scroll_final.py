with open("src/ui/app.py", "r") as f:
    content = f.read()

# Add the CSS for responsive columns
css_to_insert = """
/* Responsive Scrollable Main Panes (using anchor class to perfectly target) */
div[data-testid="column"]:has(.scrollable-pane-anchor) {
    height: calc(100vh - 120px) !important;
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
}
</style>"""

content = content.replace("</style>", css_to_insert)

# Inject anchors and remove height=820
dash_target = """# --- PANEL: Interactive Dashboard ---
with col_dash:
    with st.container(height=820, border=False):"""

dash_replace = """# --- PANEL: Interactive Dashboard ---
with col_dash:
    st.markdown('<div class="scrollable-pane-anchor"></div>', unsafe_allow_html=True)
    with st.container(border=False):"""
    
content = content.replace(dash_target, dash_replace)

chat_target = """    # --- PANEL 3: Conversation Copilot ---
with col_chat:
    with st.container(height=820, border=False):"""

chat_replace = """    # --- PANEL 3: Conversation Copilot ---
with col_chat:
    st.markdown('<div class="scrollable-pane-anchor"></div>', unsafe_allow_html=True)
    with st.container(border=False):"""

content = content.replace(chat_target, chat_replace)

with open("src/ui/app.py", "w") as f:
    f.write(content)


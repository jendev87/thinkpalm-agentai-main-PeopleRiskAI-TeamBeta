import re

with open("src/ui/app.py", "r") as f:
    content = f.read()

# 1. Inject CSS Flexbox
css_injection = """
/* Flexbox Layout Overrides */
.block-container {
    height: calc(100vh - 80px) !important;
    display: flex !important;
    flex-direction: column !important;
    padding-bottom: 0 !important;
}

[data-testid="stHorizontalBlock"] {
    flex: 1 !important;
    height: 100% !important;
    align-items: stretch !important;
}

/* Nav Column */
div[data-testid="column"]:nth-of-type(1) {
    height: 100% !important;
    overflow-y: hidden !important;
}

/* Dashboard Column */
div[data-testid="column"]:nth-of-type(2) {
    height: 100% !important;
    overflow-y: auto !important;
    padding-right: 10px !important;
}

/* AI Copilot Column */
div[data-testid="column"]:nth-of-type(3) {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}

/* Copilot Inner Wrap */
div[data-testid="column"]:nth-of-type(3) > div[data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    flex: 1 !important;
}

/* Chat History Flex Area */
div[data-testid="stVerticalBlock"]:has(.chat-history-anchor) {
    flex: 1 !important;
    overflow-y: auto !important;
    padding-right: 8px !important;
}

/* Chat Input Docking */
div[data-testid="stChatInput"] {
    position: static !important;
    margin-top: auto !important;
    padding-bottom: 24px !important;
    padding-top: 12px !important;
}
"""

content = content.replace("</style>", css_injection + "</style>")

# 2. Remove VIEWPORT_HEIGHT logic and replace with normal containers
content = re.sub(r'# Define a height variable based on a standard 1080p-optimized viewport\nVIEWPORT_HEIGHT = 760 \n', '', content)
content = content.replace('with st.container(height=VIEWPORT_HEIGHT, border=False):', 'with st.container(border=False):')

# 3. Add anchor to chat container
content = content.replace(
    'chat_container = st.container(border=False)',
    'chat_container = st.container(border=False)\n                with chat_container:\n                    st.markdown("<div class=\'chat-history-anchor\'></div>", unsafe_allow_html=True)'
)

# 4. Strip out the duplicate block of code from 896 to 940 (the duplicated pending_query check)
# The duplicate starts with '            if "pending_query" in st.session_state and st.session_state.pending_query:'
duplicate_pattern = r'            if "pending_query" in st.session_state and st.session_state.pending_query:(?:.*?)(?=\n$|$)'
# Since there are TWO, we want to remove the last one.
parts = content.rsplit('            if "pending_query" in st.session_state and st.session_state.pending_query:', 1)
if len(parts) > 1:
    content = parts[0]

with open("src/ui/app.py", "w") as f:
    f.write(content)

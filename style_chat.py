import re

with open("src/ui/app.py", "r") as f:
    content = f.read()

# 1. Update Recent Chats CSS
content = content.replace("""/* Recent Chat History Link Row */
.recent-chat-row {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    color: #94A3B8;
    font-size: 0.85rem;
    margin-bottom: 6px;
    transition: all 0.2s ease;
}""", """/* Recent Chat History Link Row */
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
}""")

# 2. Update Suggested Questions Pill Buttons
content = content.replace("""border-radius: 24px !important;
                padding: 8px 16px !important;""",
"""border-radius: 999px !important;
                padding: 6px 16px !important;""")

# 3. Provider Status Update
old_provider = """<div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #FFFFFF; font-weight: 600; font-size: 1.05rem; letter-spacing: -0.01em;">✨ {active_provider}</span>
                    <span style="background: rgba(34, 197, 94, 0.12); color: #4ADE80; font-size: 0.7rem; font-weight: 600; padding: 3px 8px; border-radius: 20px; display: inline-flex; align-items: center; gap: 5px;">
                        <span style="width: 5px; height: 5px; background-color: #4ADE80; border-radius: 50%;"></span> Connected
                    </span>
                </div>"""
new_provider = """<div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #FFFFFF; font-weight: 600; font-size: 0.95rem; letter-spacing: -0.01em;">✨ {active_provider}</span>
                    <span style="background: rgba(34, 197, 94, 0.15); color: #4ADE80; font-size: 0.65rem; font-weight: 700; padding: 2px 6px; border-radius: 12px; display: inline-flex; align-items: center; gap: 4px; text-transform: uppercase; letter-spacing: 0.05em;">
                        <span style="width: 4px; height: 4px; background-color: #4ADE80; border-radius: 50%;"></span> Active
                    </span>
                </div>"""
content = content.replace(old_provider, new_provider)


# 4. Inject User Markers in python code
# A. historical loop
content = content.replace("""                        if msg["role"] == "assistant":
                            st.markdown("<span class='assistant-marker'></span>", unsafe_allow_html=True)
                        st.markdown(msg["content"])""",
"""                        if msg["role"] == "assistant":
                            st.markdown("<span class='assistant-marker'></span>", unsafe_allow_html=True)
                        elif msg["role"] == "user":
                            st.markdown("<span class='user-marker'></span>", unsafe_allow_html=True)
                        st.markdown(msg["content"])""")

# B. New prompt rendering
content = content.replace('st.chat_message("user", avatar="👤").markdown(prompt)',
                          'st.chat_message("user", avatar="👤").markdown(f"<span class=\'user-marker\'></span>{prompt}", unsafe_allow_html=True)')


# 5. Inject CSS for User/Assistant messages
chat_css = """
/* Assistant Messages */
div[data-testid="stChatMessage"]:has(.assistant-marker) {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    padding: 8px 12px;
    border: 1px solid rgba(255,255,255,0.06);
}

/* User Messages */
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
"""
content = content.replace('</style>', chat_css + '\n</style>')

with open("src/ui/app.py", "w") as f:
    f.write(content)

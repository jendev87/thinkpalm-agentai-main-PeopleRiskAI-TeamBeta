import re

with open("src/ui/app.py", "r") as f:
    content = f.read()

# 1. Update Columns Layout
content = content.replace(
    'col_dash, col_chat = st.columns([7.5, 2.5], gap="medium")',
    'col_nav, col_dash, col_chat = st.columns([1.5, 6.0, 2.5], gap="small")'
)

# 2. Extract sidebar content and move to col_nav
sidebar_pattern = r"        with st\.sidebar:\n(.*?)(?=        if st\.session_state\.active_navigation)"
match = re.search(sidebar_pattern, content, re.DOTALL)
if match:
    sidebar_content = match.group(1)
    # Remove from col_dash
    content = content.replace("        with st.sidebar:\n" + sidebar_content, "")
    
    # Unindent and wrap in col_nav
    unindented_sidebar = "\n".join([line[4:] if line.startswith("    ") else line for line in sidebar_content.split("\n")])
    nav_block = f"""# --- PANEL 1: Navigation ---
with col_nav:
    with st.container(height=VIEWPORT_HEIGHT, border=False):
{unindented_sidebar}
"""
    # Insert before col_dash
    content = content.replace(
        '# --- PANEL: Interactive Dashboard ---',
        nav_block + '# --- PANEL 2: Interactive Dashboard ---'
    )

# 3. Update CSS styles (remove glassmorphism, flat borders)
content = content.replace(
    'background: rgba(30, 41, 59, 0.45) !important;',
    'background: #141C2B !important;'
)
content = content.replace(
    'border: 1px solid rgba(255, 255, 255, 0.08) !important;',
    'border: 1px solid rgba(255, 255, 255, 0.05) !important;'
)
content = content.replace(
    'border: 1px solid rgba(255, 255, 255, 0.06) !important;',
    'border: 1px solid rgba(255, 255, 255, 0.05) !important;'
)
content = re.sub(r'box-shadow:.*?;', '', content)
content = re.sub(r'backdrop-filter:.*?;', '', content)
content = re.sub(r'-webkit-backdrop-filter:.*?;', '', content)

# Also update inline styles for KPIs
content = content.replace(
    'background: rgba(30, 41, 59, 0.45);',
    'background: #141C2B;'
)
content = content.replace(
    'border: 1px solid rgba(255, 255, 255, 0.06);',
    'border: 1px solid rgba(255, 255, 255, 0.05);'
)

# 4. Hide scrollbars gracefully for the sleek look (VS Code style)
css_scrollbars = """
/* VS Code style scrollbars */
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
"""
content = content.replace('</style>', css_scrollbars + '</style>')

with open("src/ui/app.py", "w") as f:
    f.write(content)

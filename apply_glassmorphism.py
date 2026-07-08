import re

with open("src/ui/app.py", "r") as f:
    content = f.read()

# 1. Update Custom Header CSS to be Glassmorphic
old_header_css = """header[data-testid="stHeader"] {
    background-color: #0B0E14 !important;
    height: 60px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}"""
new_header_css = """header[data-testid="stHeader"] {
    background: rgba(11, 14, 20, 0.7) !important;
    backdrop-filter: blur(20px) !important;
    height: 60px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
}"""
content = content.replace(old_header_css, new_header_css)

# 2. Inject Streamlit Default Overrides
global_overrides = """
/* Global Streamlit UI Overrides for Glassmorphism */
div.stButton > button:not([key^="suggested_"]) {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.2s ease-in-out !important;
}
div.stButton > button:not([key^="suggested_"]):hover {
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15) !important;
    transform: translateY(-1px) !important;
}

/* Inputs & Selectboxes */
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
"""
content = content.replace('</style>', global_overrides + '\n</style>')

# 3. Replace Solid Dashboard colors with Glassmorphism
glass_style = """background: rgba(255, 255, 255, 0.02);
                backdrop-filter: blur(16px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);"""
content = content.replace("background: #141C2B;", glass_style)

# 4. Global border-radius update
content = content.replace("border-radius: 14px;", "border-radius: 16px;")

with open("src/ui/app.py", "w") as f:
    f.write(content)

import re

with open("src/ui/app.py", "r") as f:
    content = f.read()

# 1. Update CSS
css_old = """/* Flexbox Layout Overrides */
.block-container {
    height: calc(100vh - 80px) !important;
    display: flex !important;
    flex-direction: column !important;
    padding-bottom: 0 !important;
}"""

css_new = """/* Custom Header & Layout Overrides */
header[data-testid="stHeader"] {
    background-color: #0B0E14 !important;
    height: 60px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}
.block-container {
    height: calc(100vh - 60px) !important;
    padding-top: 60px !important;
    display: flex !important;
    flex-direction: column !important;
    padding-bottom: 0 !important;
}"""
content = content.replace(css_old, css_new)

# 2. Replace Python Header section
header_old = """# ==========================================
# HEADER
# ==========================================
st.markdown("# 🎯 **PeopleRisk AI Workspace**")
st.markdown("*Enterprise HR Attrition Prediction & Conversational Intelligence*")
st.divider()"""

header_new = """# ==========================================
# HEADER (Custom Injected)
# ==========================================
st.markdown('''
<div style="position: fixed; top: 0; left: 20px; right: 180px; height: 60px; display: flex; align-items: center; justify-content: space-between; z-index: 999999; pointer-events: none;">
    <div style="display: flex; align-items: center; pointer-events: auto;">
        <span style="font-size: 1.4rem; margin-right: 10px;">🎯</span>
        <span style="font-weight: 600; font-size: 1.05rem; color: #FFFFFF; margin-right: 16px; letter-spacing: -0.01em;">PeopleRisk AI</span>
        <span style="color: #64748B; font-size: 0.8rem; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 16px; font-weight: 500;">HR Attrition Intelligence</span>
    </div>
    <div style="display: flex; align-items: center; gap: 16px; pointer-events: auto;">
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 6px 12px; border-radius: 6px; display: flex; align-items: center; gap: 8px; width: 240px; color: #64748B; font-size: 0.8rem;">
            <span>🔍</span> Search workspace...
        </div>
        <div style="width: 28px; height: 28px; border-radius: 50%; background: #3B82F6; color: white; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 600; border: 2px solid #1E293B;">
            JD
        </div>
    </div>
</div>
''', unsafe_allow_html=True)"""
content = content.replace(header_old, header_new)

with open("src/ui/app.py", "w") as f:
    f.write(content)


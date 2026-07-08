with open("src/ui/app.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "row1_col1, row1_col2, row1_col3 = st.columns(3)" in line:
        new_lines.append(line.replace("row1_col1, row1_col2, row1_col3 = st.columns(3)", "row1_col1, row1_col2 = st.columns(2)"))
    elif "row2_col1, row2_col2, row2_col3 = st.columns(3)" in line:
        new_lines.append(line.replace("row2_col1, row2_col2, row2_col3 = st.columns(3)", "row2_col1, row2_col2 = st.columns(2)\n            row3_col1, row3_col2 = st.columns(2)"))
    
    # Chart mapping
    elif "with row1_col3:" in line:
        new_lines.append(line.replace("with row1_col3:", "with row2_col1:"))
    
    # Since Histogram is currently row2_col1, we change it to row2_col2
    elif "with row2_col1:" in line:
        # Donut became row2_col1 just now, but wait! We iterate sequentially!
        # If we just do simple replacements on the fly, it's safer to identify the chart blocks
        pass
        
with open("src/ui/app.py", "r") as f:
    content = f.read()
    
# Replace columns
content = content.replace("row1_col1, row1_col2, row1_col3 = st.columns(3)\n            row2_col1, row2_col2, row2_col3 = st.columns(3)", 
                          "row1_col1, row1_col2 = st.columns(2)\n            row2_col1, row2_col2 = st.columns(2)\n            row3_col1, row3_col2 = st.columns(2)")

# The order currently in the file:
# 1. Area (row1_col1)
# 2. Line (row1_col2)
# 3. Donut (row1_col3)
# 4. Hist (row2_col1)
# 5. Heat (row2_col2)
# 6. Parallel (row2_col3)

# We want:
# 1. Area (row1_col1)
# 2. Line (row1_col2)
# 3. Donut (row2_col1)
# 4. Hist (row2_col2)
# 5. Heat (row3_col1)
# 6. Parallel (row3_col2)

content = content.replace("with row1_col3:", "with row2_col1:")
# Wait, if I replace row2_col1 to row2_col2 here, it will ALSO replace the one I just created!
# So I must replace from bottom up or use specific tags.

content = content.replace("            with row2_col3:\n                with st.container(border=True):\n                    # Parallel Categories",
                          "            with row3_col2:\n                with st.container(border=True):\n                    # Parallel Categories")

content = content.replace("            with row2_col2:\n                with st.container(border=True):\n                    # Heatmap",
                          "            with row3_col1:\n                with st.container(border=True):\n                    # Heatmap")

content = content.replace("            with row2_col1:\n                with st.container(border=True):\n                    # Histogram",
                          "            with row2_col2:\n                with st.container(border=True):\n                    # Histogram")

content = content.replace("            with row1_col3:\n                with st.container(border=True):\n                    # Donut",
                          "            with row2_col1:\n                with st.container(border=True):\n                    # Donut")

# Add padding to dash_container
content = content.replace("""    with st.container(height=820, border=False):
        st.markdown("### **Organizational Risk Dashboard**")""",
"""    with st.container(height=820, border=False):
        st.markdown('<div style="padding-right: 20px;">', unsafe_allow_html=True)
        st.markdown("### **Organizational Risk Dashboard**")""")

# Close the padding div at the end of col_dash
content = content.replace("""            st.text_input("Target Manager Email", value="manager@thinkpalm.com", key="form_target_email")

# --- PANEL 3: Conversation Copilot ---""",
"""            st.text_input("Target Manager Email", value="manager@thinkpalm.com", key="form_target_email")
        st.markdown('</div>', unsafe_allow_html=True)

# --- PANEL 3: Conversation Copilot ---""")

with open("src/ui/app.py", "w") as f:
    f.write(content)


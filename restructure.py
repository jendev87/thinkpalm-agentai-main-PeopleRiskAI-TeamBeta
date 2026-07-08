with open("src/ui/app.py", "r") as f:
    content = f.read()

# 1. First block replacement
target1 = """            st.divider()

            # --- ROW 1: MACRO DYNAMICS ---
            st.markdown("#### **Macro Dynamics**")
            row1_col1, row1_col2 = st.columns(2)"""

rep1 = """            st.markdown("#### **Comprehensive Risk Insights**")
            row1_col1, row1_col2, row1_col3 = st.columns(3)
            row2_col1, row2_col2, row2_col3 = st.columns(3)"""
content = content.replace(target1, rep1)

# 2. Second block replacement (Donut to row1_col3)
target2 = """            st.divider()

            # --- ROW 2: STRATIFICATION & DISTRIBUTION ---
            st.markdown("#### **Stratification & Distribution**")
            row2_col1, row2_col2 = st.columns(2)

            with row2_col1:"""

rep2 = """            with row1_col3:"""
content = content.replace(target2, rep2)

# 3. Third block replacement (Histogram to row2_col1)
target3 = """            with row2_col2:
                with st.container(border=True):
                    # Histogram Density"""
                    
rep3 = """            with row2_col1:
                with st.container(border=True):
                    # Histogram Density"""
content = content.replace(target3, rep3)

# 4. Fourth block replacement (Heatmap to row2_col2)
target4 = """            st.divider()

            # --- ROW 3: INTER-DEPARTMENTAL FLIGHT ---
            st.markdown("#### **Inter-Departmental Flight Patterns**")
            row3_col1, row3_col2 = st.columns(2)

            with row3_col1:"""

rep4 = """            with row2_col2:"""
content = content.replace(target4, rep4)

# 5. Fifth block replacement (Parallel to row2_col3)
target5 = """            with row3_col2:
                with st.container(border=True):
                    # Parallel Categories"""

rep5 = """            with row2_col3:
                with st.container(border=True):
                    # Parallel Categories"""
content = content.replace(target5, rep5)

with open("src/ui/app.py", "w") as f:
    f.write(content)


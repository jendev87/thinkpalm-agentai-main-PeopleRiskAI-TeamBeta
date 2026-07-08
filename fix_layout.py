with open("src/ui/app.py", "r") as f:
    content = f.read()

# Revert to 3 rows of 2 columns
target_cols = """            st.markdown("#### **Comprehensive Risk Insights**")
            row1_col1, row1_col2, row1_col3 = st.columns(3)
            row2_col1, row2_col2, row2_col3 = st.columns(3)"""
rep_cols = """            st.markdown("#### **Comprehensive Risk Insights**")
            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)
            row3_col1, row3_col2 = st.columns(2)"""
content = content.replace(target_cols, rep_cols)

# Reassign column variables
content = content.replace("with row1_col3:", "with row2_col1:")
content = content.replace("with row2_col1:", "with row2_col2:", 1) # Wait, this could conflict.

# Safer manual reassignment of the specific blocks:

with open("src/ui/app.py", "r") as f:
    lines = f.readlines()

new_lines = []
in_heatmap = False
in_parallel = False

for line in lines:
    if "st.markdown(\"#### **Inter-Departmental Flight Patterns**\")" in line:
        new_lines.append(line)
        new_lines.append(line.replace('st.markdown("#### **Inter-Departmental Flight Patterns**")', 'row3_col1, row3_col2 = st.columns(2)'))
        continue
    
    if "# Heatmap: Department vs Role Risk" in line:
        new_lines.append(line.replace('                # Heatmap', '            with row3_col1:\n                with st.container(border=True):\n                    # Heatmap'))
        in_heatmap = True
        continue
    
    if "if y_val:" in line and in_heatmap:
        new_lines.append("                    if y_val:\n")
        continue
        
    if "st.session_state.pending_query =" in line and in_heatmap:
        new_lines.append("                        st.session_state.pending_query = f\"Analyze flight risk in the {y_val} department.\"\n")
        continue
        
    if "st.rerun()" in line and in_heatmap:
        new_lines.append("                        st.rerun()\n")
        in_heatmap = False
        continue

    if "# Parallel Categories" in line:
        new_lines.append(line.replace('                # Parallel', '            with row3_col2:\n                with st.container(border=True):\n                    # Parallel'))
        in_parallel = True
        continue
        
    if "st.plotly_chart(fig_parallel" in line and in_parallel:
        new_lines.append("                    st.plotly_chart(fig_parallel, use_container_width=True)\n")
        in_parallel = False
        continue

    # indenting lines for heatmap block
    if in_heatmap:
        if "heat_agg =" in line or "heat_pivot =" in line or "fig_heat =" in line or "title=" in line or "color_continuous" in line or "template=" in line or "fig_heat.update_layout" in line or "event_heat =" in line or "if event_heat" in line or "pt = " in line or "y_val =" in line:
            new_lines.append("    " + line)
        elif "with st.container(border=True):" in line:
            pass # skip the original one
        else:
            new_lines.append(line)
        continue
        
    if in_parallel:
        if "driver_dept =" in line or "fig_parallel =" in line or "title=" in line or "color_continuous" in line or "template=" in line or "fig_parallel.update_layout" in line:
            new_lines.append("    " + line)
        elif "with st.container(border=True):" in line:
            pass # skip the original one
        else:
            new_lines.append(line)
        continue

    # remove the original with st.container(border=True): that was directly above them
    if "with st.container(border=True):" in line and ("Row 3" in "".join(new_lines[-5:])):
        # Skip the original container wrappers we injected
        # Actually it's safer to just do a direct string replace on the whole file string for precision.
        pass


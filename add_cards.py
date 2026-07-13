import sys

def indent_block(text, spaces=4):
    return "\n".join((" " * spaces + line) if line.strip() else line for line in text.split("\n"))

with open('src/ui/app.py', 'r') as f:
    content = f.read()

css = """/* Beautiful Cards for Dashboard Components */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(30, 41, 59, 0.45) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3) !important;
    backdrop-filter: blur(8px) !important;
    padding: 16px !important;
}

/* Sticky Right Column (ChatGPT Style) */"""
content = content.replace("/* Sticky Right Column (ChatGPT Style) */", css)

# 1. Area Chart
area_target = """                # Area Chart: Risk Progression by Tenure Band
                tenure_agg = df.groupby('Tenure', as_index=False)['RiskPercentage'].mean()
                fig_area = px.area(tenure_agg, x='Tenure', y='RiskPercentage', 
                                   title='Risk Progression by Tenure', 
                                   color_discrete_sequence=['#FF3366'],
                                   template='plotly_dark')
                fig_area.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_area, use_container_width=True)"""
area_rep = "                with st.container(border=True):\n" + indent_block(area_target, 4)
content = content.replace(area_target, area_rep)

# 2. Line Chart
line_target = """                # Line Chart: Average Risk vs Monthly Hours
                hours_agg = df.groupby('MonthlyHours', as_index=False)['RiskPercentage'].mean()
                fig_line = px.line(hours_agg, x='MonthlyHours', y='RiskPercentage', 
                                   title='Avg Risk Trend vs Monthly Hours',
                                   color_discrete_sequence=['#38BDF8'],
                                   template='plotly_dark')
                fig_line.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_line, use_container_width=True)"""
line_rep = "                with st.container(border=True):\n" + indent_block(line_target, 4)
content = content.replace(line_target, line_rep)

# 3. Donut
donut_target = """                # Donut Chart
                strat_counts = df['RiskStratification'].value_counts().reset_index()
                strat_counts.columns = ['Risk Level', 'Count']
                fig_donut = px.pie(strat_counts, values='Count', names='Risk Level', 
                                   title='Workforce Risk Distribution', hole=0.6,
                                   color='Risk Level',
                                   color_discrete_map={'Low':'#10B981', 'Medium':'#FBBF24', 'High':'#F97316', 'Critical':'#EF4444'},
                                   template='plotly_dark')
                fig_donut.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                event_donut = st.plotly_chart(fig_donut, use_container_width=True, on_select="rerun")
                if event_donut and len(event_donut.get("selection", {}).get("points", [])) > 0:
                    pt = event_donut["selection"]["points"][0]
                    label = pt.get("label") or pt.get("point_label") or pt.get("pointNumber")
                    # Using pointNumber to look up from strat_counts if label is missing
                    if label is None and isinstance(pt.get("pointNumber"), int):
                        label = strat_counts.iloc[pt["pointNumber"]]['Risk Level']
                    if label:
                        st.session_state.pending_query = f"Summarize the employees in the {label} risk tier."
                        st.rerun()"""
donut_rep = "                with st.container(border=True):\n" + indent_block(donut_target, 4)
content = content.replace(donut_target, donut_rep)

# 4. Hist
hist_target = """                # Histogram Density
                fig_hist = px.histogram(df, x='RiskPercentage', nbins=30, 
                                        title='Risk Score Distribution Density',
                                        marginal='box',
                                        color_discrete_sequence=['#8B5CF6'],
                                        template='plotly_dark')
                fig_hist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_hist, use_container_width=True)"""
hist_rep = "                with st.container(border=True):\n" + indent_block(hist_target, 4)
content = content.replace(hist_target, hist_rep)

# 5. Heatmap
heat_target = """            # Heatmap: Department vs Role Risk
            heat_agg = df.groupby(['Department', 'Role'], as_index=False)['RiskPercentage'].mean()
            heat_pivot = heat_agg.pivot(index='Department', columns='Role', values='RiskPercentage').fillna(0)
            fig_heat = px.imshow(heat_pivot, text_auto=".1f", aspect="auto", 
                                 title="Department vs. Role Risk Grid",
                                 color_continuous_scale="Reds",
                                 template='plotly_dark')
            fig_heat.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            event_heat = st.plotly_chart(fig_heat, use_container_width=True, on_select="rerun")
            if event_heat and len(event_heat.get("selection", {}).get("points", [])) > 0:
                pt = event_heat["selection"]["points"][0]
                y_val = pt.get("y")  # Department
                if y_val:
                    st.session_state.pending_query = f"Analyze flight risk in the {y_val} department."
                    st.rerun()"""
heat_rep = "            with st.container(border=True):\n" + indent_block(heat_target, 4)
content = content.replace(heat_target, heat_rep)

# 6. Parallel
par_target = """            # Parallel Categories (Flow breakdown) for Top Driver to Department
            driver_dept = df[['Driver1', 'Department']].dropna()
            fig_parallel = px.parallel_categories(driver_dept, dimensions=['Driver1', 'Department'],
                                                  title="Top Driver Cascade to Business Unit",
                                                  color_continuous_scale="Reds",
                                                  template='plotly_dark')
            fig_parallel.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_parallel, use_container_width=True)"""
par_rep = "            with st.container(border=True):\n" + indent_block(par_target, 4)
content = content.replace(par_target, par_rep)

# 7. Top Drivers bar
bar_target = """            fig = px.bar(driver_counts.head(10), x='Count', y='Driver', orientation='h', 
                         color='Count', color_continuous_scale="Reds")
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=30, b=0), height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', template='plotly_dark')
            event_drivers = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
            if event_drivers and len(event_drivers.get("selection", {}).get("points", [])) > 0:
                pt = event_drivers["selection"]["points"][0]
                driver = pt.get("y")
                if driver:
                    st.session_state.pending_query = f"Why is {driver} a top attrition driver?"
                    st.rerun()"""
bar_rep = "            with st.container(border=True):\n" + indent_block(bar_target, 4)
content = content.replace(bar_target, bar_rep)

# 8. Roster
roster_target = "            st.dataframe(df[df['RiskPercentage'] > 75].sort_values('RiskPercentage', ascending=False).head(10), use_container_width=True, height=400)"
roster_rep = "            with st.container(border=True):\n                st.dataframe(df[df['RiskPercentage'] > 75].sort_values('RiskPercentage', ascending=False).head(10), use_container_width=True, height=400)"
content = content.replace(roster_target, roster_rep)

# 9. Exec Summary
exec_target = "            st.dataframe(macro_metrics, use_container_width=True)"
exec_rep = "            with st.container(border=True):\n                st.dataframe(macro_metrics, use_container_width=True)"
content = content.replace(exec_target, exec_rep)

with open('src/ui/app.py', 'w') as f:
    f.write(content)


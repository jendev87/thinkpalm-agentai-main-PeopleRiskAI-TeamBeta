with open("src/ui/app.py", "r") as f:
    content = f.read()

# Add height=300 to all the charts in the 2x3 grid
content = content.replace("fig_area.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')", 
                          "fig_area.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')")

content = content.replace("fig_line.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')", 
                          "fig_line.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')")

content = content.replace("fig_donut.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')", 
                          "fig_donut.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')")

content = content.replace("fig_hist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')", 
                          "fig_hist.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')")

content = content.replace("fig_heat.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')", 
                          "fig_heat.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')")

content = content.replace("fig_parallel.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')", 
                          "fig_parallel.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')")

# Also let's fix the margins so they don't look cramped
content = content.replace("height=300,", "height=300, margin=dict(l=20, r=20, t=40, b=20),")

with open("src/ui/app.py", "w") as f:
    f.write(content)


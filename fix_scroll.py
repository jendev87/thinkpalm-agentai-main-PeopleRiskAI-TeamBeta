with open("src/ui/app.py", "r") as f:
    content = f.read()

# Remove fixed height from python containers
content = content.replace("with st.container(height=820, border=False):", "with st.container(border=False):")

# Fix the CSS block
target_css = """/* Sticky Right Column (ChatGPT Style) */
div[data-testid="column"]:nth-of-type(2) {
    position: sticky !important;
    top: 40px !important;
    height: calc(100vh - 40px) !important;
    overflow-y: hidden !important;
}"""

replacement_css = """/* Responsive Scrollable Columns */
div[data-testid="column"]:nth-of-type(1), div[data-testid="column"]:nth-of-type(2) {
    height: calc(100vh - 40px) !important;
    overflow-y: auto !important;
    /* Hide scrollbar for clean look */
    scrollbar-width: none; 
    -ms-overflow-style: none;
}
div[data-testid="column"]::-webkit-scrollbar {
    display: none;
}"""

content = content.replace(target_css, replacement_css)

with open("src/ui/app.py", "w") as f:
    f.write(content)


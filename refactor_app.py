import re

with open("src/ui/app.py", "r") as f:
    content = f.read()

# I will write a script that breaks the file down into parts and reassembles it.
# Let's first split the file at `# ==========================================\n# MAIN LAYOUT`
parts = content.split("# ==========================================\n# MAIN LAYOUT\n# ==========================================")
if len(parts) < 2:
    print("Could not find MAIN LAYOUT marker.")
    exit(1)

pre_layout = parts[0]
layout = parts[1]

# Now, split the layout into the 3 columns
# --- PANEL 1: Navigation ---
nav_split = layout.split("# --- PANEL 1: Navigation ---")
dash_split = nav_split[1].split("# --- PANEL 2: Interactive Dashboard ---")
chat_split = dash_split[1].split("# --- PANEL 3: Conversation Copilot ---")

nav_content = dash_split[0]
dash_content = chat_split[0]
chat_content = chat_split[1]

# We need to unindent these contents by 4 spaces because they are currently under `with col_XXX:`
def unindent(text, spaces=4):
    lines = text.split('\n')
    unindented = []
    for line in lines:
        if line.startswith(' ' * spaces):
            unindented.append(line[spaces:])
        else:
            unindented.append(line)
    return '\n'.join(unindented)

nav_content_clean = unindent(nav_content.strip())
dash_content_clean = unindent(dash_content.strip())
chat_content_clean = unindent(chat_content.strip())

# Inside dashboard, we have sections for Risk Overview, Top Drivers, etc.
# But it's easier to just keep them as they are and wrap the whole dash_content in `render_dashboard(df, slack_url, smtp_host, smtp_port, smtp_user, smtp_pass, target_email)`
# Actually, the user specifically requested: render_risk_overview(), render_top_drivers(), etc.
# We must split dash_content_clean further.


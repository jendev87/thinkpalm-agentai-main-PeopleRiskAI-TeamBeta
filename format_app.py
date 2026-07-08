import sys

def modify_app(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    out_lines = []
    in_dash = False
    in_chat = False
    dash_indent = 0
    chat_indent = 0

    for i, line in enumerate(lines):
        if line.strip() == "with col_dash:":
            out_lines.append(line)
            dash_indent = len(line) - len(line.lstrip())
            out_lines.append(" " * dash_indent + "    with st.container(height=820, border=False):\n")
            in_dash = True
            continue
            
        if line.strip() == "with col_chat:":
            in_dash = False
            out_lines.append(line)
            chat_indent = len(line) - len(line.lstrip())
            out_lines.append(" " * chat_indent + "    with st.container(height=820, border=False):\n")
            in_chat = True
            continue

        if in_dash:
            # indent by 4 spaces
            if line.strip() == "":
                out_lines.append("\n")
            else:
                out_lines.append("    " + line)
        elif in_chat:
            if line.strip() == "":
                out_lines.append("\n")
            else:
                out_lines.append("    " + line)
        else:
            out_lines.append(line)

    with open(filepath, 'w') as f:
        f.writelines(out_lines)

modify_app("src/ui/app.py")

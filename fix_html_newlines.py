with open("src/ui/app.py", "r") as f:
    content = f.read()

content = content.replace("""                padding: 22px 24px;
                
                
                transition: transform 0.2s ease-in-out;""",
"""                padding: 22px 24px;
                transition: transform 0.2s ease-in-out;""")

content = content.replace("""                padding: 22px 24px;
                
                
            ">""",
"""                padding: 22px 24px;
            ">""")

content = content.replace("""                padding: 24px;
                
                
                text-align: center;
                margin-top: 20px;""",
"""                padding: 24px;
                text-align: center;
                margin-top: 20px;""")

with open("src/ui/app.py", "w") as f:
    f.write(content)

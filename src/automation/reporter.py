from docx import Document
from io import BytesIO
from datetime import datetime


def _html_to_pdf(html_content: str) -> bytes:
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as exc:
        raise RuntimeError(
            "PDF generation requires WeasyPrint's native GTK libraries, which are not "
            "installed on this system. Install the GTK3 runtime for Windows, then retry. "
            "See https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows"
        ) from exc
    return HTML(string=html_content).write_pdf()

def create_mitigation_docx(narrative: str) -> bytes:
    doc = Document()
    doc.add_heading('ThinkPalm PeopleRisk AI', 0)
    doc.add_heading('Manager Mitigation Action Plan', level=1)
    doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_heading('Recommended Action Narrative', level=2)
    doc.add_paragraph(narrative)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def create_mitigation_pdf(narrative: str) -> bytes:
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Mitigation Report</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #333;
                line-height: 1.6;
                padding: 40px;
            }}
            h1 {{
                color: #FF3366;
                border-bottom: 2px solid #FF3366;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #1C2130;
                margin-top: 30px;
            }}
            .timestamp {{
                color: #888;
                font-size: 0.9em;
                margin-bottom: 30px;
            }}
            .content {{
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 5px;
                border-left: 4px solid #FF3366;
                white-space: pre-wrap;
            }}
        </style>
    </head>
    <body>
        <h1>ThinkPalm PeopleRisk AI</h1>
        <h2>Manager Mitigation Action Plan</h2>
        <div class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <h2>Recommended Action Narrative</h2>
        <div class="content">{narrative}</div>
    </body>
    </html>
    """
    
    return _html_to_pdf(html_content)

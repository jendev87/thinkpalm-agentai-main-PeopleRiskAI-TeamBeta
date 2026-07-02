import pandas as pd
from datetime import datetime
from weasyprint import HTML

def generate_executive_pdf(metrics_df: pd.DataFrame, inference_text: str) -> bytes:
    """
    Generates a polished HTML-to-PDF Executive Report containing department-level metrics.
    """
    
    # Convert metrics_df to HTML table
    table_html = metrics_df.to_html(classes="styled-table", index=False)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Executive Summary Report</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #E2E8F0;
                background-color: #0E1117;
                line-height: 1.6;
                padding: 40px;
            }}
            h1 {{
                color: #FF3366;
                border-bottom: 2px solid #FF3366;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #FF3366;
                margin-top: 30px;
            }}
            .timestamp {{
                color: #888;
                font-size: 0.9em;
                margin-bottom: 30px;
            }}
            .inference-box {{
                background-color: #1C2130;
                padding: 20px;
                border-radius: 5px;
                border-left: 4px solid #FF3366;
                white-space: pre-wrap;
                margin-bottom: 40px;
            }}
            .styled-table {{
                border-collapse: collapse;
                margin: 25px 0;
                font-size: 0.9em;
                font-family: sans-serif;
                min-width: 400px;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
                width: 100%;
                color: #000;
                background-color: #ffffff;
            }}
            .styled-table thead tr {{
                background-color: #FF3366;
                color: #ffffff;
                text-align: left;
            }}
            .styled-table th, .styled-table td {{
                padding: 12px 15px;
            }}
            .styled-table tbody tr {{
                border-bottom: 1px solid #dddddd;
            }}
            .styled-table tbody tr:nth-of-type(even) {{
                background-color: #f3f3f3;
            }}
        </style>
    </head>
    <body>
        <h1>ThinkPalm PeopleRisk AI</h1>
        <h2>Executive Summary Report</h2>
        <div class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="inference-box">
            <strong>Executive Inference:</strong><br><br>
            {inference_text}
        </div>
        
        <h2>Departmental Macro Metrics</h2>
        {table_html}
    </body>
    </html>
    """
    
    # Weasyprint generation
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes

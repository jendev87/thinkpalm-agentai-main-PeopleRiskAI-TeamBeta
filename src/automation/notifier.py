import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_manager_email(target_email: str, subject: str, body: str, attachment_bytes: bytes, filename: str, smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str):
    """
    Sends an email to a manager. Uses simulated execution if missing valid host configurations.
    """
    if not smtp_host or smtp_host == "smtp.example.com":
        print(f"[SIMULATION] Email would be sent to {target_email} with subject: {subject}")
        return True
        
    target_email = target_email.replace('\xa0', '').strip() if target_email else target_email
    smtp_host = smtp_host.replace('\xa0', '').strip() if smtp_host else smtp_host
    smtp_user = smtp_user.replace('\xa0', '').strip() if smtp_user else smtp_user
    smtp_pass = smtp_pass.replace('\xa0', '').replace(' ', '').strip() if smtp_pass else smtp_pass

        
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = target_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    if attachment_bytes:
        part = MIMEApplication(attachment_bytes, Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        msg.attach(part)

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed to send email: {e}")
        return False

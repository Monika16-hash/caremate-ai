import os, smtplib
from email.message import EmailMessage

def send_email(to, subject, body):
    if not os.getenv("SMTP_USER"):
        print(f"[email skipped] {to}: {subject}"); return False
    msg = EmailMessage(); msg["From"] = os.environ["SMTP_USER"]; msg["To"] = to; msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", 587))) as s:
        s.starttls(); s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"]); s.send_message(msg)
    return True

def send_whatsapp(to_number, body):
    """Twilio WhatsApp layer. Enable by setting TWILIO_SID / TWILIO_TOKEN (pip install twilio)."""
    if not os.getenv("TWILIO_SID"):
        print(f"[whatsapp skipped] {to_number}"); return False
    from twilio.rest import Client
    Client(os.environ["TWILIO_SID"], os.environ["TWILIO_TOKEN"]).messages.create(
        from_=os.environ["TWILIO_WHATSAPP_FROM"], to=f"whatsapp:{to_number}", body=body)
    return True

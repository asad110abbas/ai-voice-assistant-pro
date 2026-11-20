import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")


def send_assignment_email(agent_email: str, ticket_id: int, issue: str) -> None:
    """Send ticket assignment notification email."""
    if not SMTP_USER or not SMTP_PASS:
        return

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = agent_email
    msg["Subject"] = f"Briha Support: Ticket #{ticket_id} Assigned to You"

    body = f"""
You have been assigned a new support ticket.

Ticket ID: #{ticket_id}
Issue Summary: {issue}

Please log in to the Briha Voice Dashboard to view and resolve this ticket.

Thank you,
Briha Support System
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        print(f"Email send error: {e}")

# save as: send_email_variant4.py
from email.message import EmailMessage
import smtplib
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env (SMTP_* and REPORT_RECIPIENTS)
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

RECIPIENTS = [
    r.strip()
    for r in os.getenv("REPORT_RECIPIENTS", "").split(",")
    if r.strip()
]

HTML_PATH = Path(
    "/home/moshe/Documents/GitHub/SHM_SA_reporter/scr/reporting/email_variant_4.html"
)


def send_html_variant4():
    if not RECIPIENTS:
        raise ValueError("REPORT_RECIPIENTS is empty or not set in .env")

    if not HTML_PATH.exists():
        raise FileNotFoundError(f"HTML file not found: {HTML_PATH}")

    # Load HTML from file
    html_body = HTML_PATH.read_text(encoding="utf-8")

    msg = EmailMessage()
    msg["Subject"] = "SHM_SA_reporter – HTML variant 4 preview"
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(RECIPIENTS)

    # Plain text fallback
    msg.set_content(
        "Your email client does not support HTML view.\n"
        "Please enable HTML or use a different client."
    )

    # HTML body
    msg.add_alternative(html_body, subtype="html")

    # Send via SSL
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)

    print(f"HTML email (variant 4) sent to: {', '.join(RECIPIENTS)}")


if __name__ == "__main__":
    send_html_variant4()

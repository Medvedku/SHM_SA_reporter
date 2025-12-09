import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Recipients (comma-separated list in .env)
RECIPIENTS = [
    r.strip()
    for r in os.getenv("REPORT_RECIPIENTS", "").split(",")
    if r.strip()
]


def send_report(pdf_path: str):
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"Report file not found: {pdf_path}")

    msg = EmailMessage()
    msg["Subject"] = f"Weekly SHM Report – {pdf_path.stem}"
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(RECIPIENTS)

    msg.set_content(
        f"Hello,\n\n"
        f"The weekly SHM report is attached.\n"
        f"Report file: {pdf_path.name}\n\n"
        f"Best regards,\nSHM_SA_reporter"
    )

    # Attach PDF
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    msg.add_attachment(
        pdf_data,
        maintype="application",
        subtype="pdf",
        filename=pdf_path.name
    )

    # SMTP SSL connection
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)

    print(f"Report sent to: {', '.join(RECIPIENTS)}")

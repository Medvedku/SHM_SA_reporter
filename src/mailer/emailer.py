import argparse
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

RECIPIENTS = [r.strip() for r in os.getenv("REPORT_RECIPIENTS_PRJ16", "").split(",") if r.strip()]


def send_email(year, week):
    if not RECIPIENTS:
        print("Error: REPORT_RECIPIENTS is empty or not set in .env")
        return

    # Construct file path
    # Assuming this script is in src/mailer/ where email files are also generated
    base_dir = Path(__file__).parent.absolute()
    html_filename = f"email_{year}W{int(week):02d}.html"
    html_path = base_dir / html_filename

    if not html_path.exists():
        print(f"Error: HTML file not found: {html_path}")
        return

    # Load HTML from file
    try:
        html_body = html_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return

    msg = EmailMessage()
    msg["Subject"] = f"PRJ-16 Report - {year} Week {week}"
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(RECIPIENTS)

    # Plain text fallback
    msg.set_content(
        f"SHM Report for {year} Week {week}.\n"
        "Your email client does not support HTML view.\n"
        "Please enable HTML or use a different client."
    )

    # HTML body
    msg.add_alternative(html_body, subtype="html")

    # Send via SSL
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        print(f"Email sent successfully to: {', '.join(RECIPIENTS)}")

        # Cleanup is now handled by src/storage/cleaner.py

    except Exception as e:
        print(f"Failed to send email: {e}")


def main():
    parser = argparse.ArgumentParser(description="Send weekly report email.")
    parser.add_argument("--year", required=True, help="Year of the report (e.g., 2025)")
    parser.add_argument("--week", required=True, help="Week number (e.g., 50)")

    args = parser.parse_args()

    send_email(args.year, args.week)


if __name__ == "__main__":
    main()

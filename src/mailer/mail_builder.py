import argparse
import os
import logging
from datetime import date

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_week_dates(year, week):
    # Match logic from report_builder_v2.py
    monday = date.fromisocalendar(year, week, 1)
    sunday = date.fromisocalendar(year, week, 7)
    fmt = "%d. %B %Y"
    return monday.strftime(fmt), sunday.strftime(fmt)


def build_mail(year, week, start_date_arg, end_date_arg):
    """
    Reads the email template and generates a new email file with the provided details.
    """
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "email_template.html")
    output_filename = f"email_{year}W{int(week):02d}.html"
    output_path = os.path.join(base_dir, output_filename)

    # Check if template exists
    if not os.path.exists(template_path):
        logger.error(f"Template file not found at {template_path}")
        return

    # Read the template
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    except Exception as e:
        logger.error(f"Error reading template: {e}")
        return

    # Recalculate dates to match Report format (DD. Month YYYY)
    # This ignores the passed start/end args for the *content*, ensuring consistency with report
    display_start, display_end = get_week_dates(int(year), int(week))

    # Replace placeholders
    # The template uses {year}, {week}, {date_from}, {date_to}
    try:
        filled_content = template_content.format(year=year, week=week, date_from=display_start, date_to=display_end)
    except KeyError as e:
        # Fallback if format fails due to extra braces (like CSS)
        filled_content = (
            template_content.replace("{year}", str(year))
            .replace("{week}", str(week))
            .replace("{date_from}", str(display_start))
            .replace("{date_to}", str(display_end))
        )

    # Write the output file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(filled_content)
        logger.info(f"Successfully created email: {output_path}")
    except Exception as e:
        logger.error(f"Error writing output file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Generate weekly report email from template.")

    parser.add_argument("--year", required=True, help="Year of the report (e.g., 2025)")
    parser.add_argument("--week", required=True, help="Week number (e.g., 50)")
    parser.add_argument("--start", required=True, help="Start date (e.g., 2025-12-08)")
    parser.add_argument("--end", required=True, help="End date (e.g., 2025-12-14)")

    args = parser.parse_args()

    build_mail(args.year, args.week, args.start, args.end)


if __name__ == "__main__":
    main()

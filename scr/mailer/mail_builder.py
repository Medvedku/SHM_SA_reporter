import argparse
import os

def build_mail(year, week, start_date, end_date):
    """
    Reads the email template and generates a new email file with the provided details.
    """
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, 'email_template.html')
    output_filename = f"email_{year}W{week}.html"
    output_path = os.path.join(base_dir, output_filename)

    # Check if template exists
    if not os.path.exists(template_path):
        print(f"Error: Template file not found at {template_path}")
        return

    # Read the template
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        print(f"Error reading template: {e}")
        return

    # Replace placeholders
    # The template uses {year}, {week}, {date_from}, {date_to}
    try:
        filled_content = template_content.format(
            year=year,
            week=week,
            date_from=start_date,
            date_to=end_date
        )
    except KeyError as e:
        print(f"Error: Missing placeholder in template - {e}")
        # Fallback to safe replace if format fails due to extra braces (like CSS)
        # However, HTML often contains braces in CSS/JS.
        # Let's use a safer replacement strategy if .format() is risky for HTML with CSS.
        filled_content = template_content.replace('{year}', str(year)) \
                                         .replace('{week}', str(week)) \
                                         .replace('{date_from}', str(start_date)) \
                                         .replace('{date_to}', str(end_date))

    # Write the output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(filled_content)
        print(f"Successfully created email: {output_path}")
    except Exception as e:
        print(f"Error writing output file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate weekly report email from template.")
    
    parser.add_argument('--year', required=True, help="Year of the report (e.g., 2025)")
    parser.add_argument('--week', required=True, help="Week number (e.g., 50)")
    parser.add_argument('--start', required=True, help="Start date (e.g., 2025-12-08)")
    parser.add_argument('--end', required=True, help="End date (e.g., 2025-12-14)")

    args = parser.parse_args()

    build_mail(args.year, args.week, args.start, args.end)

if __name__ == "__main__":
    main()

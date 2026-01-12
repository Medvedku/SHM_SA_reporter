
import subprocess
import sys
import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --- Configuration ---
# 1. parqueter
# 2. plotter
# 3. reporter
# 4. uploader_parquets
# 5. uploader_report
# 6. mail_builder
# 7. emailer
# 8. cleaner

def get_iso_week_boundaries(year=None, week=None):
    """
    Computes ISO week start (Monday) and end (next Monday).
    Defaults to the *previous* week if year/week not specified.
    Returns: year, week, start_date_str, end_date_str
    """
    now_utc = datetime.now(timezone.utc)
    iso_year, iso_week, _ = now_utc.isocalendar()

    if year is None or week is None:
        # Default to previous week
        year = iso_year
        week = iso_week - 1
        
        # Handle year rollover (if week 1 becomes week 0, go to last week of prev year)
        if week <= 0:
            year -= 1
            # ISO weeks in a year (either 52 or 53)
            # Simplest way: get date and ask for isocalendar
            # Dec 28th is alway in the last week of its year
            last_week_curr_year = datetime(year, 12, 28).isocalendar()[1]
            week = last_week_curr_year

    # Calculate start date (Monday of that week)
    # Using fromisocalendar: year, week, 1 (Monday)
    start_dt = datetime.fromisocalendar(year, week, 1).replace(tzinfo=timezone.utc)
    # End date (Next Monday)
    end_dt = start_dt + timedelta(days=7)
    
    # Format for arguments (YYYY-MM-DD)
    # Note: mail_builder might expect just the date part
    return year, week, start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")

def run_command(cmd, description):
    print(f"\n🚀 Starting: {description}")
    print(f"   Command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Finished: {description}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error in step: {description}")
        print(f"   Exit code: {e.returncode}")
        sys.exit(e.returncode)

def main():
    parser = argparse.ArgumentParser(description="Master pipeline for SHM Reporting")
    parser.add_argument("--year", type=int, help="Force specific year")
    parser.add_argument("--week", type=int, help="Force specific week")
    parser.add_argument("--skip-cleaned", action="store_true", help="Skip cleanup step")
    args = parser.parse_args()

    # 1. Determine Timeframe
    year, week, start_date, end_date = get_iso_week_boundaries(args.year, args.week)
    
    print("="*60)
    print(f"SHM REPORTER PIPELINE")
    print(f"Target: Year {year}, Week {week:02d}")
    print(f"Range:  {start_date} -> {end_date}")
    print("="*60)

    base_dir = Path(__file__).parent.resolve()
    python_exe = sys.executable

    # Define scripts
    script_parqueter = base_dir / "processing/run_parqueter.py"
    script_plotter   = base_dir / "plotting/run_plotter_v2.py"
    script_reporter  = base_dir / "report_build/report_builder_v2.py"
    script_up_parq   = base_dir / "storage/uploader_parquets.py"
    script_up_rep    = base_dir / "storage/uploader_report.py"
    script_mail_bld  = base_dir / "mailer/mail_builder.py"
    script_emailer   = base_dir / "mailer/emailer.py"
    script_cleaner   = base_dir / "storage/cleaner.py"

    # 2. Run Parqueter
    # python3 src/processing/run_parqueter.py --year Y --week W
    run_command([python_exe, str(script_parqueter), "--year", str(year), "--week", str(week)], "Parquet Processing")

    # 3. Run Plotter
    # python3 src/plotting/run_plotter_v2.py
    # (Plotter detects time from data, no args needed)
    run_command([python_exe, str(script_plotter)], "Plot Generation")

    # 4. Run Report Builder
    # python3 src/report_build/report_builder_v2.py --year Y --week W
    run_command([python_exe, str(script_reporter), "--year", str(year), "--week", str(week)], "Report Building")

    # 5. Upload Parquets
    # python3 src/storage/uploader_parquets.py
    run_command([python_exe, str(script_up_parq)], "Uploading Parquets")

    # 6. Upload Report
    # python3 src/storage/uploader_report.py
    run_command([python_exe, str(script_up_rep)], "Uploading Report")

    # 7. Build Email
    # python3 src/mailer/mail_builder.py --year Y --week W --start S --end E
    run_command([
        python_exe, str(script_mail_bld), 
        "--year", str(year), 
        "--week", str(week),
        "--start", start_date,
        "--end", end_date
    ], "Email Builder")

    # 8. Send Email
    # python3 src/mailer/emailer.py --year Y --week W
    run_command([python_exe, str(script_emailer), "--year", str(year), "--week", str(week)], "Sending Email")

    # 9. Cleaner
    if not args.skip_cleaned:
        run_command([python_exe, str(script_cleaner)], "Cleanup")
    else:
        print("\n⚠ Skipping cleanup as requested.")

    print("\n🎉 PIPELINE COMPLETED SUCCESSFULLY 🎉")

if __name__ == "__main__":
    main()

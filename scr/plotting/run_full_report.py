#!/usr/bin/env python3
"""Runner script: generate plots, build report, then clean plots.

This script executes `plotter.py` (which prompts for END date), then
`reporter.py` to create the PDF, and finally deletes the generated
figure files from the project's `plots` directory.

Usage:
  python3 scr/plotting/run_full_report.py --end-date 2025-11-23 --yes

If `--end-date` is not provided the script will prompt interactively.
Pass `--yes` to avoid a deletion confirmation prompt.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLOTS_DIR = PROJECT_ROOT / "plots"
PLOTTER_SCRIPT = PROJECT_ROOT / "scr" / "plotting" / "plotter.py"
REPORTER_SCRIPT = PROJECT_ROOT / "scr" / "plotting" / "reporter.py"


def iso_week_range_from_end(end_date_str: str) -> tuple[str, str]:
    """Return (start_date_str, end_date_str) for the ISO week containing end_date_str.

    Dates returned as ISO 'YYYY-MM-DD' strings where start_date is Monday and end_date is Sunday.
    """
    from datetime import datetime, timedelta

    end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    iso_year, iso_week, weekday = end_dt.isocalendar()
    # weekday: Monday=1 .. Sunday=7
    start_date = end_dt - timedelta(days=weekday - 1)
    end_of_week = start_date + timedelta(days=6)
    return start_date.isoformat(), end_of_week.isoformat()


def run_plotter(start_date: str | None, end_date: str | None) -> None:
    """Run the `plotter.py` script and pass start/end dates as CLI args when provided."""
    cmd = [sys.executable, str(PLOTTER_SCRIPT)]
    if start_date:
        cmd += ["--start-date", start_date]
    if end_date:
        cmd += ["--end-date", end_date]

    print(f"Running plotter: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def run_reporter(end_date: str | None) -> None:
    """Run the `reporter.py` script to build the PDF report.

    If `end_date` is provided, pass it as `--end-date` to `reporter.py`.
    """
    cmd = [sys.executable, str(REPORTER_SCRIPT)]
    if end_date:
        cmd += ["--end-date", end_date]

    print("Running reporter to generate PDF...")
    subprocess.run(cmd, check=True)


def generated_plot_paths() -> List[Path]:
    """Return a list of expected plot file paths that reporter consumes.

    This matches the filenames referenced in `reporter.py`.
    """
    paths: List[Path] = []

    # Alternating FFT + daily grid for A30..A35
    for num in range(30, 36):
        paths.append(PLOTS_DIR / f"A{num}_fft_kde.png")
        paths.append(PLOTS_DIR / f"A{num}_daily_v_grid.png")

    # Strain-temperature plots S7..S29
    for num in range(7, 30):
        paths.append(PLOTS_DIR / f"S{num}_strain_temp.png")

    # Temperatures
    paths.append(PLOTS_DIR / "temps_arch.png")
    paths.append(PLOTS_DIR / "temps_col.png")

    return paths


def clean_plots(confirm: bool) -> int:
    """Delete generated plot files. Returns number of deleted files."""
    files = generated_plot_paths()
    existing = [p for p in files if p.exists()]

    if not existing:
        print("No generated plot files found to delete.")
        return 0

    print(f"Found {len(existing)} files to delete in {PLOTS_DIR}")

    if not confirm:
        ans = input("Delete these files? [y/N]: ").strip().lower()
        if ans not in ("y", "yes"):
            print("Aborting deletion.")
            return 0

    deleted = 0
    for p in existing:
        try:
            p.unlink()
            deleted += 1
            print(f"Deleted: {p.name}")
        except Exception as e:
            print(f"Failed to delete {p}: {e}")

    print(f"Deleted {deleted} files.")
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate plots, create report, then clean plots.")
    parser.add_argument("--end-date", help="END date (YYYY-MM-DD) to provide to plotter.py", default=None)
    parser.add_argument("--yes", help="Assume yes for deletion prompts", action="store_true")

    args = parser.parse_args()

    # If user provided an end date, compute ISO-week start/end and pass those to plotter.
    start_date = None
    end_date = None
    if args.end_date:
        # compute ISO-week Monday..Sunday for the provided end date
        start_date, end_date = iso_week_range_from_end(args.end_date)

    # 1) Run plotter (may prompt if dates not provided)
    try:
        run_plotter(start_date, end_date)
    except subprocess.CalledProcessError as e:
        print(f"plotter.py failed with exit code {e.returncode}")
        sys.exit(e.returncode)

    # 2) Run reporter
    try:
        run_reporter(args.end_date)
    except subprocess.CalledProcessError as e:
        print(f"reporter.py failed with exit code {e.returncode}")
        sys.exit(e.returncode)

    # 3) Clean up generated plot images
    clean_plots(confirm=args.yes)


if __name__ == "__main__":
    main()

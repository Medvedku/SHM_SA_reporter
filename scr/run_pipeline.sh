#!/bin/bash

# SHM Reporter Pipeline - Bash Version
# Master pipeline for SHM Reporting
# Orchestrates: parqueter -> plotter -> reporter -> uploaders -> emailer -> cleaner

set -e  # Exit on error

# --- Configuration ---
# Pipeline steps:
# 1. parqueter
# 2. plotter
# 3. reporter
# 4. uploader_parquets
# 5. uploader_report
# 6. mail_builder
# 7. emailer
# 8. cleaner

# --- Helper Functions ---

print_separator() {
    echo "============================================================"
}

run_command() {
    local description="$1"
    shift
    local cmd=("$@")
    
    echo ""
    echo "🚀 Starting: $description"
    echo "   Command: ${cmd[*]}"
    
    if "${cmd[@]}"; then
        echo "✅ Finished: $description"
    else
        local exit_code=$?
        echo ""
        echo "❌ Error in step: $description"
        echo "   Exit code: $exit_code"
        exit $exit_code
    fi
}

get_iso_week_boundaries() {
    local year="$1"
    local week="$2"
    
    # If year or week not specified, use previous week
    if [ -z "$year" ] || [ -z "$week" ]; then
        # Get current ISO year and week
        local iso_year=$(date -u +"%G")
        local iso_week=$(date -u +"%V")
        
        year=$iso_year
        week=$((iso_week - 1))
        
        # Handle year rollover (when current week is 1, previous week is in previous year)
        if [ $week -le 0 ]; then
            year=$((year - 1))
            # Get last week of previous year (usually 52 or 53)
            # December 28th is always in the last week of the year per ISO 8601
            local last_week=$(date -d "${year}-12-28" +"%V" 2>/dev/null)
            if [ $? -ne 0 ] || [ -z "$last_week" ]; then
                # Fallback: most years have 52 weeks, some have 53
                last_week=52
            fi
            week=$last_week
        fi
    fi
    
    # Calculate start date (Monday of that week) using Python for reliability
    # This is more reliable than complex date arithmetic across different systems
    local start_date
    start_date=$(python3 -c "from datetime import datetime; print(datetime.fromisocalendar($year, $week, 1).strftime('%Y-%m-%d'))" 2>/dev/null)
    
    # Error handling for Python calculation
    if [ $? -ne 0 ] || [ -z "$start_date" ]; then
        echo "Error: Failed to calculate ISO week boundaries. Python datetime module required." >&2
        exit 1
    fi
    
    # Calculate end date (next Monday, 7 days later)
    local end_date=$(date -d "$start_date + 7 days" +"%Y-%m-%d" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$end_date" ]; then
        # Fallback using Python
        end_date=$(python3 -c "from datetime import datetime, timedelta; d = datetime.strptime('$start_date', '%Y-%m-%d'); print((d + timedelta(days=7)).strftime('%Y-%m-%d'))" 2>/dev/null)
        if [ $? -ne 0 ] || [ -z "$end_date" ]; then
            echo "Error: Failed to calculate end date." >&2
            exit 1
        fi
    fi
    
    echo "$year $week $start_date $end_date"
}

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Master pipeline for SHM Reporting

Options:
    --year YEAR          Force specific year
    --week WEEK          Force specific ISO week number
    --skip-cleaned       Skip cleanup step (keep temporary files)
    -h, --help          Show this help message

Examples:
    $0                              # Run for previous week
    $0 --year 2025 --week 48        # Run for specific week
    $0 --skip-cleaned               # Run without cleanup

EOF
}

# --- Argument Parsing ---
YEAR=""
WEEK=""
SKIP_CLEANED=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --year)
            YEAR="$2"
            shift 2
            ;;
        --week)
            WEEK="$2"
            shift 2
            ;;
        --skip-cleaned)
            SKIP_CLEANED=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# --- Main Pipeline ---

# Determine timeframe
read YEAR WEEK START_DATE END_DATE <<< $(get_iso_week_boundaries "$YEAR" "$WEEK")

print_separator
echo "SHM REPORTER PIPELINE"
echo "Target: Year $YEAR, Week $WEEK"
echo "Range:  $START_DATE -> $END_DATE"
print_separator

# Get base directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXE="${PYTHON_EXE:-python3}"

# Define scripts
SCRIPT_PARQUETER="$SCRIPT_DIR/processing/run_parqueter.py"
SCRIPT_PLOTTER="$SCRIPT_DIR/plotting/run_plotter_v2.py"
SCRIPT_REPORTER="$SCRIPT_DIR/report_build/report_builder_v2.py"
SCRIPT_UP_PARQ="$SCRIPT_DIR/storage/uploader_parquets.py"
SCRIPT_UP_REP="$SCRIPT_DIR/storage/uploader_report.py"
SCRIPT_MAIL_BLD="$SCRIPT_DIR/mailer/mail_builder.py"
SCRIPT_EMAILER="$SCRIPT_DIR/mailer/emailer.py"
SCRIPT_CLEANER="$SCRIPT_DIR/storage/cleaner.py"

# 2. Run Parqueter
run_command "Parquet Processing" \
    "$PYTHON_EXE" "$SCRIPT_PARQUETER" --year "$YEAR" --week "$WEEK"

# 3. Run Plotter
run_command "Plot Generation" \
    "$PYTHON_EXE" "$SCRIPT_PLOTTER"

# 4. Run Report Builder
run_command "Report Building" \
    "$PYTHON_EXE" "$SCRIPT_REPORTER" --year "$YEAR" --week "$WEEK"

# 5. Upload Parquets
run_command "Uploading Parquets" \
    "$PYTHON_EXE" "$SCRIPT_UP_PARQ"

# 6. Upload Report
run_command "Uploading Report" \
    "$PYTHON_EXE" "$SCRIPT_UP_REP"

# 7. Build Email
run_command "Email Builder" \
    "$PYTHON_EXE" "$SCRIPT_MAIL_BLD" --year "$YEAR" --week "$WEEK" --start "$START_DATE" --end "$END_DATE"

# 8. Send Email
run_command "Sending Email" \
    "$PYTHON_EXE" "$SCRIPT_EMAILER" --year "$YEAR" --week "$WEEK"

# 9. Cleaner
if [ "$SKIP_CLEANED" = false ]; then
    run_command "Cleanup" \
        "$PYTHON_EXE" "$SCRIPT_CLEANER"
else
    echo ""
    echo "⚠ Skipping cleanup as requested."
fi

echo ""
echo "🎉 PIPELINE COMPLETED SUCCESSFULLY 🎉"

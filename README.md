# SHM_SA_reporter

Automated data extraction, conversion, analysis, and reporting pipeline for SHM (Structural Health Monitoring).

This project connects to a remote MongoDB, processes sensor data into Parquet/DuckDB, generates visualization plots, builds an HTML report, uploads artifacts to cloud/FTP, and emails stakeholders.

---

## 🚀 How to Run

The entire pipeline can be orchestrated using either a **Bash script** or **Python script**.

### Option 1: Bash Script (Recommended)

The pipeline can be run using the bash scripts:
- **`main.sh`** - Main entry point (at repository root)
- **`scr/run_pipeline.sh`** - Pipeline orchestrator

By default, the script calculates the **previous ISO week** and runs the pipeline for that week.

```bash
# Run for the previous week
./main.sh
# OR
./scr/run_pipeline.sh
```

#### Options

| Argument | Description | Example |
| :--- | :--- | :--- |
| `--year` | Force a specific year | `--year 2025` |
| `--week` | Force a specific ISO week number | `--week 50` |
| `-h, --help` | Show help message | `--help` |

**Example: Reprocessing a specific week:**
```bash
./main.sh --year 2025 --week 48
```

### Option 2: Python Script (Legacy)

You can also use the Python version of the pipeline:

```bash
# Run for the previous week
python3 scr/run_pipeline.py
```

**Example: Reprocessing a specific week:**
```bash
python3 scr/run_pipeline.py --year 2025 --week 48
```

### Option 3: Docker Container

Run the pipeline in a containerized environment:

```bash
# Build the Docker image
docker build -t shm-reporter .

# Run for the previous week
docker run --rm --env-file .env shm-reporter

# Run for a specific week
docker run --rm --env-file .env shm-reporter --year 2025 --week 48
```

### Automatic Scheduling (Cron)

To schedule the report to run automatically (e.g., every Monday at 02:00 AM).

1. Open your crontab:
   ```bash
   crontab -e
   ```
2. Add the line below (adjust paths to your actual environment):
   ```bash
   # Run SHM Reporter every Monday at 2:00 AM (Bash version)
   0 2 * * 1 /home/moshe/Documents/GitHub/SHM_SA_reporter/main.sh >> /home/user/logs/shm_reporter.log 2>&1
   
   # OR use Python version
   0 2 * * 1 /usr/bin/python3 /home/moshe/Documents/GitHub/SHM_SA_reporter/scr/run_pipeline.py >> /home/user/logs/shm_reporter.log 2>&1
   ```

---

## 🔄 Pipeline Workflow

1. **Parqueter** (`run_parqueter.py`)
   - Fetches data from MongoDB for the calculated week.
   - Converts to Parquet format in `data/parquet/`.

2. **Plotter** (`run_plotter_v2.py`)
   - Ingests Parquet files into a temporary DuckDB.
   - Generates Plotly visualizations in `plots/`.

3. **Report Builder** (`report_builder_v2.py`)
   - Embeds plots into a self-contained HTML report.
   - Saves result to `reports/`.

4. **Upload Parquets** (`uploader_parquets.py`)
   - Syncs new Parquet files to Cloudflare R2 bucket.

5. **Upload Report** (`uploader_report.py`)
   - Uploads the HTML report to the configured FTP server.

6. **Emailer** (`mail_builder.py` + `emailer.py`)
   - Generates an HTML email summary.
   - Sends the email to recipients defined in `.env`.

**Note:** For containerized deployments, cleanup of temporary files is handled automatically by the container lifecycle.

---

## 🔧 Configuration

Ensure your `.env` file is set up with:
- MongoDB URI
- R2 Storage Credentials
- FTP Credentials
- SMTP Email Settings

(See `.env.example` if available)

---

## Requirements
This should be enough:\
`pip install pymongo pyarrow duckdb numpy pandas plotly scipy boto3 python-dotenv psutil requests`
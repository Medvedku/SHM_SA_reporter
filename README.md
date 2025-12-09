# SHM_SA_reporter

Automated data extraction, conversion, analysis, and reporting pipeline.

This project connects to a remote MongoDB database, downloads structured JSON
data, converts it to Parquet format, stores processed files in an R2 bucket,
generates analytical figures, creates a weekly report, and sends the report
by email. Temporary files are cleaned up after each cycle.  
The pipeline then sleeps until the next scheduled run.

---

## 🚀 Planned Workflow

1. **Download data**
   - Connect to MongoDB (hosted on Google Cloud)
   - Fetch relevant JSON documents
   - Store temporary JSON file locally

2. **Convert JSON → Parquet**
   - Use efficient columnar data format (Parquet)
   - Enable faster analytics and reduced file size

3. **Upload processed data to cloud**
   - Upload Parquet files to an R2 bucket
   - Handle versioning and cleanup

4. **Generate figures**
   - Use Python (matplotlib / seaborn / plotly) to create visualizations
   - Save plots locally for inclusion in the report

5. **Create automated report**
   - Assemble plots, statistics, and summaries into a PDF/HTML report
   - Include relevant metrics and insights

6. **Send report by email**
   - Deliver generated report to specified recipients
   - Support SMTP + secure authentication

7. **Cleanup**
   - Remove temporary files (JSON, Parquet, images, reports)
   - Ensure minimal disk usage

8. **Sleep until next scheduled cycle**
   - Typically runs weekly
   - All operations should be restart-safe and monitored

---

## 🔧 Technologies & Tools

- **Python 3.x**
- **MongoDB** (Google Cloud)
- **Pandas / PyArrow** for JSON→Parquet
- **Matplotlib / Plotly** for visualizations
- **ReportLab / WeasyPrint** for report creation
- **Cloudflare R2** (S3-compatible object storage)
- **SMTP email** for notifications
- **Cron / systemd timers** (for scheduling on deployment system)

---

## 🏗️ Deployment Targets

Planned deployment environments:

- **Development:** ODROID-C2 (microSD), Linux environment  
- **Production (future):** ODROID with SSD *or* VPS (Hetzner / DigitalOcean)

Each weekly cycle should run reliably for years with proper monitoring,
logging, and exception handling.

---

## 📦 Project Structure (to be expanded)
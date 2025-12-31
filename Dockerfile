FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (based on README dependencies)
# Install Python dependencies
RUN pip install --no-cache-dir \
    pymongo \
    pyarrow \
    duckdb \
    numpy \
    pandas \
    plotly \
    scipy \
    boto3 \
    python-dotenv \
    psutil \
    requests

# Copy application code
COPY . /app/

# Make scripts executable
RUN chmod +x /app/main.sh /app/scr/run_pipeline.sh

# Set environment variable for Python executable
ENV PYTHON_EXE=python3

# Default command - run the pipeline
ENTRYPOINT ["/app/main.sh"]

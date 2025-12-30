FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# using trixie with ghcr because for preinstalled uv

# Set working directory
WORKDIR /app

# Prevents Python from writing .pyc files to disk - saves space
ENV PYTHONDONTWRITEBYTECODE=1 
# Ensures that Python output is sent straight to terminal (e.g. for logging) and not buffered
ENV PYTHONUNBUFFERED=1

# Copy project files first to leverage Docker cache
COPY pyproject.toml .
RUN uv sync

# Create directory for data files
# RUN mkdir -p /app/data

# rest of the files goes here
COPY config/ ./config/
COPY main.py .
COPY src/ ./src

# Expose the default port
# EXPOSE 8080

# Default command using the virtual environment
CMD ["uv", "run", "main.py"]

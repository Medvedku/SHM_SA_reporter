#!/bin/bash

# Main entry point for SHM Reporter Pipeline
# This script serves as a convenient wrapper to run the pipeline

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the main pipeline script with all arguments passed through
exec "$SCRIPT_DIR/scr/run_pipeline.sh" "$@"

import subprocess
import sys
import time
import logging
import psutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_tree_memory_usage(pid):
    """
    Computes the total RSS memory usage of a process and all its children.
    """
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        total_rss = parent.memory_info().rss
        for child in children:
            try:
                total_rss += child.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return total_rss
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0


def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0: "", 1: "K", 2: "M", 3: "G", 4: "T"}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"


def main():
    # Resolve paths
    current_dir = Path(__file__).parent.resolve()
    target_script = current_dir / "run_pipeline.py"

    if not target_script.exists():
        logger.error(f"Could not find {target_script}")
        return

    # Prepare command: python3 src/run_pipeline.py [args...]
    cmd = [sys.executable, str(target_script)] + sys.argv[1:]

    logger.info("=" * 60)
    logger.info("RAM MONITOR WRAPPER")
    logger.info(f"Launching: {' '.join(cmd)}")
    logger.info("=" * 60)

    start_time = time.time()

    # Start the subprocess
    try:
        process = subprocess.Popen(cmd)
    except Exception as e:
        logger.error(f"Failed to start process: {e}")
        return

    peak_ram = 0
    try:
        while process.poll() is None:
            # Measure memory
            current_ram = get_tree_memory_usage(process.pid)
            peak_ram = max(peak_ram, current_ram)

            # Show live stats
            elapsed = time.time() - start_time
            sys.stdout.write(
                f"\r[Running] T: {elapsed:.1f}s | Current RAM: {format_bytes(current_ram)} | Peak RAM: {format_bytes(peak_ram)}   "
            )
            sys.stdout.flush()

            # Sleep briefly to avoid high CPU usage for monitoring
            time.sleep(0.5)

    except KeyboardInterrupt:
        logger.warning("Interrupted by user. Terminating pipeline...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        logger.info("Pipeline terminated.")
        return

    # Final logic
    end_time = time.time()
    duration = end_time - start_time
    return_code = process.returncode

    # Clear the status line
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

    logger.info("=" * 60)
    if return_code == 0:
        logger.info("Pipeline FINISHED successfully.")
    else:
        logger.error(f"Pipeline FAILED with exit code {return_code}.")

    logger.info("-" * 60)
    logger.info(f"Total Duration : {duration:.2f} seconds")
    logger.info(f"Peak RAM Usage : {format_bytes(peak_ram)}")
    logger.info("=" * 60)

    sys.exit(return_code)


if __name__ == "__main__":
    main()

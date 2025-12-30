#!/usr/bin/env python3
"""Run `run_full_report.py` while monitoring RAM usage.

This script launches the existing runner and periodically samples
its memory usage (and descendants when possible). It prints updates
and writes a summary JSON with peak RSS in KB.

Usage:
  python3 scr/plotting/run_with_ram.py --end-date 2025-11-23 --yes

Options:
  --interval N   Sampling interval in seconds (default 1)
  --log PATH     Path to write JSON summary (default: ./ram_usage_<ts>.json)
  --python PATH  Python executable to run the runner (default: this interpreter)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_rss_kb_psutil(pid: int) -> Optional[int]:
    try:
        import psutil

        p = psutil.Process(pid)
        rss = p.memory_info().rss
        # include children
        for c in p.children(recursive=True):
            try:
                rss += c.memory_info().rss
            except Exception:
                pass
        return int(rss / 1024)
    except Exception:
        return None


def get_rss_kb_proc(pid: int) -> Optional[int]:
    # Fallback for Linux: read /proc/<pid>/status VmRSS and try children (best-effort)
    try:
        status = Path(f"/proc/{pid}/status")
        if not status.exists():
            return None
        text = status.read_text()
        for line in text.splitlines():
            if line.startswith("VmRSS:"):
                parts = line.split()
                # VmRSS:    123456 kB
                if len(parts) >= 2:
                    return int(parts[1])
        return None
    except Exception:
        return None


def get_rss_kb(pid: int) -> int:
    # Try psutil first
    v = get_rss_kb_psutil(pid)
    if v is not None:
        return v
    v = get_rss_kb_proc(pid)
    if v is not None:
        return v
    return 0


def make_cmd(python: str, end_date: Optional[str], yes: bool, verbose: bool) -> list[str]:
    cmd = [python, str(Path(__file__).resolve().parents[2] / "scr" / "plotting" / "run_full_report.py")]
    if end_date:
        cmd += ["--end-date", end_date]
    if yes:
        cmd += ["--yes"]
    if verbose:
        cmd += ["--verbose"]
    return cmd


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--end-date", help="END date (YYYY-MM-DD)", default=None)
    p.add_argument("--yes", help="Auto-confirm deletion", action="store_true")
    p.add_argument("--interval", help="Sampling interval in seconds", type=float, default=1.0)
    p.add_argument("--log", help="Path to JSON summary file", default=None)
    p.add_argument("--python", help="Python executable to run the runner", default=sys.executable)
    p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = p.parse_args()

    cmd = make_cmd(args.python, args.end_date, args.yes, args.verbose)

    if args.verbose:
        print("Launching:", " ".join(cmd))

    start_ts = datetime.utcnow().isoformat()
    proc = subprocess.Popen(cmd)

    peak_kb = 0
    samples = []

    try:
        while True:
            if proc.poll() is not None:
                # process finished
                break
            rss = get_rss_kb(proc.pid)
            peak_kb = max(peak_kb, rss)
            samples.append({"ts": datetime.utcnow().isoformat(), "rss_kb": rss})
            if args.verbose:
                print(f"[{len(samples)}] PID={proc.pid} RSS={rss} KB (peak {peak_kb} KB)")
            time.sleep(max(0.1, args.interval))

        # one last sample after exit
        rss = get_rss_kb(proc.pid)
        peak_kb = max(peak_kb, rss)
        samples.append({"ts": datetime.utcnow().isoformat(), "rss_kb": rss})

        ret = proc.wait()
        end_ts = datetime.utcnow().isoformat()

        summary = {
            "cmd": cmd,
            "start_utc": start_ts,
            "end_utc": end_ts,
            "exit_code": ret,
            "peak_rss_kb": peak_kb,
            "samples": samples,
        }

        # Write summary
        if args.log:
            outpath = Path(args.log)
        else:
            stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            outpath = Path.cwd() / f"ram_usage_{stamp}.json"

        outpath.write_text(json.dumps(summary, indent=2))
        
        if args.verbose:
            print(f"Wrote summary to: {outpath}")
            print(f"Peak RSS: {peak_kb} KB. Exit code: {ret}")
        
        sys.exit(ret)

    except KeyboardInterrupt:
        print("Interrupted — terminating child process...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        raise


if __name__ == "__main__":
    main()

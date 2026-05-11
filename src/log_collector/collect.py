#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


DEFAULT_OUT = "data/datasets/metrics_log_events.csv"

# Signatures of "Bad events"
PATTERNS = {
    "error": re.compile(r"\b(error|failed|failure|critical)\b", re.IGNORECASE),
    "oom": re.compile(r"\b(out of memory|oom-killer|killed process)\b", re.IGNORECASE),
    "io": re.compile(r"\b(i/o error|blk_update_request|buffer i/o)\b", re.IGNORECASE),
    "auth": re.compile(r"\b(authentication failure|failed password|invalid user)\b", re.IGNORECASE),
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_new_lines(log_path: Path, state_path: Path) -> list[str]:
    
    # Reads only new lines from log file, using offset in state-file.
    
    offset = 0
    if state_path.exists():
        try:
            offset = int(state_path.read_text().strip() or "0")
        except ValueError:
            offset = 0

    if not log_path.exists():
        return []

    with log_path.open("rb") as f:
        f.seek(offset)
        data = f.read()
        new_offset = f.tell()

    # Saving new offset
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(str(new_offset))

    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        text = ""

    lines = [ln for ln in text.splitlines() if ln.strip()]
    return lines


def classify_events(lines: list[str]) -> dict[str, int]:
    counts = {k: 0 for k in PATTERNS}
    for ln in lines:
        for name, rx in PATTERNS.items():
            if rx.search(ln):
                counts[name] += 1
    counts["lines_total"] = len(lines)
    return counts


def collect_metrics() -> dict[str, float]:
    cpu_percent = psutil.cpu_percent(interval=1.0)

    # cpu_times_percent returns percent by category, including iowait
    ct = psutil.cpu_times_percent(interval=None)
    iowait_percent = float(getattr(ct, "iowait", 0.0))

    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    io = psutil.disk_io_counters()

    return {
        "cpu_percent": round(cpu_percent, 2),
        "cpu_iowait": round(iowait_percent, 2),
        "mem_percent": round(vm.percent, 2),
        "swap_percent": round(swap.percent, 2),
        "disk_percent_root": round(disk.percent, 2),
        "disk_read_bytes": float(io.read_bytes if io else 0),
        "disk_write_bytes": float(io.write_bytes if io else 0),
    }


def ensure_csv_header(path: Path, fieldnames: list[str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()


def append_row(path: Path, row: dict) -> None:
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        w.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect metrics + log events into CSV dataset")
    ap.add_argument("--log", default="/var/log/syslog", help="Log file to read (default: /var/log/syslog)")
    ap.add_argument("--out", default=DEFAULT_OUT, help=f"CSV output path (default: {DEFAULT_OUT})")
    ap.add_argument("--state", default="data/processed/syslog.offset", help="Offset state file path")
    ap.add_argument("--interval", type=int, default=10, help="Sampling interval seconds (default: 10)")
    ap.add_argument("--iterations", type=int, default=0, help="0 = infinite, otherwise N iterations")
    args = ap.parse_args()

    log_path = Path(args.log)
    out_path = Path(args.out)
    state_path = Path(args.state)

    fieldnames = [
        "ts_utc",
        "cpu_percent",
        "cpu_iowait",
        "mem_percent",
        "swap_percent",
        "disk_percent_root",
        "disk_read_bytes",
        "disk_write_bytes",
        "lines_total",
        "error",
        "oom",
        "io",
        "auth",
    ]
    ensure_csv_header(out_path, fieldnames)

    i = 0
    while True:
        lines = read_new_lines(log_path, state_path)
        events = classify_events(lines)
        metrics = collect_metrics()

        row = {"ts_utc": utc_now_iso(), **metrics, **events}
        append_row(out_path, row)

        print(f"[{row['ts_utc']}] cpu={row['cpu_percent']}% mem={row['mem_percent']}% "
              f"lines={row['lines_total']} err={row['error']} oom={row['oom']} io={row['io']} auth={row['auth']}")

        i += 1
        if args.iterations and i >= args.iterations:
            break
        time.sleep(args.interval)

    print(f"Saved dataset: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


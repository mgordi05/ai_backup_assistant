#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_LOG = "data/datasets/backup_results.csv"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_csv_header(path: Path, fieldnames: list[str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()


def get_dir_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return total
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def run_backup(source: Path, target_root: Path) -> dict:
    started_at = utc_now_iso()
    ts_folder = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = target_root / f"backup_{ts_folder}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    rsync_cmd = [
        "rsync",
        "-a",
        "--delete",
        f"{source}/",
        f"{backup_dir}/",
    ]

    start_perf = time.perf_counter()
    result = subprocess.run(
        rsync_cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    duration_sec = round(time.perf_counter() - start_perf, 3)

    src_size = get_dir_size_bytes(source)
    dst_size = get_dir_size_bytes(backup_dir)
    src_files = count_files(source)
    dst_files = count_files(backup_dir)

    success = result.returncode == 0
    status = "SUCCESS" if success else "FAILED"

    return {
        "started_at_utc": started_at,
        "finished_at_utc": utc_now_iso(),
        "status": status,
        "return_code": result.returncode,
        "duration_sec": duration_sec,
        "source_path": str(source),
        "backup_path": str(backup_dir),
        "source_files": src_files,
        "backup_files": dst_files,
        "source_size_bytes": src_size,
        "backup_size_bytes": dst_size,
        "stdout": (result.stdout or "").strip().replace("\n", " | "),
        "stderr": (result.stderr or "").strip().replace("\n", " | "),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run rsync backup and log result")
    parser.add_argument("--source", default="test_data/source", help="Source directory")
    parser.add_argument("--target", default="test_data/backup_target", help="Backup target root directory")
    parser.add_argument("--log", default=DEFAULT_LOG, help="CSV log path")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    target = Path(args.target).resolve()
    log_path = Path(args.log)

    if not shutil.which("rsync"):
        raise SystemExit("rsync is not installed or not found in PATH")

    if not source.exists() or not source.is_dir():
        raise SystemExit(f"Source directory does not exist: {source}")

    target.mkdir(parents=True, exist_ok=True)

    row = run_backup(source, target)

    fieldnames = [
        "started_at_utc",
        "finished_at_utc",
        "status",
        "return_code",
        "duration_sec",
        "source_path",
        "backup_path",
        "source_files",
        "backup_files",
        "source_size_bytes",
        "backup_size_bytes",
        "stdout",
        "stderr",
    ]
    ensure_csv_header(log_path, fieldnames)

    with log_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)

    print(f"Backup status: {row['status']}")
    print(f"Duration: {row['duration_sec']} sec")
    print(f"Backup path: {row['backup_path']}")
    print(f"Files copied: {row['backup_files']}")
    if row["stderr"]:
        print(f"stderr: {row['stderr']}")

    return 0 if row["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

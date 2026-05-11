#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd


FEATURES = [
    "cpu_percent",
    "cpu_iowait",
    "mem_percent",
    "swap_percent",
    "disk_percent_root",
    "lines_total",
    "error",
    "oom",
    "io",
    "auth",
]

DEFAULT_DECISION_LOG = "data/datasets/smart_backup_log.csv"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_csv_header(path: Path, fieldnames: list[str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()


def decide(data_path: str, model_path: str, scaler_path: str, threshold: float, max_cpu: float) -> dict:
    df = pd.read_csv(data_path)
    last = df.tail(1).copy()

    if last.empty:
        raise SystemExit("Dataset is empty, cannot decide.")

    X = last[FEATURES].fillna(0.0)

    scaler = joblib.load(scaler_path)
    model = joblib.load(model_path)

    Xs = scaler.transform(X)
    score = float(model.score_samples(Xs)[0])

    cpu = float(last["cpu_percent"].iloc[0])
    is_anomaly = score <= threshold
    too_busy = cpu >= max_cpu

    decision = "POSTPONE" if (is_anomaly or too_busy) else "BACKUP_NOW"

    return {
        "ts_utc": str(last["ts_utc"].iloc[0]),
        "anomaly_score": score,
        "threshold": threshold,
        "cpu_percent": cpu,
        "max_cpu": max_cpu,
        "is_anomaly": is_anomaly,
        "too_busy": too_busy,
        "decision": decision,
    }


def run_backup_executor(source: str, target: str, backup_log: str) -> subprocess.CompletedProcess:
    cmd = [
        "./src/scheduler/backup_executor.py",
        "--source", source,
        "--target", target,
        "--log", backup_log,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-driven smart backup launcher")
    parser.add_argument("--data", default="data/datasets/metrics_log_events.csv")
    parser.add_argument("--model", default="models/iforest.joblib")
    parser.add_argument("--scaler", default="models/scaler.joblib")
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--max-cpu", type=float, default=60.0)

    parser.add_argument("--source", default="test_data/source")
    parser.add_argument("--target", default="test_data/backup_target")
    parser.add_argument("--backup-log", default="data/datasets/backup_results.csv")
    parser.add_argument("--decision-log", default=DEFAULT_DECISION_LOG)
    args = parser.parse_args()

    decision_info = decide(
        data_path=args.data,
        model_path=args.model,
        scaler_path=args.scaler,
        threshold=args.threshold,
        max_cpu=args.max_cpu,
    )

    # determine reason
    if decision_info["is_anomaly"] and decision_info["too_busy"]:
        reason = "BOTH"
    elif decision_info["too_busy"]:
        reason = "HIGH_CPU"
    elif decision_info["is_anomaly"]:
        reason = "ANOMALY"
    else:
        reason = "NONE"

    row = {
        "run_at_utc": utc_now_iso(),
        "sample_ts_utc": decision_info["ts_utc"],
        "anomaly_score": round(decision_info["anomaly_score"], 6),
        "threshold": round(decision_info["threshold"], 6),
        "cpu_percent": round(decision_info["cpu_percent"], 2),
        "max_cpu": round(decision_info["max_cpu"], 2),
        "is_anomaly": decision_info["is_anomaly"],
        "too_busy": decision_info["too_busy"],
        "reason": reason,
        "decision": decision_info["decision"],
        "action_taken": "",
        "executor_return_code": "",
        "executor_stdout": "",
        "executor_stderr": "",
    }

    if decision_info["decision"] == "BACKUP_NOW":
        result = run_backup_executor(args.source, args.target, args.backup_log)
        row["action_taken"] = "BACKUP_EXECUTED"
        row["executor_return_code"] = result.returncode
        row["executor_stdout"] = (result.stdout or "").strip().replace("\n", " | ")
        row["executor_stderr"] = (result.stderr or "").strip().replace("\n", " | ")
        print("Decision: BACKUP_NOW")
        print((result.stdout or "").strip())
        if result.stderr:
            print("stderr:", result.stderr.strip())
    else:
        row["action_taken"] = "BACKUP_SKIPPED"
        row["executor_return_code"] = ""
        print("Decision: POSTPONE")
        print("Backup skipped due to anomaly or high load.")

    decision_log_path = Path(args.decision_log)
    fieldnames = list(row.keys())
    ensure_csv_header(decision_log_path, fieldnames)

    with decision_log_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/datasets/metrics_log_events.csv")
    ap.add_argument("--model", default="models/iforest.joblib")
    ap.add_argument("--scaler", default="models/scaler.joblib")
    ap.add_argument("--threshold", type=float, required=True, help="Anomaly threshold from training output")
    ap.add_argument("--max_cpu", type=float, default=60.0, help="Hard rule: don't backup above CPU%")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    last = df.tail(1).copy()

    X = last[FEATURES].fillna(0.0)

    scaler = joblib.load(args.scaler)
    model = joblib.load(args.model)

    Xs = scaler.transform(X)
    score = float(model.score_samples(Xs)[0])

    cpu = float(last["cpu_percent"].iloc[0])

    # Decision: combine ML + hard rule (объяснимо для диплома)
    is_anomaly = score <= args.threshold
    too_busy = cpu >= args.max_cpu

    decision = "POSTPONE" if (is_anomaly or too_busy) else "BACKUP_NOW"

    print(f"Last ts={last['ts_utc'].iloc[0]}")
    print(f"anomaly_score={score:.6f} threshold={args.threshold:.6f} is_anomaly={is_anomaly}")
    print(f"cpu_percent={cpu:.2f} max_cpu={args.max_cpu:.2f} too_busy={too_busy}")
    print(f"DECISION={decision}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())


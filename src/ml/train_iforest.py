#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


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
    ap.add_argument("--data", default="data/datasets/metrics_log_events.csv", help="CSV dataset path")
    ap.add_argument("--model-out", default="models/iforest.joblib", help="Model output path")
    ap.add_argument("--scaler-out", default="models/scaler.joblib", help="Scaler output path")
    ap.add_argument("--contamination", type=float, default=0.05, help="Expected anomaly ratio")
    args = ap.parse_args()

    df = pd.read_csv(args.data)

    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns: {missing}")

    X = df[FEATURES].fillna(0.0)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=200,
        contamination=args.contamination,
        random_state=42,
    )
    model.fit(Xs)

    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model_out)
    joblib.dump(scaler, args.scaler_out)

    # score_samples: smaller number = more anomaly
    scores = model.score_samples(Xs)
    df["anomaly_score"] = scores

    # Threshold: taking minimum quantile by contamination
    threshold = float(pd.Series(scores).quantile(args.contamination))
    print(f"Trained IsolationForest on {len(df)} rows")
    print(f"Anomaly threshold (lower is worse): {threshold:.6f}")

    # printing top 5 anomalies
    print("\nTop-5 anomalies:")
    print(df.sort_values("anomaly_score").head(5)[["ts_utc", "anomaly_score"] + FEATURES])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


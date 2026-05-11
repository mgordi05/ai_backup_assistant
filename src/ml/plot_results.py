#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


METRICS_CSV = "data/datasets/metrics_log_events.csv"
SMART_LOG_CSV = "data/datasets/smart_backup_log.csv"
BACKUP_CSV = "data/datasets/backup_results.csv"
OUT_DIR = Path("docs/figures")


def ensure_out_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(p)


def plot_cpu(metrics_df: pd.DataFrame) -> Path:
    df = metrics_df.copy()
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)

    plt.figure(figsize=(12, 5))
    plt.plot(df["ts_utc"], df["cpu_percent"])
    plt.xlabel("Time")
    plt.ylabel("CPU %")
    plt.title("CPU utilization over time")
    plt.xticks(rotation=30)
    plt.tight_layout()

    out = OUT_DIR / "cpu_over_time.png"
    plt.savefig(out, dpi=150)
    plt.close()
    return out


def plot_anomaly_score(smart_df: pd.DataFrame) -> Path:
    df = smart_df.copy()
    df["run_at_utc"] = pd.to_datetime(df["run_at_utc"], utc=True)

    plt.figure(figsize=(12, 5))
    plt.plot(df["run_at_utc"], df["anomaly_score"], marker="o")

    if "threshold" in df.columns and not df["threshold"].isna().all():
        threshold = float(df["threshold"].dropna().iloc[-1])
        plt.axhline(y=threshold)

    plt.xlabel("Time")
    plt.ylabel("Anomaly score")
    plt.title("Anomaly score over time")
    plt.xticks(rotation=30)
    plt.tight_layout()

    out = OUT_DIR / "anomaly_score_over_time.png"
    plt.savefig(out, dpi=150)
    plt.close()
    return out


def plot_decisions(smart_df: pd.DataFrame) -> Path:
    df = smart_df.copy()

    counts = df["decision"].value_counts().reindex(["BACKUP_NOW", "POSTPONE"], fill_value=0)

    plt.figure(figsize=(8, 5))
    plt.bar(counts.index, counts.values)
    plt.xlabel("Decision")
    plt.ylabel("Count")
    plt.title("Backup decisions")

    for i, v in enumerate(counts.values):
        plt.text(i, v, str(v), ha="center", va="bottom")

    plt.tight_layout()

    out = OUT_DIR / "decision_counts.png"
    plt.savefig(out, dpi=150)
    plt.close()
    return out


def plot_backup_duration(backup_df: pd.DataFrame) -> Path:
    df = backup_df.copy()
    df["started_at_utc"] = pd.to_datetime(df["started_at_utc"], utc=True)

    plt.figure(figsize=(12, 5))
    plt.plot(df["started_at_utc"], df["duration_sec"], marker="o")
    plt.xlabel("Time")
    plt.ylabel("Duration (sec)")
    plt.title("Backup duration over time")
    plt.xticks(rotation=30)
    plt.tight_layout()

    out = OUT_DIR / "backup_duration_over_time.png"
    plt.savefig(out, dpi=150)
    plt.close()
    return out


def main() -> int:
    ensure_out_dir()

    metrics_df = load_csv(METRICS_CSV)
    smart_df = load_csv(SMART_LOG_CSV)
    backup_df = load_csv(BACKUP_CSV)

    outputs = [
        plot_cpu(metrics_df),
        plot_anomaly_score(smart_df),
        plot_decisions(smart_df),
        plot_backup_duration(backup_df),
    ]

    print("Generated figures:")
    for path in outputs:
        print(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

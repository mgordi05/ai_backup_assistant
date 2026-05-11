# AI Backup Assistant

AI-based prototype for intelligent backup scheduling and anomaly detection in SME server environments.

This project was developed as part of a Bachelor's thesis at Tallinn University of Technology (TalTech).

## Project Goal

The goal of the prototype is to improve server backup reliability by analyzing system metrics and log events before starting a backup process.

Instead of using a static cron schedule, the system dynamically decides whether a backup should be executed immediately or postponed based on current server conditions.

## Main Features

* anomaly detection using Isolation Forest
* dynamic backup scheduling
* CPU-aware backup decisions
* automatic backup postponing during high system load
* log-based anomaly monitoring
* backup execution logging
* automatic result visualization

## Technologies Used

* Python 3.12
* scikit-learn
* pandas
* matplotlib
* psutil
* rsync
* systemd.timer
* Ubuntu 24.04


## Example Workflow

### 1. Collect system metrics and logs

```bash
./src/log_collector/collect.py
```

### 2. Train anomaly detection model

```bash
./src/ml/train_iforest.py
```

### 3. Run smart backup scheduler

```bash
./src/scheduler/smart_backup.py
```

## Backup Decision Logic

The system can generate two main decisions:

* `BACKUP_NOW`
* `POSTPONE`

Possible postponing reasons:

* `HIGH_CPU`
* `ANOMALY`
* `BOTH`

## Example Test Scenarios

* normal system operation
* high CPU load
* synthetic log anomalies
* failed authentication events

## Thesis Context

This repository contains the practical implementation of the Bachelor's thesis:

**"Tehisintellektil põhinev abiline serverite varundamiseks ja hooldamiseks väikeettevõttes"**

Tallinn University of Technology (TalTech), 2026.

## Repository Contents

The repository includes:

* source code
* testing scripts
* prototype architecture
* generated figures
* example datasets
* automation scripts

## Author

Mark Gordin



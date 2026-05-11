#!/bin/bash

cd /opt/ai-backup-assistant

# активируем venv
source venv/bin/activate

# собираем свежие метрики (3 замера)
./src/log_collector/collect.py --interval 2 --iterations 3

# запускаем AI + backup
./src/scheduler/smart_backup.py --threshold -0.611155

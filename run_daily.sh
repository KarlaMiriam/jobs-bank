#!/bin/bash

# caminho do seu projeto (o seu está no iCloud Drive)
PROJECT_DIR="/Users/karlaraymondi/Library/Mobile Documents/com~apple~CloudDocs/jobbot"

# entra na pasta
cd "$PROJECT_DIR" || exit 1

# ativa o virtualenv
source .venv/bin/activate

# cria pasta de logs (se não existir)
mkdir -p logs

# data bonitinha
NOW=$(date +"%Y-%m-%d_%H-%M-%S")

# roda o robô e salva log
python main.py >> "logs/run_$NOW.log" 2>&1

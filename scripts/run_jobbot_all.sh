#!/usr/bin/env bash
set -euo pipefail

# No Render, o app normalmente fica em /app
cd /app

echo "🚀 Iniciando coleta de vagas EB3 (EUA)..."
python main.py

echo "🍁 Iniciando coleta de vagas do Canadá..."
python main_canada.py

echo "✅ Todas as coletas finalizadas com sucesso."

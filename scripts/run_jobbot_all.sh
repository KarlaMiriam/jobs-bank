#!/usr/bin/env bash
set -euo pipefail

# Removemos o cd /app – no Render o working dir já é a raiz do projeto

echo "🚀 Iniciando coleta de vagas EB3 (EUA)..."
python main.py

echo "🍁 Iniciando coleta de vagas do Canadá..."
python main_canada.py

echo "✅ Todas as coletas finalizadas com sucesso."

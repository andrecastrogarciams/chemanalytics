#!/bin/bash
# ChemAnalytics - Script de Atualização Automática (Ubuntu Server)
# Local padrão: /opt/chemanalytics/deploy/ubuntu/update.sh

set -e

PROJECT_ROOT="/opt/chemanalytics"
BRANCH="chore/ubuntu-deploy-templates"

echo "--------------------------------------------------"
echo "🚀 Iniciando atualização do ChemAnalytics..."
echo "--------------------------------------------------"

cd $PROJECT_ROOT

echo "📥 1. Baixando código mais recente ($BRANCH)..."
sudo -u chemanalytics git fetch origin
sudo -u chemanalytics git reset --hard origin/$BRANCH

echo "🐍 2. Atualizando Backend (Python/Django)..."
sudo -u chemanalytics $PROJECT_ROOT/.venv/bin/python -m pip install -q -r backend/requirements.txt
sudo -u chemanalytics $PROJECT_ROOT/.venv/bin/python -m pip install -q -r backend/requirements-integration.txt
sudo -u chemanalytics $PROJECT_ROOT/.venv/bin/python backend/manage.py migrate
sudo -u chemanalytics $PROJECT_ROOT/.venv/bin/python backend/manage.py collectstatic --noinput

echo "⚛️ 3. Reconstruindo Frontend (React/Vite)..."
cd frontend
sudo -u chemanalytics npm ci
sudo -u chemanalytics npm run build

echo "🔄 4. Reiniciando serviços..."
sudo systemctl restart chemanalytics

echo "--------------------------------------------------"
echo "✅ Atualização concluída com sucesso!"
echo "--------------------------------------------------"
sudo systemctl status chemanalytics --no-pager

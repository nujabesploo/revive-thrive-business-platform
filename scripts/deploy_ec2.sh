#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/projects/revive-thrive-business-platform}"
SERVICE_NAME="${SERVICE_NAME:-revive-thrive}"

echo "Deploying from: $APP_DIR"
cd "$APP_DIR"

git pull origin main
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt

sudo systemctl restart "$SERVICE_NAME"
sudo systemctl reload nginx

echo "Checking gunicorn upstream health"
curl -fsS http://127.0.0.1:5000/health >/dev/null

echo "Checking nginx reverse proxy health"
curl -fsS http://127.0.0.1/health >/dev/null

echo "Deploy complete"

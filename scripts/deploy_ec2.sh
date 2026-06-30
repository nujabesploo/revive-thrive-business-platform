#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/projects/revive-thrive-business-platform}"
SERVICE_NAME="${SERVICE_NAME:-revive-thrive}"

echo "Deploying from: $APP_DIR"
cd "$APP_DIR"

git pull origin main
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl reload nginx
curl -fsS http://127.0.0.1/health

echo "Deploy complete"

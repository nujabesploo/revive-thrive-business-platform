#!/usr/bin/env bash

# EC2 Setup Script for Revive & Thrive Tech Flask App
# Run on the EC2 instance as ubuntu user.

set -euo pipefail

PROJECT_DIR="/home/ubuntu/revive-thrive-platform"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_FILE="/etc/systemd/system/revive-thrive.service"
NGINX_CONF="/etc/nginx/sites-available/revive-thrive"
NGINX_ENABLED="/etc/nginx/sites-enabled/revive-thrive"
PUBLIC_IP="3.89.29.94"

# 1. Update system and install prerequisites
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git curl

# 2. Ensure project exists
if [ ! -d "$PROJECT_DIR" ]; then
  echo "Project directory $PROJECT_DIR does not exist. Create it and upload files first."
  exit 1
fi

cd "$PROJECT_DIR"

# 3. Set up virtual environment and dependencies
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Create systemd service
sudo tee "$SERVICE_FILE" > /dev/null <<'EOF'
[Unit]
Description=Revive Thrive Flask App
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/revive-thrive-platform
Environment="PATH=/home/ubuntu/revive-thrive-platform/venv/bin"
ExecStart=/home/ubuntu/revive-thrive-platform/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable revive-thrive
sudo systemctl start revive-thrive

# 5. Configure NGINX
sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name ${PUBLIC_IP};

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf "$NGINX_CONF" "$NGINX_ENABLED"
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 6. Status
sudo systemctl status revive-thrive --no-pager
sudo systemctl status nginx --no-pager

echo "Setup complete. Visit http://${PUBLIC_IP} to verify."
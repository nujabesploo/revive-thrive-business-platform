#!/usr/bin/env bash

# EC2 Setup Script for Revive & Thrive Tech Flask App
# Run on the EC2 instance as ubuntu user.

set -euo pipefail

PROJECT_DIR="/home/ubuntu/projects/revive-thrive-business-platform"
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
  echo "Project directory $PROJECT_DIR does not exist. Clone the repository first."
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
WorkingDirectory=/home/ubuntu/projects/revive-thrive-business-platform
Environment="PATH=/home/ubuntu/projects/revive-thrive-business-platform/venv/bin"
EnvironmentFile=-/home/ubuntu/projects/revive-thrive-business-platform/.env
ExecStart=/home/ubuntu/projects/revive-thrive-business-platform/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

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
      proxy_connect_timeout 60s;
      proxy_read_timeout 60s;
      proxy_send_timeout 60s;
    }
}
EOF

sudo ln -sf "$NGINX_CONF" "$NGINX_ENABLED"
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "Waiting for gunicorn to accept connections..."
for i in {1..20}; do
  if curl -fsS http://127.0.0.1:5000/health >/dev/null; then
    echo "Gunicorn health check passed"
    break
  fi
  sleep 1
done

curl -fsS http://127.0.0.1/health >/dev/null
echo "Nginx reverse proxy health check passed"

# 6. Status
sudo systemctl status revive-thrive --no-pager
sudo systemctl status nginx --no-pager

echo "Setup complete. Visit http://${PUBLIC_IP} to verify."
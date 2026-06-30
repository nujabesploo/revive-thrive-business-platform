# Revive & Thrive Tech EC2 Deployment Guide

## Overview
This guide covers deploying the Flask app to an Ubuntu EC2 instance using Gunicorn, systemd, and NGINX. It also includes instructions for domain setup and HTTPS.

## Assumptions
- EC2 instance user: `ubuntu`
- Project path: `/home/ubuntu/projects/revive-thrive-business-platform`
- Virtualenv path: `/home/ubuntu/projects/revive-thrive-business-platform/venv`
- App entrypoint: `app:app`
- Docker already added to repo, but this guide uses EC2 host deployment.

---

## Phase 1 — Create systemd service

1. SSH into EC2:

```bash
ssh -i ~/Downloads/revive-thrive-key.pem ubuntu@3.89.29.94
```

2. Go to the project directory:

```bash
cd /home/ubuntu/projects/revive-thrive-business-platform
```

3. Activate the virtual environment and test Gunicorn:

```bash
source venv/bin/activate
gunicorn --bind 127.0.0.1:5000 app:app
```

4. In another terminal, verify the app loads:

```bash
http://3.89.29.94:5000
```

5. Stop the test server with `CTRL+C`.


### Create service file

Create `/etc/systemd/system/revive-thrive.service` with:

```ini
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
```

Then run:

```bash
sudo systemctl daemon-reload
sudo systemctl start revive-thrive
sudo systemctl enable revive-thrive
sudo systemctl status revive-thrive
```


## Phase 2 — Connect NGINX

1. Create `/etc/nginx/sites-available/revive-thrive`:

```nginx
server {
    listen 80;
    server_name 3.89.29.94;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

2. Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/revive-thrive /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

3. Test in browser:

```bash
http://3.89.29.94
```


## Phase 3 — Add Domain/Subdomain

1. In your DNS provider, create an `A` record:

- Name: `www` or your chosen subdomain
- Value: `3.89.29.94`
- TTL: 300 or default

2. Optionally create a root record:

- Name: `@`
- Value: `3.89.29.94`

3. Wait for DNS propagation.


## Phase 4 — Add HTTPS

1. Install Certbot:

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

2. Run Certbot to get certificates:

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

3. Follow prompts and verify NGINX reloads.

4. Check certificate status:

```bash
sudo certbot certificates
```


## Phase 5 — Final Polish

1. Confirm service status:

```bash
sudo systemctl status revive-thrive
```

2. Confirm NGINX status:

```bash
sudo systemctl status nginx
```

3. Verify pages:

- `http://3.89.29.94`
- `https://yourdomain.com`
- `https://yourdomain.com/inventory`
- `https://yourdomain.com/admin`

4. Capture screenshots:

- Homepage
- Admin dashboard
- Add inventory page
- Edit inventory page
- API JSON response
- Database table / project tree
- Running on HTTPS

5. Commit and push:

```bash
git add .
git commit -m "Add EC2 deployment guide and inventory dashboard"
git push origin main
```

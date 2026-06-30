# Revive & Thrive Tech Platform

Production-ready Flask platform for repair booking, ticket management, and inventory operations. This repository is the flagship DevOps portfolio project for Revive & Thrive Tech.

## Core Features
- Customer booking workflow with email + Telegram business alerts
- Admin-authenticated dashboard, ticket updates, and inventory controls
- Public marketing homepage with S3-hosted brand media
- Health endpoint for uptime probes: `GET /health`
- Branded custom error pages (`404` and `500`)

## Architecture
```
Browser
  -> Nginx (TLS termination, reverse proxy)
    -> Gunicorn (systemd-managed)
      -> Flask app
        -> SQLite (current)
        -> S3 media
        -> Telegram Bot API
```

## Quick Start (Local)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

App URLs:
- `http://127.0.0.1:5000` (or next available port)
- `http://127.0.0.1:5000/health`

## Environment Variables
Set these in `.env`:

```env
FLASK_SECRET_KEY=change-me
BUSINESS_EMAIL=you@example.com
MAIL_USERNAME=your-smtp-user
MAIL_PASSWORD=your-smtp-password

TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

S3_BASE_URL=https://your-cloudfront-or-s3-base-url

ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
```

## Docker
The container now runs with Gunicorn by default.

Build:
```bash
docker build -t revive-thrive-platform .
```

Run:
```bash
docker run --rm -p 5000:5000 --env-file .env revive-thrive-platform
```

Test:
```bash
curl http://127.0.0.1:5000/health
```

## CI/CD (GitHub Actions)
### CI Workflow
File: `.github/workflows/ci.yml`

Runs on push/PR:
- dependency install
- Python syntax check
- Flask route smoke tests
- Docker build validation

### EC2 Deploy Workflow
File: `.github/workflows/deploy-ec2.yml`

Runs on push to `main` (or manual trigger) and deploys via SSH.

Required repository secrets:
- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`

## EC2 Deployment (Manual)
```bash
cd ~/projects/revive-thrive-business-platform
git pull origin main
sudo systemctl restart revive-thrive
sudo systemctl reload nginx
curl -fsS http://127.0.0.1/health
```

Detailed guide: `deploy/README-EC2.md`

## This Week DevOps Targets
- Stabilize production endpoints and error handling
- Keep Docker image runnable locally
- Keep CI green on each push
- Enable push-to-deploy with GitHub Actions
- Maintain deployment docs as a real team runbook

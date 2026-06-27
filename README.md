# Revive & Thrive Tech - Inventory Management System

## Project Overview
Revive & Thrive Tech is a full-stack inventory management and repair booking platform built with Flask, SQLite, and modern responsive HTML/CSS. The app supports technicians and administrators to track repair inventory, manage repair requests, and monitor stock levels.

## Business Problem
Repair technicians need a streamlined system to track parts inventory, manage repair tickets, and access real-time status without relying on spreadsheets or email chains.

## Solution
This platform provides:
- Repair booking and ticketing workflow
- Inventory dashboard for repair parts
- Inventory CRUD operations
- Repair status tracking for customers
- Admin dashboard for ticket overview
- REST API endpoints for inventory and bookings
- Deployment-ready Docker and EC2 support

## Features

### Inventory Dashboard
- Total inventory items
- Low stock items
- Total inventory value
- Out-of-stock count
- Search and category filters
- Add, edit, delete inventory items

### Repair Management
- Book repair requests
- Track repair status by phone
- Admin ticket management
- Update repair status, cost, and notes

### API Endpoints
- `GET /api/inventory`
- `GET /api/inventory/<id>`
- `GET /api/bookings`

### Deployment
- Docker containerization
- EC2 deployment with systemd and NGINX
- HTTPS support via Certbot

## Tech Stack
- Python 3
- Flask
- SQLite
- HTML/CSS
- Gunicorn
- NGINX
- Docker

## Getting Started

### Local Setup
1. Clone the repo:
   ```bash
   git clone <repo-url>
   cd revive-thrive-business-platform
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python3 app.py
   ```
4. Open in browser:
   ```bash
   http://localhost:5000
   ```

## Docker Setup

```bash
docker build -t revive-thrive-platform .
docker run -p 5000:5000 revive-thrive-platform
```

## EC2 Deployment

A deployment guide is available in `deploy/README-EC2.md`.

## Project Structure

- `app.py` — Flask application
- `templates/` — Jinja2 HTML templates
- `static/style.css` — app styling
- `deploy/` — EC2 deployment templates and script
- `Dockerfile` — container image build
- `.dockerignore` — Docker ignore rules

## Future Improvements
- Domain and SSL automation
- Inventory auto deduction from repair bookings
- Email notifications for customers
- CI/CD pipeline
- Multi-store inventory support

## Screenshots
Add screenshots of:
- Homepage
- Admin dashboard
- Add inventory page
- Edit inventory page
- API JSON response
- Running on HTTPS

## Business Value
This application helps Revive & Thrive Tech reduce manual inventory management, increase repair visibility, and improve customer service with a polished web interface.

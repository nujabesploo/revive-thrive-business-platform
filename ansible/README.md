# Ansible Automation

This playbook configures an Ubuntu app server for Revive & Thrive Tech.

## What it does
- Installs runtime dependencies
- Ensures Python virtualenv and app dependencies
- Installs systemd service for Gunicorn
- Configures and enables Nginx reverse proxy
- Runs local health check against `/health`

## Run

1. Copy inventory and vars examples:
   cp inventory.ini.example inventory.ini
   cp group_vars/all.yml.example group_vars/all.yml

2. Edit both files with your real host and values.

3. Execute playbook:
   ansible-playbook -i inventory.ini site.yml

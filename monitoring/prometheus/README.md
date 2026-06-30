# Prometheus Monitoring

Local monitoring stack for DevOps validation:
- Prometheus on port 9090
- Node exporter on port 9100
- Health scrape for app endpoint

## Start
cd monitoring/prometheus
docker compose up -d

## Verify
- Prometheus: http://127.0.0.1:9090
- Targets page: http://127.0.0.1:9090/targets

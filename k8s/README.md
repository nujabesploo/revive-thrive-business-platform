# Kubernetes Baseline

This directory contains a baseline deployment model for Revive & Thrive Tech.

## Apply order
kubectl apply -f base/namespace.yaml
kubectl apply -f base/configmap.yaml
kubectl apply -f base/secret.example.yaml
kubectl apply -f base/deployment.yaml
kubectl apply -f base/service.yaml
kubectl apply -f base/ingress.yaml
kubectl apply -f base/hpa.yaml

## Notes
- Replace container image with your real registry image.
- Copy secret.example.yaml to secret.yaml and fill real values.
- Install metrics-server before enabling HPA in production.

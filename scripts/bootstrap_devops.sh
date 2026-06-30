#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

printf "DevOps bootstrap check in %s\n" "$ROOT_DIR"

for p in \
  "$ROOT_DIR/infrastructure/terraform" \
  "$ROOT_DIR/ansible" \
  "$ROOT_DIR/k8s/base" \
  "$ROOT_DIR/monitoring/prometheus" \
  "$ROOT_DIR/.github/workflows"; do
  if [[ -d "$p" ]]; then
    printf "OK  %s\n" "$p"
  else
    printf "MISS %s\n" "$p"
    exit 1
  fi
done

printf "DevOps baseline directories verified\n"

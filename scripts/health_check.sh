#!/usr/bin/env bash
set -euo pipefail

TARGET_URL="${1:-https://revivethrivetech.com/health}"

printf "Checking %s\n" "$TARGET_URL"
response="$(curl -fsS "$TARGET_URL")"
printf "Response: %s\n" "$response"

echo "$response" | grep -q '"status"' && echo "Health check passed"

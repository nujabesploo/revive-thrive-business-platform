#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" - <<'CHECK'
from pathlib import Path
for name in ['app.py', 'config.py', 'database.py', 'media.py', 'transactions.py']:
    compile(Path(name).read_text(), name, 'exec')
CHECK
"$PYTHON_BIN" scripts/test_transactions.py
bash -n deploy/setup-ec2.sh

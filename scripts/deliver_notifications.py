"""Single-host worker; flock prevents overlapping runs and duplicate concurrent delivery."""
import fcntl
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app,send_email,send_telegram
from notifications import deliver_pending
with open('/tmp/revive-notifications.lock','w') as lock:
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(0)
    with app.app_context():
        print(deliver_pending(send_email,send_telegram))

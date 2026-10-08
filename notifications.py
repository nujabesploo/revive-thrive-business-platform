"""Durable notification outbox. Worker delivery is at-least-once, never exactly-once."""
import time
import uuid
from database import get_db_connection


def initialize():
    db = get_db_connection()
    db.cursor().execute('''CREATE TABLE IF NOT EXISTS notification_outbox (
        id TEXT PRIMARY KEY, channel TEXT NOT NULL, recipient TEXT NOT NULL,
        subject TEXT NOT NULL, body TEXT NOT NULL, created_at REAL NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0, next_attempt REAL NOT NULL DEFAULT 0,
        delivered_at REAL, last_error TEXT NOT NULL DEFAULT '')''')
    db.cursor().execute('''CREATE TABLE IF NOT EXISTS contact_messages (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL,
        message TEXT NOT NULL, created_at REAL NOT NULL)''')
    db.commit()


def enqueue(db, channel, recipient, subject, body):
    db.cursor().execute('''INSERT INTO notification_outbox
        (id,channel,recipient,subject,body,created_at) VALUES (?,?,?,?,?,?)''',
        (uuid.uuid4().hex,channel,recipient,subject,body,time.time()))


def deliver_pending(email_sender, telegram_sender, limit=25):
    """Run only from the single locked worker, not a request or web process."""
    db=get_db_connection()
    rows=db.cursor().execute('''SELECT * FROM notification_outbox WHERE delivered_at IS NULL
        AND next_attempt <= ? ORDER BY created_at LIMIT ?''',(time.time(),limit)).fetchall()
    delivered=0
    for row in rows:
        error='delivery_not_confirmed'
        try:
            ok=(telegram_sender(row['body']) if row['channel']=='telegram' else
                email_sender(row['recipient'],row['subject'],row['body']))
        except Exception as exc:
            ok=False
            error=type(exc).__name__  # Never persist tokens, payloads or provider responses.
        attempts=row['attempts']+1
        db.cursor().execute('''UPDATE notification_outbox SET attempts=?, next_attempt=?,
            delivered_at=?, last_error=? WHERE id=?''',
            (attempts,time.time()+min(3600,30*2**min(attempts,7)),
             time.time() if ok else None,'' if ok else error,row['id']))
        db.commit()
        delivered+=bool(ok)
    return {'attempted':len(rows),'delivered':delivered}

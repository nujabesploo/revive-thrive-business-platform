"""Capability-based repair tracking. Never expose customer or staff-only fields."""
from flask import current_app
from itsdangerous import BadData, URLSafeTimedSerializer
from database import get_db_connection

MAX_AGE = 90 * 24 * 60 * 60

def serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='repair-tracking-v1')

def issue_tracking_code(booking_id):
    return serializer().dumps({'booking': int(booking_id)})

def lookup_tracking_code(code):
    if not code or len(code) > 512:
        return None
    try:
        payload = serializer().loads(code, max_age=MAX_AGE)
        booking_id = payload.get('booking') if isinstance(payload, dict) else None
        if type(booking_id) is not int or booking_id < 1:
            return None
    except BadData:
        return None
    conn = get_db_connection()
    try:
        row = conn.cursor().execute('SELECT ticket_code, status FROM bookings WHERE id = ?', (booking_id,)).fetchone()
        if row is None:
            return None
        return {'reference': row['ticket_code'], 'status': row['status'] or 'New Request'}
    finally:
        conn.close()

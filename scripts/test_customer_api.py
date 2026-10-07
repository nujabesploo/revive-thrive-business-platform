"""Exercise public catalog and private tracking without production data or email."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(tempfile.mkdtemp()) / 'api.db')
os.environ['FLASK_SECRET_KEY'] = 'disposable-test-key'
import app as application
from repair_tracking import issue_tracking_code
app = application.app
app.config['TESTING'] = True
with app.test_client() as client:
    catalog = client.get('/api/v1/repair-catalog')
    assert catalog.status_code == 200 and catalog.json['quote_required'] is True
    assert set(catalog.json) == {'version', 'devices', 'services', 'booking_url', 'quote_required'}
    assert client.post('/api/v1/repair-status', data={}).status_code == 400
    client.get('/book')
    with client.session_transaction() as state:
        csrf = state['csrf_token']
    data = dict(csrf_token=csrf, customer_name='Private Test Name', phone_number='5551234567', email='test@example.invalid', device_type='iPhone', device_model='13', service_needed='Screen Repair', issue_description='Private description', preferred_date='2099-01-01')
    with patch.object(application, 'send_email'), patch.object(application, 'send_telegram', return_value=True):
        invalid = client.post('/book', data={**data, 'device_type':'unsupported'})
        assert invalid.status_code == 400
        assert client.post('/book', data=data).status_code == 302
    with client.session_transaction() as state:
        code = state['tracking_code']
    response = client.post('/api/v1/repair-status', data={'csrf_token':csrf, 'tracking_code':code})
    assert response.status_code == 200
    assert set(response.json['repair']) == {'reference', 'status'}
    assert response.headers['Cache-Control'] == 'no-store'
    assert 'Private' not in response.get_data(as_text=True)
    for invalid in ['RT-0001', code + 'bad', 'x'*513]:
        assert client.post('/api/v1/repair-status', data={'csrf_token':csrf,'tracking_code':invalid}).status_code == 404
    with app.app_context(), patch('itsdangerous.timed.time.time', return_value=1):
        expired = issue_tracking_code(1)
    assert client.post('/api/v1/repair-status', data={'csrf_token':csrf,'tracking_code':expired}).status_code == 404
    assert client.get('/api/bookings').status_code == 302
    assert client.get('/track').headers['Cache-Control'] == 'no-store'
    assert client.get('/success').headers['Cache-Control'] == 'no-store'
print('Catalog, booking validation, private tracking, tampering, expiry, CSRF and staff isolation passed.')

import os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.mkdtemp())/'alerts.db')
os.environ['FLASK_SECRET_KEY']='test-only'
from app import app
from database import get_db_connection
from notifications import deliver_pending
app.config['TESTING']=True
with app.test_client() as c:
 c.get('/book')
 with c.session_transaction() as s: token=s['csrf_token']
 assert c.post('/book',data=dict(csrf_token=token,customer_name='Test',email='test@example.invalid',phone_number='5551234567',device_type='iPhone',device_model='13',service_needed='Screen Repair',issue_description='test',preferred_date='2099-01-01')).status_code==302
 assert c.post('/contact',data=dict(csrf_token=token,name='Test',email='test@example.invalid',message='Do not send externally')).status_code==302
 assert c.get('/api/v1/notification-health').status_code==302
 assert c.get('/admin/notifications').status_code==302
with app.app_context():
 db=get_db_connection();cur=db.cursor()
 assert cur.execute('SELECT email FROM bookings').fetchone()[0]=='test@example.invalid'
 assert cur.execute('SELECT COUNT(*) FROM contact_messages').fetchone()[0]==1
 assert cur.execute('SELECT COUNT(*) FROM notification_outbox').fetchone()[0]==5
 assert deliver_pending(lambda *a:False,lambda *a:False)=={'attempted':5,'delivered':0}
 assert deliver_pending(lambda *a:True,lambda *a:True)['attempted']==0
 cur.execute('UPDATE notification_outbox SET next_attempt=0');db.commit()
 assert deliver_pending(lambda *a:True,lambda *a:True)=={'attempted':5,'delivered':5}
 assert deliver_pending(lambda *a:True,lambda *a:True)['attempted']==0
print('Booking/contact persistence, retry backoff, successful delivery deduplication and protected health routes passed with fake senders.')

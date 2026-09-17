import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.mkdtemp())/'test.db')
os.environ['FLASK_SECRET_KEY']='test-only-secret'
os.environ['ADMIN_PASSWORD']='test-only-password'
from app import app
from database import get_engine
from transactions import metadata, records
from sqlalchemy import select
with app.app_context():
    metadata.create_all(get_engine())
app.config['TESTING']=True
with app.test_client() as client:
    for path in ['/','/book','/services','/contact','/admin/login']:
        response=client.get(path)
        assert response.status_code==200,(path,response.status_code)
        assert response.headers['X-Frame-Options']=='DENY'
        assert "form-action 'self'" in response.headers['Content-Security-Policy']
    assert client.post('/admin/transactions',data={}).status_code==400
    assert client.get('/admin/transactions').status_code==302
    with client.session_transaction() as state:
        token=state['csrf_token']
        state['is_admin']=True
        state['admin_username']='test-admin'
    payload={'csrf_token':token,'description':'=SUM(A1:A2)','amount':'12.50','kind':'income'}
    assert client.post('/admin/transactions',data=payload).status_code==302
    page = client.get('/admin/transactions')
    assert page.status_code==200
    assert b'Net recorded balance' in page.data
    assert b'$12.50' in page.data
    assert b"'=SUM" in client.get('/admin/transactions/export.csv').data
    with app.app_context(),get_engine().connect() as conn:
        record_id=conn.scalar(select(records.c.id))
    assert client.post(f'/admin/transactions/{record_id}/delete',data={'csrf_token':token}).status_code==302
    assert client.post(f'/admin/transactions/{record_id}/restore',data={'csrf_token':token}).status_code==302
    payload['amount']='NaN'
    assert client.post('/admin/transactions',data=payload).status_code==400
print('Public routes, authentication, CSRF, create/delete/restore, CSV safety and amount validation passed on a disposable database.')

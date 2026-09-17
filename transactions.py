"""Authenticated bookkeeping records, separate from repair quotes and payments."""
import csv
import io
import secrets
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from flask import Blueprint, abort, flash, redirect, render_template, request, session, Response
from sqlalchemy import MetaData, Table, Column, Integer, String, Text, CheckConstraint, select, insert, update
from database import get_engine

bp = Blueprint('transactions', __name__, url_prefix='/admin/transactions')
metadata = MetaData()
records = Table('transactions', metadata,
    Column('id', String(40), primary_key=True), Column('description', Text, nullable=False),
    Column('amount_cents', Integer, nullable=False), Column('kind', String(20), nullable=False),
    Column('created_at', String(40), nullable=False), Column('deleted_at', String(40)),
    CheckConstraint('amount_cents > 0'))
events = Table('transaction_audit', metadata, Column('id', Integer, primary_key=True),
    Column('transaction_id', String(40), nullable=False), Column('action', String(20), nullable=False),
    Column('created_at', String(40), nullable=False), Column('actor', String(100), nullable=False))

def now():
    return datetime.now(timezone.utc).isoformat()

@bp.before_request
def require_admin():
    if session.get('is_admin') is not True:
        return redirect('/admin/login?next=/admin/transactions')

def log(conn, record_id, action):
    conn.execute(insert(events).values(transaction_id=record_id, action=action, created_at=now(), actor=session.get('admin_username', 'admin')))

@bp.route('', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        kind = request.form.get('kind')
        try:
            amount = Decimal(request.form.get('amount', ''))
            if not amount.is_finite() or amount <= 0 or amount > 1000000 or amount.as_tuple().exponent < -2:
                raise ValueError()
        except (InvalidOperation, ValueError):
            abort(400, 'Enter a positive amount with at most two decimal places.')
        if not description or len(description) > 500 or kind not in ('income', 'expense', 'refund'):
            abort(400, 'Enter a description and a valid transaction type.')
        record_id = secrets.token_hex(16)
        with get_engine().begin() as conn:
            conn.execute(insert(records).values(id=record_id, description=description, amount_cents=int(amount*100), kind=kind, created_at=now()))
            log(conn, record_id, 'created')
        flash('Transaction recorded. This does not charge or refund a customer.', 'success')
        return redirect('/admin/transactions')
    deleted = request.args.get('deleted') == '1'
    with get_engine().connect() as conn:
        rows = conn.execute(select(records).where(records.c.deleted_at.is_not(None) if deleted else records.c.deleted_at.is_(None)).order_by(records.c.created_at.desc())).mappings().all()
    totals = {kind: sum(row['amount_cents'] for row in rows if row['kind'] == kind) for kind in ('income', 'expense', 'refund')}
    totals['net'] = totals['income'] - totals['expense'] - totals['refund']
    return render_template('transactions.html', records=rows, deleted=deleted, totals=totals)

@bp.post('/<record_id>/delete')
def delete(record_id):
    with get_engine().begin() as conn:
        result = conn.execute(update(records).where(records.c.id == record_id, records.c.deleted_at.is_(None)).values(deleted_at=now()))
        if result.rowcount != 1:
            abort(404)
        log(conn, record_id, 'deleted')
    flash('Transaction moved to deleted records. You can restore it.', 'success')
    return redirect('/admin/transactions')

@bp.post('/<record_id>/restore')
def restore(record_id):
    with get_engine().begin() as conn:
        result = conn.execute(update(records).where(records.c.id == record_id, records.c.deleted_at.is_not(None)).values(deleted_at=None))
        if result.rowcount != 1:
            abort(404)
        log(conn, record_id, 'restored')
    return redirect('/admin/transactions')

@bp.get('/export.csv')
def export():
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['id', 'created_at', 'description', 'type', 'amount_usd'])
    with get_engine().connect() as conn:
        for row in conn.execute(select(records).where(records.c.deleted_at.is_(None))).mappings():
            description = row['description']
            if description.lstrip().startswith(('=', '+', '-', '@')):
                description = "'" + description
            writer.writerow([row['id'],row['created_at'],description,row['kind'],f"{row['amount_cents']/100:.2f}"])
    return Response(out.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=revive-transactions.csv','Cache-Control':'no-store'})

def register_transactions(app):
    app.register_blueprint(bp)
    @app.cli.command('init-transactions')
    def init_transactions():
        metadata.create_all(get_engine())
        print('Transaction tables created. Existing repair records preserved.')

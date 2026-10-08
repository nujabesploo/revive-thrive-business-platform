import os
import re
import secrets
from datetime import datetime, date
from functools import wraps
import smtplib
import requests
from email.message import EmailMessage
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify, session
from config import Config
from database import get_db_connection, init_db, init_db_app
from media import init_media_app, media_url
from transactions import register_transactions
from video_catalog import REPAIR_VIDEOS, PROMO_VIDEOS
from notifications import initialize as init_notifications, enqueue
from repair_catalog import DEVICE_TYPES, REPAIR_SERVICES
from repair_tracking import issue_tracking_code, lookup_tracking_code

app = Flask(__name__)
load_dotenv()
app.config.from_object(Config)
Config.init_app(app)

# Notification / credentials
BUSINESS_EMAIL = os.getenv("BUSINESS_EMAIL") or "tifealli28@gmail.com"
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

init_db_app(app)
init_media_app(app)
register_transactions(app)

def csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']

@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy'] = "frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'"
    if request.path.startswith(('/admin', '/ticket', '/status', '/inventory', '/track', '/success', '/api/v1/repair-status')) or session.get('is_admin'):
        response.headers['Cache-Control'] = 'no-store'
    if os.getenv('APP_ENV') == 'production' and request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response

@app.before_request
def verify_csrf():
    if request.method == 'POST':
        expected = session.get('csrf_token', '')
        supplied = request.form.get('csrf_token', '')
        if not expected or not secrets.compare_digest(expected, supplied):
            abort(400, 'Your form expired. Reload the page and try again.')

with app.app_context():
    init_db()
    init_notifications()


@app.context_processor
def inject_template_helpers():
    return {
        "media_url": media_url,
        "hero_motion_ready": os.path.isfile(os.path.join(app.static_folder, "motion", "ready.txt")),
        "is_admin_authenticated": session.get("is_admin") is True,
        "csrf_token": csrf_token,
        "device_types": DEVICE_TYPES,
        "repair_services": REPAIR_SERVICES,
    }


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if session.get("is_admin") is not True:
            flash("Please sign in as admin to access this page.", "error")
            return redirect(url_for("admin_login", next=request.path))
        return view_func(*args, **kwargs)

    return wrapped_view


def _safe_next_path(target):
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("admin")


def send_email(to_email, subject, body):
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("Email credentials missing.")
        return False

    msg = EmailMessage()
    msg["From"] = MAIL_USERNAME
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as smtp:
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.send_message(msg)
        print("Email sent.")
        return True
    except Exception as e:
        app.logger.error("Email delivery failed: %s", type(e).__name__)
        return False


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
        }, timeout=12)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            print("Telegram API did not confirm delivery.")
            return False
        print("Telegram sent.")
        return True
    except Exception as e:
        app.logger.error("Telegram delivery failed: %s", type(e).__name__)
        return False


STATUS_OPTIONS = [
    "New Request",
    "Received",
    "Diagnosing",
    "Waiting For Parts",
    "In Repair",
    "Completed",
    "Delivered",
]


def normalize_phone_number(phone):
    return re.sub(r"[^0-9]", "", phone or "")


@app.route("/")
def home():
    return render_template("home_refined.html", repair_videos=REPAIR_VIDEOS, promo_videos=PROMO_VIDEOS)


@app.route("/health")
def health():
    return {"status": "healthy", "service": "revive-thrive-tech"}, 200


@app.get("/api/v1/repair-catalog")
def repair_catalog_api():
    # Public, read-only data only. Customer records remain behind staff login.
    response = jsonify({
        "version": 1,
        "devices": list(DEVICE_TYPES),
        "services": list(REPAIR_SERVICES),
        "booking_url": url_for("book"),
        "quote_required": True,
    })
    response.headers["Cache-Control"] = "public, max-age=300"
    return response


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        form_data = {
            key: request.form.get(key, "").strip()
            for key in [
                "customer_name",
                "phone_number",
                "email",
                "device_type",
                "device_model",
                "service_needed",
                "issue_description",
                "preferred_date",
            ]
        }

        if any(len(v) > 4000 for v in form_data.values()) or len(form_data["email"]) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", form_data["email"]):
            abort(400, "Check your email address and keep field values under 4,000 characters.")

        if not all(form_data.values()):
            flash("Please complete every field before submitting your booking.", "error")
            return render_template("book.html", form=form_data)

        if form_data["device_type"] not in DEVICE_TYPES or form_data["service_needed"] not in REPAIR_SERVICES:
            flash("Choose a supported device and repair service.", "error")
            return render_template("book.html", form=form_data), 400

        try:
            appointment_date = datetime.strptime(
                form_data["preferred_date"], "%Y-%m-%d"
            ).date()

            if appointment_date < date.today():
                raise ValueError("Past date")

        except ValueError:
            flash("Please select a valid appointment date today or in the future.", "error")
            return render_template("book.html", form=form_data)

        normalized_phone = normalize_phone_number(form_data["phone_number"])
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO bookings (
                customer_name,
                email,
                phone_number,
                phone_number_normalized,
                device_type,
                device_model,
                service_needed,
                issue_description,
                preferred_date,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                form_data["customer_name"],
                form_data["email"],
                form_data["phone_number"],
                normalized_phone,
                form_data["device_type"],
                form_data["device_model"],
                form_data["service_needed"],
                form_data["issue_description"],
                form_data["preferred_date"],
                created_at,
            ),
        )

        # capture ticket id before closing connection
        ticket_id = cursor.lastrowid

        # generate human-friendly ticket code and save it
        ticket_code = f"RT-{int(ticket_id):04d}"
        try:
            cursor.execute(
            "UPDATE bookings SET ticket_code = ? WHERE id = ?",
            (ticket_code, ticket_id),
            )
        except Exception:
            pass

        tracking_code = issue_tracking_code(ticket_id)
        session["tracking_code"] = tracking_code

        # prepare notification messages
        business_message = f"""
    🔔 NEW BOOKING

    Ticket: {ticket_code}
    Customer: {form_data.get("customer_name")}
    Phone: {form_data.get("phone_number")}
    Email: {form_data.get("email")}
    Device: {form_data.get("device_type")} {form_data.get("device_model")}
    Service: {form_data.get("service_needed")}
    Issue: {form_data.get("issue_description")}
    Preferred Date: {form_data.get("preferred_date")}

    Admin: https://revivethrivetech.com/admin
    """

        customer_message = f"""
    Hi {form_data.get("customer_name")},

    Thanks for choosing Revive & Thrive Tech.

    We received your repair request. Your appointment and quote are not confirmed yet.

    Ticket: {ticket_code}
    Device: {form_data.get("device_type")} {form_data.get("device_model")}
    Service: {form_data.get("service_needed")}

    Track your repair: https://revivethrivetech.com/track
    Private tracking code: {tracking_code}
    Keep this code private. It expires after 90 days.

    We will contact you shortly with the next update so your experience feels smooth from start to finish.

    We appreciate your trust and look forward to serving you.

    - Revive & Thrive Tech
    """

        # Save alerts atomically with the booking; provider failures cannot lose them.
        enqueue(conn, 'telegram', '', 'New repair request', business_message[:3900])
        enqueue(conn, 'email', BUSINESS_EMAIL, 'New Repair Booking - Revive & Thrive Tech', business_message)
        enqueue(conn, 'email', form_data['email'], 'Your Revive & Thrive Tech Repair Request', customer_message)
        conn.commit()
        conn.close()

        flash("Repair request saved. Keep the private tracking code shown below.", "success")
        return redirect(url_for("success"))

    # Only accept supported public selections; never prefill personal data from URLs.
    selections = {}
    for key, allowed in {
        "device_type": DEVICE_TYPES,
        "service_needed": REPAIR_SERVICES,
    }.items():
        value = request.args.get(key, "")
        if value in allowed:
            selections[key] = value
    return render_template("book.html", form=selections)


@app.route("/success")
def success():
    return render_template("success.html", tracking_code=session.get("tracking_code"))


@app.route("/track", methods=["GET", "POST"])
def track_repair():
    result = None
    error = None
    if request.method == "POST":
        result = lookup_tracking_code(request.form.get("tracking_code", "").strip())
        if result is None:
            error = "We could not verify this code. Check your saved code or contact us for help."
    return render_template("track.html", repair=result, error=error)


@app.post("/api/v1/repair-status")
def repair_status_api():
    # CSRF-protected form POST keeps the private capability out of URL/access logs.
    result = lookup_tracking_code(request.form.get("tracking_code", "").strip())
    if result is None:
        return jsonify({"error": "Tracking code unavailable or expired"}), 404
    return jsonify({"repair": result})


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    next_path = _safe_next_path(request.args.get("next"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        posted_next = _safe_next_path(request.form.get("next"))

        valid_user = secrets.compare_digest(username, ADMIN_USERNAME)
        valid_pass = secrets.compare_digest(password, ADMIN_PASSWORD)

        if ADMIN_PASSWORD and ADMIN_PASSWORD != "change-me" and valid_user and valid_pass:
            session["is_admin"] = True
            session["admin_username"] = username
            flash("Admin login successful.", "success")
            return redirect(posted_next)

        flash("Invalid admin credentials.", "error")
        return render_template("admin_login.html", next_path=posted_next)

    return render_template("admin_login.html", next_path=next_path)


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("is_admin", None)
    session.pop("admin_username", None)
    flash("You have been signed out.", "success")
    return redirect(url_for("home"))


@app.route("/admin")
@admin_required
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
    bookings = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_tickets = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE status != 'Completed' AND status != 'Delivered'"
    )
    open_tickets = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'Completed' OR status = 'Delivered'"
    )
    completed_tickets = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(repair_cost) FROM bookings")
    revenue = cursor.fetchone()[0] or 0

    conn.close()

    return render_template(
        "admin.html",
        bookings=bookings,
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        completed_tickets=completed_tickets,
        revenue=revenue,
        status_options=STATUS_OPTIONS,
    )


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if len(name) > 200 or len(email) > 254 or len(message) > 4000 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            abort(400, 'Check your email address and keep your message under 4,000 characters.')

        if not (name and email and message):
            flash('Please complete all fields before sending your message.', 'error')
            return render_template('contact.html', form={'name':name, 'email':email, 'message':message})

        body = f"Contact form submission\n\nName: {name}\nEmail: {email}\n\nMessage:\n{message}"

        import time, uuid
        conn = get_db_connection()
        conn.cursor().execute('INSERT INTO contact_messages (id,name,email,message,created_at) VALUES (?,?,?,?,?)',
                     (uuid.uuid4().hex,name,email,message,time.time()))
        enqueue(conn, 'email', BUSINESS_EMAIL, 'New website message', body)
        enqueue(conn, 'telegram', '', 'New website message', body[:3900])
        conn.commit()
        flash('Your message has been saved. We will be in touch shortly.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html', form={})


@app.route('/admin/notifications')
@admin_required
def notification_status():
    conn=get_db_connection()
    pending=conn.cursor().execute('SELECT COUNT(*) FROM notification_outbox WHERE delivered_at IS NULL').fetchone()[0]
    failed=conn.cursor().execute('SELECT COUNT(*) FROM notification_outbox WHERE delivered_at IS NULL AND attempts > 0').fetchone()[0]
    messages=conn.cursor().execute('SELECT * FROM contact_messages ORDER BY created_at DESC LIMIT 100').fetchall()
    return render_template('notifications.html',pending=pending,failed=failed,messages=messages)


@app.route('/api/v1/notification-health')
@admin_required
def notification_health():
    conn=get_db_connection()
    count=conn.cursor().execute('SELECT COUNT(*) FROM notification_outbox WHERE delivered_at IS NULL').fetchone()[0]
    return jsonify(pending=count,telegram_configured=bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),email_configured=bool(MAIL_USERNAME and MAIL_PASSWORD))


@app.route("/ticket/<int:id>", methods=["GET", "POST"])
@admin_required
def ticket(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (id,))
    booking = cursor.fetchone()

    if booking is None:
        conn.close()
        abort(404)

    if request.method == "POST":
        status = request.form.get("status", booking["status"]).strip()
        repair_cost = request.form.get("repair_cost", booking["repair_cost"])
        notes = request.form.get("notes", "").strip()

        try:
            repair_cost_value = float(repair_cost) if str(repair_cost).strip() != "" else 0
        except ValueError:
            repair_cost_value = 0

        cursor.execute(
            """
            UPDATE bookings
            SET status = ?, repair_cost = ?, notes = ?
            WHERE id = ?
            """,
            (status, repair_cost_value, notes, id),
        )

        conn.commit()

        flash("Ticket updated successfully.", "success")

        cursor.execute("SELECT * FROM bookings WHERE id = ?", (id,))
        booking = cursor.fetchone()

    conn.close()

    return render_template(
        "ticket.html",
        booking=booking,
        status_options=STATUS_OPTIONS,
    )


@app.route("/status", methods=["GET", "POST"])
@admin_required
def status():
    booking = None

    if request.method == "POST":
        phone_input = request.form.get("phone", "").strip()

        if not phone_input:
            flash("Please enter a phone number to check status.", "error")
            return render_template("status.html", booking=None)

        normalized_phone = normalize_phone_number(phone_input)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM bookings WHERE phone_number_normalized = ? ORDER BY id DESC",
            (normalized_phone,),
        )

        booking = cursor.fetchone()
        conn.close()

        if booking is None:
            flash("No repair request found for that phone number. Please try again.", "error")

    return render_template("status.html", booking=booking)


@app.route("/api/bookings")
@admin_required
def api_bookings():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
    bookings = cursor.fetchall()

    conn.close()


    return jsonify({"bookings": [dict(row) for row in bookings]})


# Inventory Management Routes
@app.route("/inventory")
@admin_required
def inventory():
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM inventory WHERE 1=1"
    params = []

    if search_query:
        query += " AND item_name LIKE ?"
        params.append(f"%{search_query}%")

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    items = cursor.fetchall()

    # Dashboard stats
    cursor.execute("SELECT COUNT(*) FROM inventory")
    total_items = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventory WHERE quantity <= reorder_level")
    low_stock = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantity * cost) FROM inventory")
    total_value = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM inventory WHERE quantity = 0")
    out_of_stock = cursor.fetchone()[0]

    cursor.execute("SELECT DISTINCT category FROM inventory ORDER BY category")
    categories = [row[0] for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "inventory.html",
        items=items,
        total_items=total_items,
        low_stock=low_stock,
        total_value=total_value,
        out_of_stock=out_of_stock,
        categories=categories,
        search_query=search_query,
        category_filter=category_filter,
    )


@app.route("/inventory/add", methods=["GET", "POST"])
@admin_required
def inventory_add():
    if request.method == "POST":
        form_data = {
            key: request.form.get(key, "").strip()
            for key in [
                "item_name",
                "category",
                "quantity",
                "cost",
                "supplier",
                "reorder_level",
            ]
        }

        if not all([form_data.get("item_name"), form_data.get("category")]):
            flash("Item name and category are required.", "error")
            return render_template("inventory_add.html", form=form_data)

        try:
            quantity = int(form_data.get("quantity", 0))
            cost = float(form_data.get("cost", 0))
            reorder_level = int(form_data.get("reorder_level", 5))
        except ValueError:
            flash("Quantity, cost, and reorder level must be valid numbers.", "error")
            return render_template("inventory_add.html", form=form_data)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO inventory (item_name, category, quantity, cost, supplier, reorder_level, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                form_data["item_name"],
                form_data["category"],
                quantity,
                cost,
                form_data["supplier"],
                reorder_level,
                now,
                now,
            ),
        )

        conn.commit()
        conn.close()

        flash("Inventory item added successfully.", "success")
        return redirect(url_for("inventory"))

    return render_template("inventory_add.html", form={})


@app.route("/inventory/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def inventory_edit(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inventory WHERE id = ?", (id,))
    item = cursor.fetchone()

    if item is None:
        conn.close()
        flash("Item not found.", "error")
        return redirect(url_for("inventory"))

    if request.method == "POST":
        form_data = {
            key: request.form.get(key, "").strip()
            for key in [
                "item_name",
                "category",
                "quantity",
                "cost",
                "supplier",
                "reorder_level",
            ]
        }

        if not all([form_data.get("item_name"), form_data.get("category")]):
            flash("Item name and category are required.", "error")
            return render_template("inventory_edit.html", form=form_data, item=item)

        try:
            quantity = int(form_data.get("quantity", 0))
            cost = float(form_data.get("cost", 0))
            reorder_level = int(form_data.get("reorder_level", 5))
        except ValueError:
            flash("Quantity, cost, and reorder level must be valid numbers.", "error")
            return render_template("inventory_edit.html", form=form_data, item=item)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            UPDATE inventory
            SET item_name = ?, category = ?, quantity = ?, cost = ?, supplier = ?, reorder_level = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                form_data["item_name"],
                form_data["category"],
                quantity,
                cost,
                form_data["supplier"],
                reorder_level,
                now,
                id,
            ),
        )

        conn.commit()

        flash("Inventory item updated successfully.", "success")
        conn.close()
        return redirect(url_for("inventory"))

    conn.close()

    return render_template("inventory_edit.html", item=item, form={})


@app.route("/inventory/delete/<int:id>", methods=["POST"])
@admin_required
def inventory_delete(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM inventory WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Inventory item deleted successfully.", "success")
    return redirect(url_for("inventory"))


@app.route("/api/inventory")
@admin_required
def api_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inventory ORDER BY id DESC")
    items = cursor.fetchall()

    conn.close()

    return jsonify({"inventory": [dict(row) for row in items]})


@app.route("/api/inventory/<int:id>")
@admin_required
def api_inventory_item(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inventory WHERE id = ?", (id,))
    item = cursor.fetchone()

    conn.close()

    if item is None:
        return jsonify({"error": "Item not found"}), 404

    return jsonify(dict(item))


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500


def find_available_port(host, preferred_port=5000, max_tries=20):
    import socket

    if isinstance(preferred_port, str):
        preferred_port = int(preferred_port)

    for port in range(preferred_port, preferred_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue

    return preferred_port


if __name__ == "__main__":
    with app.app_context():
        init_db()
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    configured_port = os.environ.get("PORT", 5000)
    port = find_available_port(host, configured_port)
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    if str(configured_port) != str(port):
        print(f"Port {configured_port} is in use. Starting on available port {port} instead.")
    app.run(host=host, port=port, debug=debug_mode)

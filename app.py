import os
import re
import sqlite3
from datetime import datetime, date
import smtplib
import requests
from email.message import EmailMessage
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify

app = Flask(__name__)
load_dotenv()

# Notification / credentials
BUSINESS_EMAIL = os.getenv("BUSINESS_EMAIL")
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "revive-thrive-secret")
app.config["DATABASE"] = os.path.join(os.path.dirname(__file__), "database.db")
def send_email(to_email, subject, body):
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("Email credentials missing.")
        return

    msg = EmailMessage()
    msg["From"] = MAIL_USERNAME
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.send_message(msg)
        print("Email sent.")
    except Exception as e:
        print(f"Email failed: {e}")


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
        })
        print("Telegram sent.")
    except Exception as e:
        print(f"Telegram failed: {e}")


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


def get_db_connection():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def add_column_if_missing(cursor, table_name, column_name, column_definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [column[1] for column in cursor.fetchall()]

    if column_name not in existing_columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            device_type TEXT NOT NULL,
            device_model TEXT NOT NULL,
            service_needed TEXT NOT NULL,
            issue_description TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            status TEXT DEFAULT 'New Request',
            created_at TEXT NOT NULL
        )
        """
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "phone_number_normalized",
        "TEXT NOT NULL DEFAULT ''",
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "repair_cost",
        "REAL DEFAULT 0",
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "notes",
        "TEXT DEFAULT ''",
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "ticket_code",
        "TEXT DEFAULT ''",
    )

    cursor.execute("SELECT id, phone_number FROM bookings")
    rows = cursor.fetchall()

    for row in rows:
        normalized = normalize_phone_number(row["phone_number"])
        cursor.execute(
            "UPDATE bookings SET phone_number_normalized = ? WHERE id = ?",
            (normalized, row["id"]),
        )

    # Inventory table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            cost REAL DEFAULT 0,
            supplier TEXT,
            reorder_level INTEGER DEFAULT 5,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


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

        if not all(form_data.values()):
            flash("Please complete every field before submitting your booking.", "error")
            return render_template("book.html", form=form_data)

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
                phone_number,
                phone_number_normalized,
                device_type,
                device_model,
                service_needed,
                issue_description,
                preferred_date,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                form_data["customer_name"],
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

        conn.commit()
        conn.close()

        # prepare notification messages
        business_message = f"""
    🔔 NEW BOOKING

    Ticket: {ticket_code}
    Customer: {form_data.get("customer_name")}
    Phone: {form_data.get("phone_number")}
    Device: {form_data.get("device_type")} {form_data.get("device_model")}
    Service: {form_data.get("service_needed")}
    Issue: {form_data.get("issue_description")}
    Preferred Date: {form_data.get("preferred_date")}

    Admin: https://revivethrivetech.com/admin
    """

        customer_message = f"""
    Hi {form_data.get("customer_name")},

    Thank you for booking with Revive & Thrive Tech.

    Your repair request has been received.

    Ticket: {ticket_code}
    Device: {form_data.get("device_type")} {form_data.get("device_model")}
    Service: {form_data.get("service_needed")}

    Track your repair: https://revivethrivetech.com/status

    We will contact you shortly to confirm your appointment.

    - Revive & Thrive Tech
    """

        # Notify business via Telegram and email
        try:
            send_telegram(business_message)
        except Exception as e:
            print(f"Business telegram notify failed: {e}")

        try:
            if BUSINESS_EMAIL:
                send_email(
                    BUSINESS_EMAIL,
                    "New Repair Booking - Revive & Thrive Tech",
                    business_message,
                )
        except Exception as e:
            print(f"Business email notify failed: {e}")

        # Notify customer (email)
        try:
            customer_email = form_data.get("email") or request.form.get("email")
            if customer_email:
                send_email(
                    customer_email,
                    "Your Revive & Thrive Tech Booking Confirmation",
                    customer_message,
                )
        except Exception as e:
            print(f"Customer email notify failed: {e}")

        # (No SMS here — using email and Telegram notifications)

        flash("Repair request submitted successfully. We will contact you soon.", "success")
        return redirect(url_for("success"))

    return render_template("book.html", form={})


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/admin")
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

        if not (name and email and message):
            flash('Please complete all fields before sending your message.', 'error')
            return render_template('contact.html', form={'name':name, 'email':email, 'message':message})

        body = f"Contact form submission\n\nName: {name}\nEmail: {email}\n\nMessage:\n{message}"

        try:
            if BUSINESS_EMAIL:
                send_email(BUSINESS_EMAIL, f'Contact form: {name}', body)
            flash('Your message has been sent. We will be in touch shortly.', 'success')
            return redirect(url_for('success'))
        except Exception as e:
            print('Contact email failed:', e)
            flash('Failed to send message. Please try again later.', 'error')

    return render_template('contact.html', form={})


@app.route("/ticket/<int:id>", methods=["GET", "POST"])
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
def api_bookings():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
    bookings = cursor.fetchall()

    conn.close()


    return jsonify({"bookings": [dict(row) for row in bookings]})


# Inventory Management Routes
@app.route("/inventory")
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
def inventory_delete(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM inventory WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Inventory item deleted successfully.", "success")
    return redirect(url_for("inventory"))


@app.route("/api/inventory")
def api_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inventory ORDER BY id DESC")
    items = cursor.fetchall()

    conn.close()

    return jsonify({"inventory": [dict(row) for row in items]})


@app.route("/api/inventory/<int:id>")
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
    return "<h1>404 - Page Not Found</h1><p>The page you requested does not exist.</p>", 404


@app.errorhandler(500)
def server_error(error):
    return "<h1>500 - Server Error</h1><p>Something went wrong on the server.</p>", 500


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
    init_db()
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    configured_port = os.environ.get("PORT", 5000)
    port = find_available_port(host, configured_port)
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    if str(configured_port) != str(port):
        print(f"Port {configured_port} is in use. Starting on available port {port} instead.")
    app.run(host=host, port=port, debug=debug_mode)
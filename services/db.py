import sqlite3


def get_db_connection(database_path):
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn


def add_column_if_missing(cursor, table_name, column_name, column_definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [column[1] for column in cursor.fetchall()]
    if column_name not in existing_columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def init_db(database_path):
    conn = get_db_connection(database_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            email TEXT NOT NULL DEFAULT '',
            device_type TEXT NOT NULL,
            device_model TEXT NOT NULL,
            service_needed TEXT NOT NULL,
            issue_description TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            status TEXT DEFAULT 'New Request',
            created_at TEXT NOT NULL,
            phone_number_normalized TEXT NOT NULL DEFAULT '',
            repair_cost REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            ticket_code TEXT DEFAULT ''
        )
        """
    )

    add_column_if_missing(cursor, "bookings", "email", "TEXT NOT NULL DEFAULT ''")
    add_column_if_missing(cursor, "bookings", "phone_number_normalized", "TEXT NOT NULL DEFAULT ''")
    add_column_if_missing(cursor, "bookings", "repair_cost", "REAL DEFAULT 0")
    add_column_if_missing(cursor, "bookings", "notes", "TEXT DEFAULT ''")
    add_column_if_missing(cursor, "bookings", "ticket_code", "TEXT DEFAULT ''")

    cursor.execute("SELECT id, phone_number FROM bookings")
    rows = cursor.fetchall()
    for row in rows:
        normalized = normalize_phone_number(row["phone_number"])
        cursor.execute(
            "UPDATE bookings SET phone_number_normalized = ? WHERE id = ?",
            (normalized, row["id"]),
        )

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


def normalize_phone_number(phone):
    import re
    return re.sub(r"[^0-9]", "", phone or "")

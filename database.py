import os
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from flask import current_app, g
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine, Result
from sqlalchemy.exc import SQLAlchemyError


def _default_sqlite_url() -> str:
    """Build the default SQLite URL used when DATABASE_URL is not provided."""
    base_dir = os.path.dirname(__file__)
    return f"sqlite:///{os.path.join(base_dir, 'database.db')}"


def resolve_database_url() -> str:
    """Resolve database URL from env with SQLite fallback for local development."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return _default_sqlite_url()
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def _is_sqlite_url(database_url: str) -> bool:
    """Return True when a database URL targets SQLite."""
    return database_url.startswith("sqlite")


class ResultRow(dict):
    """Dictionary-like row that also supports integer index access."""

    def __init__(self, mapping: Dict[str, Any], ordered_keys: Sequence[str]):
        super().__init__(mapping)
        self._ordered_values = [mapping.get(key) for key in ordered_keys]

    def __getitem__(self, item: Union[int, str]) -> Any:
        if isinstance(item, int):
            return self._ordered_values[item]
        return super().__getitem__(item)


class DBCursor:
    """Cursor-like adapter that allows legacy sqlite-style query calls."""

    def __init__(self, connection: "DBConnection"):
        self.connection = connection
        self._result: Optional[Result] = None
        self.lastrowid: Optional[int] = None

    def _convert_qmarks(self, query: str, params: Union[Sequence[Any], Dict[str, Any], None]) -> Tuple[str, Dict[str, Any]]:
        if params is None:
            return query, {}

        if isinstance(params, dict):
            return query, dict(params)

        params_seq = list(params)
        if "?" not in query:
            return query, {f"p{i}": value for i, value in enumerate(params_seq)}

        converted_query = query
        converted_params: Dict[str, Any] = {}
        for i, value in enumerate(params_seq):
            key = f"p{i}"
            converted_query = converted_query.replace("?", f":{key}", 1)
            converted_params[key] = value
        return converted_query, converted_params

    def execute(self, query: str, params: Union[Sequence[Any], Dict[str, Any], None] = None) -> "DBCursor":
        converted_query, converted_params = self._convert_qmarks(query, params)
        self._result = self.connection.raw.execute(text(converted_query), converted_params)

        self.lastrowid = getattr(self._result, "lastrowid", None)
        if self.lastrowid is None and query.strip().lower().startswith("insert"):
            try:
                if self.connection.is_sqlite:
                    row = self.connection.raw.execute(text("SELECT last_insert_rowid() AS id")).mappings().first()
                else:
                    row = self.connection.raw.execute(text("SELECT LASTVAL() AS id")).mappings().first()
                if row:
                    self.lastrowid = int(row.get("id"))
            except Exception:
                self.lastrowid = None

        return self

    def fetchone(self) -> Optional[ResultRow]:
        if self._result is None:
            return None
        row = self._result.mappings().first()
        if row is None:
            return None
        mapping = dict(row)
        return ResultRow(mapping, list(mapping.keys()))

    def fetchall(self) -> List[ResultRow]:
        if self._result is None:
            return []
        rows = self._result.mappings().all()
        formatted: List[ResultRow] = []
        for row in rows:
            mapping = dict(row)
            formatted.append(ResultRow(mapping, list(mapping.keys())))
        return formatted


class DBConnection:
    """Connection wrapper that mirrors sqlite connection/cursor patterns."""

    def __init__(self, raw: Connection, is_sqlite: bool):
        self.raw = raw
        self.is_sqlite = is_sqlite

    def cursor(self) -> DBCursor:
        return DBCursor(self)

    def commit(self) -> None:
        self.raw.commit()

    def close(self) -> None:
        self.raw.close()


def get_engine() -> Engine:
    """Create or return a shared SQLAlchemy engine attached to app extensions."""
    engine = current_app.extensions.get("database_engine")
    if engine is not None:
        return engine

    database_url = current_app.config["DATABASE_URL"]
    connect_args = {"check_same_thread": False} if _is_sqlite_url(database_url) else {}
    engine = create_engine(database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
    current_app.extensions["database_engine"] = engine
    return engine


def get_db_connection() -> DBConnection:
    """Return a request-scoped database connection object."""
    if "db_connection" not in g:
        engine = get_engine()
        raw = engine.connect()
        g.db_connection = DBConnection(raw=raw, is_sqlite=_is_sqlite_url(current_app.config["DATABASE_URL"]))
    return g.db_connection


def close_db_connection(_: Optional[BaseException] = None) -> None:
    """Close connection at the end of each request."""
    db = g.pop("db_connection", None)
    if db is not None:
        db.close()


def init_db_app(app) -> None:
    """Initialize DB settings and attach teardown handling to the Flask app."""
    database_url = resolve_database_url()
    app.config["DATABASE_URL"] = database_url
    app.config["DATABASE"] = database_url
    app.teardown_appcontext(close_db_connection)


def _table_columns(cursor: DBCursor, table_name: str) -> List[str]:
    """Return current column names for a table in SQLite or PostgreSQL."""
    query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = :table_name
    """
    if cursor.connection.is_sqlite:
        query = f"PRAGMA table_info({table_name})"
        cursor.execute(query)
        rows = cursor.fetchall()
        return [row[1] for row in rows]

    cursor.execute(query, {"table_name": table_name})
    rows = cursor.fetchall()
    return [row["column_name"] for row in rows]


def add_column_if_missing(cursor: DBCursor, table_name: str, column_name: str, column_definition: str) -> None:
    """Add a column only when missing, preserving existing data."""
    existing_columns = _table_columns(cursor, table_name)
    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def _create_tables(cursor: DBCursor) -> None:
    """Create core tables with backward-compatible schema defaults."""
    if cursor.connection.is_sqlite:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                email TEXT DEFAULT '',
                device_type TEXT NOT NULL,
                device_model TEXT NOT NULL,
                service_needed TEXT NOT NULL,
                issue_description TEXT NOT NULL,
                preferred_date TEXT NOT NULL,
                status TEXT DEFAULT 'New Request',
                created_at TEXT NOT NULL,
                updated_at TEXT DEFAULT '',
                phone_number_normalized TEXT NOT NULL DEFAULT '',
                repair_cost REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                ticket_code TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                repair_type TEXT DEFAULT '',
                appointment_date TEXT DEFAULT '',
                technician TEXT DEFAULT '',
                estimated_cost REAL DEFAULT 0
            )
            """
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
                updated_at TEXT NOT NULL,
                purchase_price REAL DEFAULT 0,
                retail_price REAL DEFAULT 0,
                sku TEXT DEFAULT '',
                location TEXT DEFAULT '',
                last_updated TEXT DEFAULT ''
            )
            """
        )
    else:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id BIGSERIAL PRIMARY KEY,
                customer_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                email TEXT DEFAULT '',
                device_type TEXT NOT NULL,
                device_model TEXT NOT NULL,
                service_needed TEXT NOT NULL,
                issue_description TEXT NOT NULL,
                preferred_date TEXT NOT NULL,
                status TEXT DEFAULT 'New Request',
                created_at TEXT NOT NULL,
                updated_at TEXT DEFAULT '',
                phone_number_normalized TEXT NOT NULL DEFAULT '',
                repair_cost DOUBLE PRECISION DEFAULT 0,
                notes TEXT DEFAULT '',
                ticket_code TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                repair_type TEXT DEFAULT '',
                appointment_date TEXT DEFAULT '',
                technician TEXT DEFAULT '',
                estimated_cost DOUBLE PRECISION DEFAULT 0
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id BIGSERIAL PRIMARY KEY,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                cost DOUBLE PRECISION DEFAULT 0,
                supplier TEXT,
                reorder_level INTEGER DEFAULT 5,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                purchase_price DOUBLE PRECISION DEFAULT 0,
                retail_price DOUBLE PRECISION DEFAULT 0,
                sku TEXT DEFAULT '',
                location TEXT DEFAULT '',
                last_updated TEXT DEFAULT ''
            )
            """
        )


def _sync_missing_columns(cursor: DBCursor) -> None:
    """Ensure new production-friendly columns exist without dropping current schema."""
    booking_columns = {
        "email": "TEXT DEFAULT ''",
        "phone_number_normalized": "TEXT NOT NULL DEFAULT ''",
        "repair_cost": "REAL DEFAULT 0",
        "notes": "TEXT DEFAULT ''",
        "ticket_code": "TEXT DEFAULT ''",
        "updated_at": "TEXT DEFAULT ''",
        "phone": "TEXT DEFAULT ''",
        "repair_type": "TEXT DEFAULT ''",
        "appointment_date": "TEXT DEFAULT ''",
        "technician": "TEXT DEFAULT ''",
        "estimated_cost": "REAL DEFAULT 0",
    }

    for column_name, definition in booking_columns.items():
        add_column_if_missing(cursor, "bookings", column_name, definition)

    inventory_columns = {
        "purchase_price": "REAL DEFAULT 0",
        "retail_price": "REAL DEFAULT 0",
        "sku": "TEXT DEFAULT ''",
        "location": "TEXT DEFAULT ''",
        "last_updated": "TEXT DEFAULT ''",
    }

    for column_name, definition in inventory_columns.items():
        add_column_if_missing(cursor, "inventory", column_name, definition)


def _sync_derived_values(cursor: DBCursor) -> None:
    """Backfill normalized and compatibility fields so old routes keep working."""
    cursor.execute("SELECT id, phone_number, service_needed, preferred_date, repair_cost, created_at FROM bookings")
    rows = cursor.fetchall()

    for row in rows:
        normalized = re.sub(r"[^0-9]", "", row["phone_number"] or "")
        cursor.execute(
            """
            UPDATE bookings
            SET
                phone_number_normalized = :normalized,
                phone = COALESCE(NULLIF(phone, ''), phone_number),
                repair_type = COALESCE(NULLIF(repair_type, ''), service_needed),
                appointment_date = COALESCE(NULLIF(appointment_date, ''), preferred_date),
                estimated_cost = COALESCE(estimated_cost, repair_cost),
                updated_at = COALESCE(NULLIF(updated_at, ''), created_at)
            WHERE id = :booking_id
            """,
            {"normalized": normalized, "booking_id": row["id"]},
        )

    cursor.execute("SELECT id, updated_at, created_at FROM inventory")
    inventory_rows = cursor.fetchall()
    for row in inventory_rows:
        last_updated = row["updated_at"] or row["created_at"] or ""
        cursor.execute(
            "UPDATE inventory SET last_updated = :last_updated WHERE id = :inventory_id",
            {"last_updated": last_updated, "inventory_id": row["id"]},
        )


def _create_indexes(cursor: DBCursor) -> None:
    """Create indexes to speed up common booking and inventory lookups."""
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_phone_norm ON bookings (phone_number_normalized)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_created ON bookings (created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_appointment_date ON bookings (appointment_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_category ON inventory (category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_sku ON inventory (sku)")


def init_db() -> None:
    """Initialize schema, sync missing columns, and add indexes safely."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        _create_tables(cursor)
        _sync_missing_columns(cursor)
        _sync_derived_values(cursor)
        _create_indexes(cursor)
        conn.commit()
    except SQLAlchemyError:
        conn.raw.rollback()
        raise

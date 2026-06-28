import re
from datetime import datetime
from services.db import get_db_connection
from services.notifications import NotificationService


def normalize_phone_number(phone):
    return re.sub(r"[^0-9]", "", phone or "")


def save_booking(form_data, database_path):
    normalized_phone = normalize_phone_number(form_data["phone_number"])
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection(database_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO bookings (
            customer_name,
            phone_number,
            email,
            device_type,
            device_model,
            service_needed,
            issue_description,
            preferred_date,
            phone_number_normalized,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            form_data["customer_name"],
            form_data["phone_number"],
            form_data["email"],
            form_data["device_type"],
            form_data["device_model"],
            form_data["service_needed"],
            form_data["issue_description"],
            form_data["preferred_date"],
            normalized_phone,
            created_at,
        ),
    )

    ticket_id = cursor.lastrowid
    ticket_code = NotificationService.generate_ticket_number()

    cursor.execute(
        "UPDATE bookings SET ticket_code = ? WHERE id = ?",
        (ticket_code, ticket_id),
    )

    conn.commit()
    conn.close()

    return ticket_code

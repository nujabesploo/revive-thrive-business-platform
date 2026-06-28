from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from services.booking_service import save_booking
from services.notifications import NotificationService
from services.email_service import send_email
from config import BUSINESS_EMAIL

booking_bp = Blueprint("booking", __name__)


@booking_bp.route("/book", methods=["GET", "POST"])
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

        ticket_code = save_booking(form_data, current_app.config["DATABASE"])
        form_data["ticket_number"] = ticket_code

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

        try:
            NotificationService.send_telegram_alert(form_data)
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

        try:
            customer_email = form_data.get("email")
            if customer_email:
                send_email(
                    customer_email,
                    "Your Revive & Thrive Tech Booking Confirmation",
                    customer_message,
                )
        except Exception as e:
            print(f"Customer email notify failed: {e}")

        flash("Repair request submitted successfully. We will contact you soon.", "success")
        return redirect(url_for("success"))

    return render_template("book.html", form={})

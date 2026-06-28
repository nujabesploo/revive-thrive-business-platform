import os
import smtplib
from email.message import EmailMessage
from config import MAIL_USERNAME, MAIL_PASSWORD


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

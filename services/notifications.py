import os
import requests
from datetime import datetime


class NotificationService:

    @staticmethod
    def generate_ticket_number():
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"RT-{timestamp}"

    @staticmethod
    def send_telegram_alert(booking):

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token or not chat_id:
            print("Telegram configuration missing.")
            return

        message = f"""
🔔 NEW REPAIR BOOKING

Ticket:
{booking['ticket_number']}

Customer:
{booking['customer_name']}

Phone:
{booking['phone_number']}

Email:
{booking['email']}

Device:
{booking['device_type']}

Issue:
{booking['issue_description']}

Preferred Date:
{booking['preferred_date']}
"""

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": message
            }
        )

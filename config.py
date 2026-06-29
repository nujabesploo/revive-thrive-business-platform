import os
from dotenv import load_dotenv

load_dotenv()

BUSINESS_EMAIL = os.getenv("BUSINESS_EMAIL")
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "revive-thrive-assets")
S3_BASE_URL = os.getenv("S3_BASE_URL", "").rstrip("/")

STATUS_OPTIONS = [
    "New Request",
    "Received",
    "Diagnosing",
    "Waiting For Parts",
    "In Repair",
    "Completed",
    "Delivered",
]

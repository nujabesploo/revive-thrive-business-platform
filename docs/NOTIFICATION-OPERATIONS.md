# Booking and contact delivery
Bookings, customer email, contact messages and queued alerts persist in the database. Booking+alerts commit together. A single systemd worker retries email/Telegram with exponential backoff capped at one hour. Successful provider submissions are not retried. Provider acceptance does not guarantee inbox receipt. A crash after provider acceptance but before database acknowledgement may cause a duplicate.

Admin dashboard → Messages & alert delivery shows persisted website messages and pending alert counts. Authenticated GET /api/v1/notification-health exposes configuration booleans and queue count, never credentials. No public booking list is exposed.

Production currently needs notification credentials. Existing values are in the owner's local project .env; never paste them into chat/logs/Git. On the server run `venv/bin/python scripts/configure_notifications.py` and enter MAIL_USERNAME, Gmail app password in MAIL_PASSWORD, TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID using hidden prompts. Use the existing bot; owner must start its chat. Restart `revive-thrive`, then `revive-notifications.service`. Send a clearly marked owner-only test after configuration. Do not replay old customer notifications blindly.

Phone call links remain +13476715335. Telegram/email apps can notify the owner's phone. SMS is NOT configured and needs a provider, approved cost and messaging setup. Existing AWS instance alarms are separate; pending SNS email confirmation and an external HTTP monitor remain necessary for whole-server/network outages. A queue on this server cannot alert while the whole server is unreachable.

New reported booking has not been found in the inspected database (latest record August1). Ask for reference/time and verify production request logs, without exposing customer data. Do not claim a lost booking was recovered.

# Customer experience release — October 7, 2026

## Implemented
- Shared dark palette, less compressed headings, highlighted booking navigation.
- Device/repair finder on home and services. Server-rendered options remain usable without JavaScript or if the catalog API fails.
- GET /api/v1/repair-catalog: public device/service options; no customer data. Cache: 300 seconds.
- POST /api/v1/repair-status: form-encoded tracking_code and session csrf_token. Returns only repair reference and status. Invalid/expired codes return the same generic 404; CSRF failures return 400. No-store responses.
- /track offers the same lookup as an HTML form. New bookings issue a signed 90-day code on the confirmation screen and in the existing customer-email notification. Codes are bearer capabilities: keep private. No names, phone numbers, staff notes, device contents or repair cost are exposed by tracking. Codes are not placed in URLs. Existing bookings need staff contact; this release does not backfill codes.
- Staff bookings/inventory remain authenticated. No database schema change or new dependencies.

## Verification
Run PYTHON_BIN=venv/bin/python bash scripts/check.sh and venv/bin/python scripts/test_customer_api.py.
Customer tests use a disposable database and mock all email/Telegram sends.
Eight public routes checked at desktop and 390px mobile for overflow. Booking selector handoff verified in browser.
No live customer booking was submitted for testing. Production notification delivery is not independently verified.

## Still required for customer accounts and history
1. Choose identity method/provider and verify outbound email delivery. Recommended starting design: verified email sign-in links, short expiry, single-use tokens, server-side rate limits and session revocation.
2. Store verified customer ownership separately from booking contact information. Do not attach historical bookings based only on an unverified email or phone number.
3. Add recovery, account deletion/export and session management; test cross-customer authorization before launch.
No customer-account feature is claimed complete in this release.

## Advertising package (draft; no paid campaign launched)
Campaign: Opening October 20 at Grow DeSoto Market Place, booth #701.
Headline: Cracked screen? Let’s find your next step.
Body: Meet Tife at Revive & Thrive Tech. Tell us your device and what happened. We’ll confirm the repair options, price and timing before work begins. Opening October 20 in DeSoto.
CTA: Request a repair.
Destination: https://revivethrivetech.com/book
Creative: existing real screen-repair video first; existing brand films as supporting creative.
Needed before paid launch: separate daily/lifetime ad cap, dates, platform and service area approval. No unsupported discounts, warranty or turnaround claims. No new tracking pixels added.

## Operations follow-up
Confirmed private tracking codes are not individually revocable in this initial implementation; expiration is 90 days. Key rotation invalidates all codes and sessions. If per-ticket revocation becomes necessary, add server-side token hashes/revocation records before expanding the returned data.
Keep the existing hosting budget; no additional AWS service or paid API required for this release.

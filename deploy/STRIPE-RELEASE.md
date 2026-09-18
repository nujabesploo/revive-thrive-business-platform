# Stripe checkout release requirements

Provider confirmed by owner: Stripe. No live payment integration or charge is enabled yet.

Use Stripe-hosted Checkout so this app never receives raw card numbers or CVCs. Server-side approved prices/quotes must determine the amount, not browser input. Store a payment record separately from manual bookkeeping and connect it to the repair ticket. Persist the Checkout Session ID and an idempotency key before retrying requests. Verify webhook signatures against the raw body and deduplicate event IDs. Only mark paid when provider payment status confirms payment; a redirect is not proof. Keep refunds auditable and require authenticated owner authorization.

Owner decision pending: deposit amount, full approved repair quote, or fixed-price services. Stripe account access and webhook signing credentials must be configured privately. Do not paste secrets into chat or commit them. Test successful, declined, abandoned, duplicate and delayed payments in Stripe test mode before live activation. Telegram alerts should include a reference and status, not customer notes or payment credentials.

Official references:
- https://docs.stripe.com/payments/checkout
- https://docs.stripe.com/webhooks

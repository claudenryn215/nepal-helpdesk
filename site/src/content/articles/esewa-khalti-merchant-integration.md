---
title: eSewa / Khalti Payment Gateway Integration for Small Businesses (2026)
description: 'Integrate eSewa or Khalti payment gateway for your Nepal business: requirements, KYC documents, webhook setup, testing, and going live — without a developer.'
keywords:
- esewa merchant registration
- khalti payment gateway integration
- esewa api integration nepal
- payment gateway nepal business
- खल्ती व्यापारी
tags:
- esewa
- khalti
- merchant
- payment-gateway
niche: fintech
sources:
- https://merchant.esewa.com.np
- https://admin.khalti.com
summary:
- problem: Merchant application rejected
  cause: Incomplete business documents
  fix: Submit PAN, company registration, and bank account details
- problem: Sandbox works, live fails
  cause: Live keys not activated or domain mismatch
  fix: Register the exact live domain; use the live secret key
- problem: Payment success not reaching your site
  cause: Webhook/callback URL misconfigured
  fix: Verify callback URL and signature verification code
publishedAt: '2026-08-01T13:54:01.000Z'
lastVerified: '2026-08-06T13:54:01.000Z'
confidence: kb
related: [esewa-kyc-verification-error, khalti-wallet-topup-error]
trendingScore: 60.0
---

## Quick Answers

| Problem | Common cause | Fix |
| --- | --- | --- |
| Merchant application rejected | Incomplete business documents | Submit PAN, company registration, and bank account details |
| Sandbox works, live fails | Live keys not activated or domain mismatch | Register the exact live domain; use the live secret key |
| Payment success not reaching your site | Webhook/callback URL misconfigured | Verify callback URL and signature verification code |


## Step 1: Check business requirements

1. You need a registered business: PAN/VAT certificate or company registration.
2. A bank account in the business name (or verified owner name).
3. A live website or app with a working checkout page.


<div class="ad-slot" style="min-height:90px">Ad Slot — in-article 1 — advertising placeholder</div>


## Step 2: Register as a merchant

1. eSewa: apply at merchant.esewa.com.np with business documents.
2. Khalti: apply at admin.khalti.com with the same documents.
3. Both review within a few working days; expect a verification call.

## Step 3: Get your keys and set up the sandbox

1. eSewa provides a Merchant Code and Secret Key.
2. Khalti provides a Public Key and Secret Key.
3. Start integration against the sandbox (test) environment.

## Step 4: Integrate the payment link or API

1. No-code option: generate a payment link/QR from the merchant dashboard.
2. API option: add the checkout call on your site with the merchant keys.
3. Use the official documentation for the exact endpoint and fields.

## Step 5: Configure the callback/webhook

1. Set the callback URL where the wallet sends the result after payment.
2. On the server, verify the signature with your secret key before marking paid.
3. Test a real (small) payment in sandbox mode first.

## Step 6: Go live

1. Confirm the live domain in the merchant dashboard — mismatches break live payments.
2. Switch keys from sandbox to live and run one real transaction.
3. Keep transaction logs for refunds and disputes.

## Troubleshooting

| Problem | Cause | Fix |
| --- | --- | --- |
| Sandbox payment works but live URL fails | Live keys or domain not activated | Check merchant dashboard for live status; re-enter domain exactly |
| Customer paid but order not updated | Callback not verified | Check server logs; ensure callback path is public (no auth wall) |
| Refund API errors | Wrong transaction reference | Use the wallet transaction ID from the dashboard, not your order ID |



<div class="ad-slot" style="min-height:90px">Ad Slot — in-article 2 — advertising placeholder</div>


## FAQ

**Q:** Does eSewa/Khalti charge merchant fees?

**A:** Yes, each gateway has per-transaction fees and settlement cycles — check the merchant agreement.

**Q:** How long does settlement take?

**A:** Typically 1–2 working days after successful transaction matching.

**Q:** Do I need a developer for integration?

**A:** For payment links and QR, no. For API checkout, basic web development is needed.

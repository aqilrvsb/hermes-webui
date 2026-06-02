---
name: new-client
description: Scaffold a new marketing client/brand project — create its workspace and bind it (via AGENTS.md) to its Zernio ad account, FB/IG page, WhatsApp report recipient, target ROAS and brand voice. Use when onboarding a new client or brand.
---
# New Client / Brand Scaffold

Each client is self-contained: one workspace + its own ad account, page, and WhatsApp report channel, recorded in `AGENTS.md`.

Steps:
1. Ask for: client name, which Zernio ad account (run `ads_list_ad_accounts`), FB/IG page, WhatsApp number/contact to send reports to, target ROAS, monthly budget, brand voice.
2. Ensure `/workspace/<client>` exists (Add Space, or mkdir).
3. Write `/workspace/<client>/AGENTS.md`:
   ```
   # Client: <name>
   ad_account_id: <zernio ad account id>
   fb_page: <id/name>
   whatsapp_report_to: <number or contact>
   target_roas: <e.g. 2.0>
   monthly_budget: <e.g. RM3000>
   brand_voice: <short description>
   # The marketer agent must use ONLY this ad account + page + WhatsApp channel for this client.
   ```
4. Confirm. Never spend or go live without explicit approval.

Never mix one client's ad account/page/budget with another's.

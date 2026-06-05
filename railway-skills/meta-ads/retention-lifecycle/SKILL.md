---
name: retention-lifecycle
description: Post-purchase retention, onboarding, churn-save, upsell, and win-back for the PeningBot + PeningLab subscriptions (LTV is the other half of profit for a SaaS). Use to keep paying customers, raise LTV, and reactivate lapsed ones via zernio messaging / whacenter broadcasts.
---

# Retention & Lifecycle (the other half of profit)

Acquisition without retention = a leaky bucket. For a subscription SaaS, **LTV drives whether you can afford
to scale ads** (see `measurement`: LGP:CAC ≥ 3:1). This agent owns the *existing customer* — distinct from the
CRO agent (pre-purchase) and the Ad Builder (acquisition).

## Onboarding (first 7 days = churn risk window)
- **PeningBot:** the moment of value = first auto-closing. Nudge new users to (1) scan QR, (2) paste a prompt
  template, (3) see the first auto-reply within 5 min. WhatsApp them a quick-start + "dah ada closing pertama?"
- **PeningLab:** value = first batch generated. Nudge to paste a TikTok Shop link → generate 10 videos → post.
  WhatsApp "dah generate video pertama? Ada masalah?"

## Churn-save (catch the signals)
- Signals: credit balance untouched 7+ days (PeningLab), no AI replies (PeningBot), no logins, plan near expiry
  without renewal. → trigger a win-back message/offer before they lapse.
- Renewal reminders before expiry (both bill monthly via CHIP). Make renewing one tap.

## Upsell / expansion (raise LTV)
- **PeningBot:** Starter→Pro/Premium (more devices), + Ads Reporting add-on (RM12/slot). Trigger when they hit
  device limits or run multiple ad accounts.
- **PeningLab:** Standard→Pro (BEST SELLER), Pro→Premium when credits run low frequently. Frame as cost-per-video.

## Win-back (lapsed customers)
Broadcast to expired/cancelled with a festive offer or new-feature hook (Raya/CNY/payday/11.11). BM/Manglish,
modest. Use zernio messaging (`messages_*`, `broadcasts_*`) and whacenter for WhatsApp sends.

## Output & guardrails
Write actions/segments to `_shared/retention_<brand>.json`. Feed LTV signals to the Analyst/Head of Growth so
ad spend decisions reflect real LTV. Modest, halal-safe copy; never spam; respect opt-out. Don't mix brands.

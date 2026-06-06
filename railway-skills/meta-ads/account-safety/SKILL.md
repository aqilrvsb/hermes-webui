---
name: account-safety
description: Meta ad-account health — setup done right, ban prevention, disabled-account recovery (Ben Heath's method), special ad categories, and the pixel/tracking traps. Use when setting up a new account, before scaling, or when an account/page gets restricted or write-locked.
---

# Account safety & health (2026)

Bans and write-locks are routine even for good advertisers (Heath's agency loses several accounts/month and
"nearly always" recovers them). Build for resilience.

## Setup done right (prevents most problems)
- Build in **Business Manager** (business.facebook.com): Business Portfolio → Page → Ad Account → Pixel, and
  assign yourself **full control** on each. **Never boost from the app** (adds a 30% Apple tax, worse control).
- Complete **full Business Verification** (and domain verification) → far fewer bans, easier appeals.
- **2FA** on; gradual spend ramp on new accounts; don't run flagged content.
- **Special Ad Categories:** if the ad touches credit/finance, employment, housing, or social/political
  issues, you MUST declare it — failing to tick can disable the account. PeningBot/PeningLab (business SaaS) is
  normally NOT a special category — leave blank unless a specific offer triggers it.

## Content that triggers bans (avoid)
- Scam-y / get-rich claims ("untung besar", "cepat kaya", guaranteed income), health/financial overpromises,
  before/after that implies guaranteed results, personal-attribute targeting ("you, diabetic?"). Keep MY copy
  modest and halal-safe (see `copywriting`). Aggressive unsupported landing-page claims also spike CPMs (Sam).

## Pixel / tracking traps (these look like "Meta hates me" but are self-inflicted)
- A purchase/lead event firing on **page load** tells Meta everyone converts → it floods bots/spam. "Better a
  pixel that doesn't know how to convert than one that thinks it does when it doesn't." Verify with **Meta
  Pixel Helper**; gate the event to the real action (see `measurement`, `website-sales-funnel`).
- Optimize for the real event from day one (don't believe the "warm up the pixel with traffic first" myth).

## Disabled-account recovery — Ben Heath's 4-step method
1. **Request Review** (in-account) → escalates to a human; can take weeks. Say you didn't break the rules; if
   you did slightly, admit it + promise compliance.
2. **facebook.com/business/help → AI Business Assistant** → run its steps, then "I've tried those, what next?"
   to get routed to a **live human agent** (can reinstate on the spot; if you get a weak agent, close + retry).
3. **Contact your Meta rep** (higher-spend accounts get better reps).
4. **Business verification** (sometimes appeals only succeed after verifying).
- Won't recover **severe** violations (banned products, discriminatory ads). **Avoid** paid "recovery services"
  and **never buy "seasoned"/aged agency accounts** (ToS violation, more likely to be banned).

## Write-lock note (relevant to this account)
A specific ad account can hit a Meta **write-lock** (e.g. subcode 3858385) — you can read but not create/edit.
Don't fight it; resolve the live working account (do a tiny PAUSED smoke-test to confirm write access before
building) and use the recovery steps above for the locked one. Always resolve the live account each run.

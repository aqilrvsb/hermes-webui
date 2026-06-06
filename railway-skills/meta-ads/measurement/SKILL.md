---
name: measurement
description: How to measure Meta ads correctly in 2026 — judge by profit/GPT not ROAS, incremental & new-customer attribution, the 2026 click-through→engage-through change, CAPI/event-quality, audience-segment reporting, and signal optimization. Use to set up tracking, pick the optimization event, read results, and decide kill/scale by real economics.
---

# Measurement (2026) — measure profit, not vanity

The hard 2026 lesson (CT, Sam, Jordan, Media Ninja): **reported ROAS lies.** Judge by real economics and feed
Meta the highest-quality signal you can.

## Track these, not ROAS
- **GPT = Gross Profit per Transaction** (CT's north star) — build as a custom column: AOV − COGS − fees.
  Decision metric = **did total profit volume (revenue − ad spend) go UP?** A 2x-ROAS / RM120-AOV ad can
  out-earn a 4x / RM40 one. "You can't pay bills with fractions."
- **New-customer CAC, not blended ROAS** (Jordan). Blended hides bad acquisition (returning buyers who'd buy
  anyway). Only scale when *new-customer* economics are on target.
- **For SaaS (website subscription):** cost-per-**Purchase** (paid sub) + its LTV. Max allowable CAC = the
  margin/LTV break-even gate. LTV needs a window (30/60/90-day) — fire a re-bill event so Meta sees high-LTV cohorts.

## Incremental attribution (the 2026 tool — Sam)
Columns → Compare attribution settings → **Incremental attribution** = conversions that happened *because of*
Meta, not last-click steals. Expect a big drop vs default 7-day-click/1-day-view (Sam: 379→206; prospecting
108→29). **Evaluate prospecting creative on incremental**; scale by incremental ROAS. Real incrementality =
reaching people *before* they shop (CT's GEM: buy a bike → push helmet ads before they search).

## The 2026 attribution change (Heath, Tiana) — must brief every client
- "Click-through" now = a **real LINK click only**. Old social/engagement clicks (likes, comments, shares,
  "see more") + **≥5-sec video views** reclassified as **"engage-through"** (1-day window). 7-day click→buy
  window unchanged.
- Effect: **reported conversions DROP with no real change** (video ads hit hardest). Reconcile against
  back-end/CRM. **Stop comparing pre/post-change campaigns** (measured differently). Check rollout: Ad Set →
  Attribution model → "Show more" → "engage-through".
- **For website sales:** the Purchase fires via Pixel + CAPI on the site — reconcile Meta's reported numbers
  vs the site's real subscriptions (Supabase/CRM truth).

## Event quality > ad volume (CT) — the signal lever
"Scale the QUALITY of events you track, not the volume of ads." Fire a custom event for the specific outcome
and optimize to it:
- **Optimize for the deepest real event**, never traffic/ATC/"messaging started" (Sam, Media Ninja, all).
- **New-customer event:** create a custom "new customer" conversion (Zapier/Elevar) and set the ad-set
  optimization event to it → new-customer share rises to 85–95%, CAC falls (CT, Teekus case $463k→$1M/mo with
  LESS spend by optimizing the right event).
- **Purchase event:** fire the server-side **Purchase** via CAPI (deduped by payment id) valued at the real
  subscription price (see `website-sales-funnel`) so Meta runs a true purchase-optimized campaign.
- **Subscriptions:** fire an event on **re-bill** so Meta builds a high-LTV cohort.

## CAPI / pixel gut-check (Sam)
Events Manager → purchase/lead event → compare blue (browser) vs green (server) lines. Expect **server ~10%
higher** than browser; a 10–20%+ gap = broken tracking, fix it. Then confirm server events ≈ actual
Shopify/CRM/WhatsApp count. Verify firing with **Meta Pixel Helper**; use **Test Events** for new events.
Trap: a purchase/lead event firing on page-load tells Meta everyone converts → it floods bots. (Heath, Andy)

## Audience-segment reporting (Media Ninja, Heath)
Advertising Settings → Audience Segments: label **Existing customers** (purchasers) + **Engaged** (visitors/
ATC/leads). Two payoffs: (1) break ROAS down by new/engaged/existing (else 100% shows "unknown"); (2) gives
Meta a better signal for which new users convert → lifts new-customer ROAS. A "6.36 blended" often hides
"6.10 new" once engaged/existing are stripped out.

## Cross-platform / hygiene
- **UTMs** when running multiple channels (each platform over-claims +1 per sale) → CRM/Shopify is source of truth.
- **Turn OFF Andromeda AI creative enhancements** when you need a clean read on whether the *concept* won
  (they alter photo/music/copy and usually drop performance) — Media Ninja.
- Frequency check: retargeting monthly frequency > ~8 = overspending, cut. Prospecting frequency ~1 = reaching new.
- Don't trust the last 2–3 days of any 30-day window; judge on 7- and 30-day.

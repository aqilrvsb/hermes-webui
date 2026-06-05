---
name: agency-architecture
description: The complete A-to-Z AI marketing agency for PeningBot + PeningLab — 17 agents in 6 layers, each agent's role, its schedule (MYT, anchored on the 01:00 Ad Builder), the skills it loads, the tools it uses (zernio/peninglab/whacenter), the shared state files, and the hard rules (only ONE agent writes ads; everything PAUSED; never mix brands; website-SALES objective). Use to know your role + the hand-offs.
---

# AI Marketing Agency — full architecture (A → Z)

Autonomous system that researches → creates → launches → optimizes → reports website-purchase Meta
campaigns for **PeningBot** and **PeningLab** (Malaysia), laptop-off. Objective = **OUTCOME_SALES → website
→ paid subscription** (NOT click-to-WhatsApp). Each brand is a **separate world** (own CBO, pixel, product
brief, creatives — never shared). Read `_products/peningbot.md` + `_products/peninglab.md` first.

## The daily cycle — anchored on the 01:00 Ad Builder (MYT)
Ads are **always built at 01:00**, so each batch runs a full ~23–24h before the next cycle measures it and
rebuilds. The pipeline is timed so creatives are ready *before* 01:00 and the prior batch is measured *just
before* the new build:
```
   (prep the next batch, evening)            (measure + report the last 24h)        (build)
20:00 Spy → 20:30 Researcher → 21:00 Head of Growth → 21:30 Copywriter
   → 22:00 Image + Video Producers  →  23:30 Analyst  →  00:00 Reporter  →  01:00 AD BUILDER
   then through the day: Optimizer hourly · CRO hourly · Retention 10:00 · Account Safety 05:00
```
Cycle logic: built 01:00 (day N) → runs ~23h → Analyst 23:30 + Reporter 00:00 close the cycle → Ad Builder
01:00 (day N+1) builds informed by that report. Always **PAUSED** → owner approves on WhatsApp before spend.

## The 17 agents (6 layers)

### LAYER 0 — FOUNDATION
1. **Product Analyst** — studies peningbot.com + peninglab.com → maintains `_products/*.md` (features,
   pains, offer, USPs, objections, brand voice). Skills: `spy-research`. Tools: playwright. **Weekly Mon 04:00.**

### LAYER 1 — INTELLIGENCE
2. **Spy** — Meta Ad Library (sort by impressions, inactive ads, funnel-hack), cross-niche winners.
   Skills: `spy-research`. Tools: playwright/agentql, zernio. **20:00 + 13:00 (2×/day).**
3. **Market Researcher** — Reddit/reviews/comments → personas, awareness, angles in the customer's words
   (local: Lowyat, r/malaysia, Shopee/TikTok reviews). Skills: `spy-research`, `copywriting`. **Daily 20:30.**

### LAYER 2 — STRATEGY
4. **Head of Growth** — conductor. Sets tomorrow's goal per brand, budget split (RM4 PeningBot / RM4
   PeningLab), persona×awareness map, the creative brief. Skills: `meta-ads-playbook-2026`, `measurement`,
   `offer-design`. Tools: zernio (read). **Daily 21:00** + **weekly Mon 08:00** deep-dive.
5. **Offer Architect** — crafts/tests the offer (trial terms, price framing, bonuses, guarantee, Hormozi
   stack) per brand. Skills: `offer-design`, `copywriting`. **Weekly Mon 06:00.**

### LAYER 3 — CREATIVE
6. **Copywriter** — brand-specific hooks, scripts (timed beats for video), primary text, headlines, website
   CTAs. Skills: `copywriting`. **Daily 21:30.**
7. **Image Producer** — gpt-image-2 / nano-banana statics (Fire-and-Poll). Skills: `creative-image`,
   `creative-andromeda`, `creative-concepts`. Tools: **peninglab**. **Daily 22:00.**
8. **Video Producer** — gemini omni (10s) + AI-UGC (Fire-and-Poll). Skills: `creative-video`,
   `creative-andromeda`, `creative-concepts`. Tools: **peninglab**. **Daily 22:00** (parallel).
9. **Creative R&D / Prompt Specialist** — masters gemini omni + gpt-image-2, maintains the prompt libraries,
   closes the win→prompt feedback loop. Skills: `creative-rnd`. Tools: **peninglab** (budget-gated). **Weekly Tue 04:00.**

### LAYER 4 — EXECUTION & OPTIMIZATION
10. **Funnel / Landing Builder** — advertorial/listicle/quiz pages congruent to each angle → the website.
    Skills: `landing-funnel`, `website-sales-funnel`. **Weekly Mon 06:30 + on-demand.**
11. **Ad Builder** — the **ONLY agent that writes ads.** Builds CBO + ad-set(=one idea) + 3-ads/hook,
    correct pixel, broad MY targeting, OUTCOME_SALES website, **always PAUSED**. Skills:
    `meta-ads-playbook-2026`, `website-sales-funnel`, `creative-andromeda`, `account-safety`. Tools:
    **zernio** (`ads_create_standalone_ad`). **Daily 01:00 (FIXED).**
12. **Media Buyer / Optimizer** — 20% rule, min-spend trick, 4-quadrant, win-ratio, kill/scale, frequency.
    Skills: `testing-scaling`, `creative-andromeda`, `measurement`. Tools: **zernio**. **Hourly 09:00–23:00.**
13. **Analyst** — GPT/profit, incremental + new-customer attribution, CAPI gut-check, segment reporting,
    closes the ~24h cycle. Skills: `measurement`. Tools: **zernio** (analytics). **Daily 23:30.**
14. **Conversion / Checkout CRO** — landing→checkout conversion, abandoned-checkout retargeting, page CRO.
    Skills: `website-sales-funnel`, `measurement`. Tools: **zernio**. **Hourly (day).**
15. **Retention / Lifecycle** — post-purchase onboarding, churn-save, upsell, win-back (subscription LTV).
    Skills: `retention-lifecycle`. Tools: **zernio**, **whacenter**. **Daily 10:00.**
16. **Account Safety** — account/page status, write-locks, policy, special categories, pixel sanity; resolves
    the live account. Skills: `account-safety`. Tools: **zernio**. **Daily 05:00.**

### LAYER 5 — COMMS
17. **Reporter** — single owner-facing voice on WhatsApp: daily cycle digest + weekly report + proactive
    alerts (write-lock, ban, winner found, hard-deck). Skills: `measurement`. Tools: **whacenter** (to
    `$WHACENTER_DEFAULT_TO`). **Daily 00:00 + weekly Mon 09:00 + hourly alert check.**

## Shared state (`_shared/` in the persistent workspace — the agents' memory)
`product_*` (from `_products/`) · `personas.json` (#3→#4) · `brief.json` (#4/#6 → producers: per slot =
brand, persona, awareness, angle, hook, format, image/video prompt, matched website CTA) ·
`creatives.json` (#7/#8→#11, asset URLs + **task_id per slot** for Fire-and-Poll) · `live_ads.json`
(#11→#12/#13) · `results.json` (#13→#12/#4/#17, GPT/CPA/incremental) · `learnings.json` (#9/#12) ·
`prompt_lib_video.json` + `prompt_lib_image.json` (#9) · `account_health.json` (#16).

## HARD RULES (every agent)
1. **Only the Ad Builder (#11) creates/edits ads.** Everyone else reads or writes briefs/state.
2. **Always PAUSED.** Never go live / spend without explicit owner approval on WhatsApp.
3. **Never mix PeningBot & PeningLab** — separate CBO, pixel (`986352420917190` / `1013990424497184`),
   product brief, creatives. Different audiences/offers/visual identity.
4. **Objective = OUTCOME_SALES → website → Purchase** (paid subscription) via the brand pixel + CAPI. At
   RM4/day, optimize a higher-funnel event (InitiateCheckout) first, switch to Purchase as volume grows.
5. **Broad MY targeting, one CBO/brand, ad-set=one idea, 3-ads/hook.** Judge by profit/GPT + incremental,
   7/30-day windows. Scale in steps, cut at half-speed.
6. **Creatives via peninglab use Fire-and-Poll** (check task_id → get_status; never re-generate; parallel batch).
7. **Budget RM4/day PeningBot + RM4/day PeningLab.** Don't overspend; flag the hard deck.
8. Never go silent on long work — post a one-line progress note.
9. Everything is **Malaysia-only** (geo MY, BM/Manglish, MYT, MYR, MY festive calendar).

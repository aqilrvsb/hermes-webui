---
name: testing-scaling
description: The 2026 testing + scaling system (Sam Piliero, Nick Theriot, CT the Disrupter, Media Ninja, Ben Heath, Jordan Hayes). Covers how to test inside one CBO (min-spend trick), the 7-day judging window, kill/scale criteria, win ratio, the 4-quadrant ad classifier, the 20% scaling rule, marginal scaling, and learning-phase rules. Use to launch tests, decide what to kill/scale, and set budgets.
---

# Testing & Scaling (2026)

Everything happens inside **one CBO per goal** (no separate test/scale campaigns — Nick). New idea = new ad
set; let Meta allocate. Judge on **7-day and 30-day** windows, NEVER 24h/hourly ("Facebook is consistently
inconsistent").

## The CBO testing problem + fix (Sam, Media Ninja)
New ad sets often won't spend under CBO (Meta feeds proven winners). **Fix: set ad-set minimum daily spend =
1× your target CPA** (e.g. CPA RM50 → RM50/day min) for **7 days**, then **REMOVE the minimum** so CBO spends
freely. Forces ~1/8 of budget into testing; winners hit baseline fast, losers spend the floor then fade.
- **Low-budget cap:** the minimum must never exceed **20% of total budget** (RM100/day → max RM20 min).

## How to judge a test
- **Delivery first (CT):** did the test ad earn spend? No spend = dead on arrival → it was never going to work,
  discard (don't force spend). A real winner takes a **top-5 spend slot within 24–48h** (Jordan).
- **7-day rule (Nick):** after 7 days, keep if no negative impact; turn OFF if it's below the top-3 spenders
  AND has a worse CPA. Record **creative learnings on EVERY ad** (winner + loser) — the 15-min stare ritual.
- **Spend gates before judging (Andy):** <RM ~150-equiv spent → don't touch (not enough data); RM150–200 →
  enough to judge vs break-even / target CPL; way over target after RM200+ → kill.
- **CTR / hook gate:** CTR ~1%+ and hook rate ≥30% before you blame anything downstream.
- **Diagnostic (Nick, relative to YOUR campaign average, not absolute):** high cost-per-link-click vs avg =
  **creative** problem; normal CPC but bad CPA = **landing/greeting** problem (often ad↔destination mismatch).
- **Heath's decision tree:** 0 conv → offer; few conv + low CTR → creative; few conv + high CTR → landing/offer
  post-click; many conv but unprofitable → pricing/model; many + profitable → scale.

## Win ratio (the creative KPI — Jordan)
% of produced ads that become scalable winners. **Target 15–20%**, and MAINTAIN it as volume grows (adding
volume that halves win-ratio nets fewer winners). Test big things first: **Offer → Angle → Style → Hook → copy**.

## The 4-quadrant ad classifier (Media Ninja) — sort ads by spend
1. **High spend / low CPA = winner** → never pause; duplicate into more surfaces to force more spend.
2. **High spend / avg CPA = "supportive ad"** (top-of-funnel feeder shown to most people) → **do nothing**.
   Pausing it collapses the account — "the biggest mistake you can make."
3. **High spend / high CPA** → if CTR is well above account avg, PAUSE (high-engagement junk traffic).
4. **Low spend / low CPA** → let run, don't force spend, don't pause winners to feed it.
5. **Low spend / high CPA** → pause immediately.

## Scaling (steps, never spikes — cut at half-speed)
- **The 20% rule (Nick — run once/day at campaign level):** hit yesterday's KPI → **+20% budget**, repeat.
  Missed KPI → waited ≥3 days? No → wait. Yes + at your **"hard deck"** (max you can lose over 30 days, tied to
  cash) → don't cut. Yes + not at hard deck → **−20%**.
- **Marginal automated rule (CT/Heath):** if trailing-7-day CPA < target, raise budget a small % (e.g. 3–5%),
  capped by margin (so even zero new sales stays profitable); pair a −3%/day rule above an upper CPA with a
  floor budget. Use percentage, run midnight–1am, add an impressions guard (≥2,000) + a max-budget ceiling.
- **Manual stepped (Heath):** bigger % at low budgets, smaller % high (e.g. 50→100→150→200→300→…→1,000 = +20%);
  wait **5–10 days** between steps; never change an ad set >1×/5–7 days (re-enters learning ~1–2 days).
- **Aggressive (Sam):** when WELL above goal (target 2x, hitting 4–5x), scale **+100% or more** — "strike while
  the iron is hot." **Ignore the learning phase when scaling UP** (it only penalises pausing).
- **Never turn off >20% of spend in one day** (that's a budget change). Cut at **half the speed** you scaled;
  optimize (kill worst) BEFORE cutting budget; after a cut wait 48–72h.

## Learning phase
Exits at ~**50 optimization events/week/ad set** (often 20–40). You CAN be profitable while Learning Limited —
fix offer/creative/consolidation, don't panic-spend. Consolidate ad sets or optimize a higher-funnel event if
you genuinely can't hit volume.

## Break-even gate (always compute first — Andy)
Max allowable CPA = margin per sale (for a subscription: the per-sub margin / LTV gate). Judge every ad
against this, not vanity ROAS.

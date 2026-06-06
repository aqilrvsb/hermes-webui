---
name: meta-ads-playbook-2026
description: The master Meta/Facebook ads strategy brain for 2026 — the consensus of 9 top media buyers (Ben Heath, Sam Piliero, North Digital, Tiana Asperjan, Andy Stauring, Jordan Hayes, CT the Disrupter, Media Ninja, Nick Theriot), ~110 videos. Use for EVERY ad decision: account structure, targeting, funnel, the non-negotiable rules. Product = PeningBot + PeningLab (WhatsApp-automation SaaS, Malaysia), run as click-to-WhatsApp (CTWA).
---

# Meta Ads Playbook 2026 — the marketing brain

Synthesized from 9 elite 2026 sources. Where they AGREE, it's law. Products = **PeningBot** (B2B WhatsApp-
automation SaaS for SME owners) + **PeningLab** (AI UGC-content studio for TikTok Shop sellers) — both
Malaysia, both sold as a **paid subscription on the website** (objective = SALES, drive to the site to buy —
NOT click-to-WhatsApp). Read the per-brand briefs in `_products/peningbot.md` + `_products/peninglab.md`
FIRST; they're different products — never share creative. Always resolve the live ad account first.
Sister skills: `creative-andromeda`, `copywriting`, `creative-image`, `creative-video`, `testing-scaling`,
`spy-research`, `website-sales-funnel`, `measurement`, `account-safety`, `offer-design`, `landing-funnel`,
`retention-lifecycle`, `creative-rnd`, `agency-architecture`.

## The 12 laws (near-unanimous across all 9 creators)

1. **CONSOLIDATE. One CBO campaign per business goal.** A "business goal" = one country/market, one
   product/offer, or one storefront. Budget at campaign level (Advantage Campaign Budget), let Meta
   allocate. One campaign at 50 conv/wk beats two at 25 (no fragmentation, exits learning faster).
   → PeningBot = its own CBO; PeningLab = its own CBO. (Heath, Sam, North, Jordan, CT, Media Ninja, Nick)

2. **NEVER duplicate a campaign to scale.** Identical campaigns to the same users = **auction overlap**
   (breaks Meta's per-user impression-sequence plan). Add ad sets to the existing campaign instead. (Heath, CT)

3. **BROAD targeting always. The CREATIVE is the targeting.** No interest stacking, no lookalikes for
   prospecting. You build an ad for an avatar; Meta finds the people. Only hard inputs: **geo + age + gender**
   (and language for MY). Over-narrow audiences are the #1 reason ads won't spend. (ALL 9)

4. **Ad set = ONE idea/avatar/angle.** New creative idea → new ad set in the same CBO (number them
   sequentially: 100, 101, 102…). Don't mix avatars in one ad set. (Sam "packs", Jordan, Nick, Media Ninja)

5. **Hybrid warm+cold — no separate retargeting campaign** for prospecting. Custom audiences are now
   "suggestions"; a "cold" set spends on warm anyway and auto-reallocates. (Heath, CT) *(Light broad
   retargeting/retention is OK as a small separate budget once you have a buyer pool — Media Ninja 85/10/5.)*

6. **Creative is the #1 lever and the only thing you truly control.** Post-**Andromeda**, Meta is a
   matchmaker on the visual/copy. Diversity > volume, but you still need real volume. (ALL — see `creative-andromeda`)

7. **Optimize for the DEEPEST real event, never a cheap proxy.** Always optimize for the true outcome
   (Purchase / qualified Lead), never traffic/ATC/"messaging started". For CTWA: optimize for a **qualified
   WhatsApp conversation** and send it back via CAPI as the conversion. (Sam, CT, Nick, Media Ninja — see `measurement`)

8. **Judge by PROFIT and INCREMENTALITY, not reported ROAS.** Track GPT (gross profit per transaction) /
   new-customer CAC, not blended ROAS. A 2x-ROAS ad can out-earn a 4x one. (CT, Jordan, Sam — see `measurement`)

9. **Funnel mix by awareness ≈ 50–70% TOF / 20–30% MOF / 10–20% BOF.** TOF = unsung heavy lifter; BOF gets
   the credit. Build a *team* of ads, each with a funnel job. (Tiana — see `copywriting`)

10. **Test big first: Offer → Angle → Style → Hook → (last) copy/colour.** Most "no sales" = offer problem,
    not targeting ("Meta's targeting is great now"). Expect most tests to fail; one winner pays for many. (Heath, all)

11. **Scale in steps, never spike.** ~20% up once/day when KPI is hit (Nick's 20% rule); or 20–30% every
    3–7 days; or a marginal automated rule (raise % only while CPA < target, capped by margin). Bigger % at
    low budgets, smaller % high. Cut at HALF the speed you scaled. (Heath, Sam, Jordan, CT, Nick — see `testing-scaling`)

12. **Stability wins. Don't day-trade the account.** Don't reset learning, don't react to one bad day, batch
    changes (≤ once/7 days per ad set), judge on 7- and 30-day windows — never hourly/24h. (CT, Nick, Heath)

## 2026 platform facts you must know
- **Andromeda / Advantage+ AI** runs delivery; the advertiser's job is creative + offer + signal quality.
- **Attribution changed:** "click-through" now = a real **link click only**; old social/engagement clicks +
  5-sec video views are reclassified as **"engage-through"** (1-day window). Expect REPORTED conversions to
  drop with no real change — reconcile against back-end/CRM; don't compare pre/post-change campaigns. (Heath, Tiana)
- **Learning phase** exits at ~**50 optimization events/week** per ad set (often 20–40 in practice). You can
  be profitable while "Learning Limited" — fix offer/creative/consolidation, don't panic-spend.
- **Value Rules** (up to 10): keep targeting broad but bid DOWN on weak segments (or up on a starved
  high-value one). Needs your real numbers (LTV, close rate). (Heath, Sam, CT)
- **Flexible ads were killed** → use single image/video + Advantage+ "Flex media"; check crops before publish.

## Brand bindings (LOCKED)
- **PeningBot pixel** `986352420917190` · **PeningLab pixel** `1013990424497184` (pass the right one as
  `promoted_object.pixelId` + a purchase `customEventType`).
- Objective = **OUTCOME_SALES → website → Purchase** (Pixel + CAPI, customEventType PURCHASE). NOT CTWA.
- Budget = RM 4/day per brand, hard-capped (resolve account live).
- One brand = one CBO = its own creatives. **Never mix PeningBot and PeningLab.** Launch **LIVE (ACTIVE), capped RM4/day** — only the Ad Builder creates/closes ads.

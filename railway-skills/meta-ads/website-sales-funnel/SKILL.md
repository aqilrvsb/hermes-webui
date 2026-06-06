---
name: website-sales-funnel
description: The website-purchase funnel for 2026 (objective = SALES, drive to the site to buy a paid subscription) for PeningBot + PeningLab. Covers campaign setup (OUTCOME_SALES, website conversion, Pixel + CAPI), the ad→landing→checkout→purchase flow, optimizing a higher-funnel event at low budget, and abandoned-checkout retargeting. Use to set up campaigns and design the on-site conversion path.
---

# Website-Sales Funnel (objective = SALES, not WhatsApp)

The funnel: **Ad → website (peningbot.com / peninglab.com) → checkout → paid subscription (Purchase).** The
purchase is a CHIP subscription; the Pixel + CAPI fire on it. NOT click-to-WhatsApp.

## Campaign setup (via zernio `ads_create_standalone_ad`)
- **Objective OUTCOME_SALES**, conversion location **Website**.
- `promoted_object.pixelId` = **PeningBot `986352420917190`** or **PeningLab `1013990424497184`** + a purchase
  `customEventType`. CAPI sends server-side Purchase (deduped: PeningBot by payment_id, PeningLab by
  `purchase-<payment.id>`).
- **One CBO per brand**, broad Malaysia targeting (geo MY, age, gender, language), Advantage+ placements,
  ad-set = one idea, 3-ads/hook. **Launch LIVE (status ACTIVE), each campaign capped RM4/day** — no PAUSE,
  no approval gate; the RM4/day cap is the safety. (Only the Ad Builder creates/closes ads.)

## Optimization event at low budget (RM4/day) — important
RM4/day yields too few *purchases* to optimize Purchase directly (can't hit ~50/wk learning volume). So:
1. **Start by optimizing a higher-funnel event** that fires often enough: **InitiateCheckout** / begin-checkout
   (or ViewContent/AddToCart if available). This gives Meta signal.
2. **Switch to Purchase** once purchase volume supports it (as budget/conversions grow). (Heath/CT's rule.)
Always send the real Purchase back via CAPI regardless, so attribution + value-optimization improve over time.

## The on-site path (must be congruent — see `landing-funnel`)
- Match the landing page to the ad's awareness stage: unaware→advertorial/quiz, problem-aware→listicle,
  product-aware→the product/pricing page. The page's hook must continue the ad's hook (congruence lifts CR).
- PeningBot site beats: pain mockup (unread WhatsApps) → cost calculator → transformation → testimonials →
  "Mula Sekarang" → CHIP. PeningLab: hero "10 video/3 minit" → 4-card pricing (Pro = BEST SELLER) → proof.
- Keep it simple (Nick: white-bg/black-text listicles + quiz funnels win). CTA continuity ad→page→checkout.

## Diagnose leaks (relative to your campaign average)
- Clicks but no checkouts → landing/offer problem (or ad↔page mismatch).
- Checkouts but no purchase → pricing/checkout friction (CHIP step, trust).
- Purchases but unprofitable → offer/AOV (upsell, higher tier) — see `measurement`, `offer-design`.

## Abandoned-checkout retargeting (the Conversion/Checkout-CRO agent)
Build a small broad-retargeting audience of InitiateCheckout-no-Purchase (last 7–14 days) and run a BOF
offer/urgency creative. Don't over-spend at RM4/day; keep it lean. (Avoid heavy cart-abandon retargeting —
those already said no; broad retargeting self-regenerates — CT.)

## Malaysia specifics
CHIP payment (FPX/DuitNow/TNG/Boost/card) — works only for MY. BM/Manglish on page. Festive pushes
(Raya/CNY/Merdeka/payday/11.11). Trust signals (real testimonials, founder, specific numbers). No "free trial"
language (neither product offers one).

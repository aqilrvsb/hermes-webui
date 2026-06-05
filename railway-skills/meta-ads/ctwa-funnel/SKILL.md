---
name: ctwa-funnel
description: Click-to-WhatsApp (CTWA) funnel design for Malaysia/SEA — campaign setup, the ad→WhatsApp greeting congruence rule, lead-quality gating, sending qualified-lead events back via CAPI so Meta optimizes for buyers, qualifying flow, and follow-up. Use to design the PeningBot/PeningLab WhatsApp funnel end-to-end and the WhatsApp opening/qualifying messages.
---

# Click-to-WhatsApp (CTWA) funnel — Malaysia

CTWA is cheap and preferred in WhatsApp-heavy markets. Heath names India/Brazil (Malaysia's peers): "you can
sell anything on WhatsApp there, low-ticket included" — so CTWA fits both PeningBot and PeningLab. The SaaS's
edge: it OWNS the WhatsApp conversation, so it can qualify leads and feed quality signal back to Meta.

## Campaign setup
- Objective **OUTCOME_SALES / Engagement** with **WhatsApp** as the conversion location (CTWA). Pass the
  brand pixel (PeningBot `986352420917190` / PeningLab `1013990424497184`) + a purchase `customEventType`.
- **One CBO per brand**, broad targeting (geo=Malaysia, age, gender, language), Advantage+ placements,
  ad-set = one idea, 3-ads/hook (see `meta-ads-playbook-2026`, `creative-andromeda`).
- Build via the **zernio** MCP `ads_create_ctwa_ad` (full campaign+adset+ad in one call), always **PAUSED** first.

## The funnel A→Z
Ad (hook) → click → **WhatsApp greeting** → qualifying questions → offer → close → follow-up.
1. **Greeting congruence (critical):** the first auto-reply MUST mirror the ad's hook/angle. Problem-aware ad
   ("Penat balas WhatsApp?") → greeting names that exact problem + the promise. Write ad + greeting as a pair.
   Congruence is a top conversion lever (Jordan: 1.6%→3.6%).
2. **Qualify with friction = your quality dial (North Digital):** ask 1 qualifying question, watch a week, add
   another until quality stabilises. Custom short-answer (typing) filters junk better than buttons. A CTWA
   lead is already phone-verified (real WhatsApp number) — pitch that as higher quality than FB lead forms.
3. **Offer + close:** free 7-day trial (no card), auto-reply 24/7, time-saved. Human-escalation for hot leads.
4. **Follow-up:** broadcast/sequence to non-closers (whacenter / zernio messaging). Response speed matters most.

## Lead-quality GATING (the #1 transferable idea — Nick, CT, North, Media Ninja)
Most "leads" have zero intent and look identical to Meta. **Only fire the conversion event for QUALIFIED
conversations.** Nick gates B2B leads <$30k/mo to a no-event thank-you page so Meta optimizes only toward
qualified leads (25% close rate). For CTWA:
- Define "qualified" (e.g. answered budget/intent, is an SME owner, asked about pricing).
- **Send the qualified conversation back as the conversion via CAPI** — `ads_send_conversions` /
  `whatsapp_send_whats_app_conversion`, valued at your **average lead value** so you can run a true
  purchase-optimized campaign. This is exactly the "optimize for the deepest event" law (see `measurement`).
- Don't fire on "messaging started" — that's the cheap proxy that floods you with tyre-kickers.

## Optimization
- Optimize for **qualified conversations**, not raw chats. Proxy/leading metrics: cost-per-conversation-started
  and cost-per-qualified-reply (your ATC/IC equivalents) predict cost-per-closed before the sale lands.
- Reconcile **Meta-reported vs your WhatsApp/CRM data** daily (CTWA conversions live in WhatsApp). Use the
  2026 attribution note: a click into WhatsApp now counts as a proper link-click conversion, but reported
  numbers shift — don't compare pre/post-change (see `measurement`).
- Auto-score conversation quality from the chat text (Claude classifier) → a weekly "% qualified" metric
  (productized version of North's manual call-listening). This is the killer dashboard for MY SMEs.

## Landing-page congruence (when a page precedes WhatsApp)
Match the page to awareness: unaware → advertorial/quiz; problem-aware → listicle; product-aware → product
page. Winning formats (Nick): **listicles** (us-vs-them) and **quiz funnels** (HeyFlow); dead-simple white-bg
/black-text. Often best to send straight to WhatsApp (no friction) for low-ticket MY leads.

## Malaysia specifics
BM/Manglish copy; festive pushes (Raya/CNY/payday/11.11); FPX/bank-transfer norms; trust is everything
(real testimonials, founder ads, "dibalas dalam 5 minit"). Spam-wary market → look human, not AI.

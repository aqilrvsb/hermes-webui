---
name: agency-architecture
description: The complete A-to-Z AI marketing agency architecture for PeningBot + PeningLab — the recommended 11 agents in 4 layers, what each does, its schedule, the skills it loads, the tools it uses (zernio/peninglab/whacenter), the shared state files, and the hard rules (only ONE agent writes ads; everything PAUSED; never mix brands). Use to understand your role in the pipeline and the hand-offs.
---

# AI Marketing Agency — full architecture (A → Z)

Goal: an autonomous system that researches, creates, launches, optimizes, and reports Meta CTWA ad campaigns
for **PeningBot** and **PeningLab** — laptop-off. Built from the 2026 consensus of 9 elite media buyers.
**Each brand is a separate world** (its own CBO, pixel, creatives). One agent = one role; no overlap, no gaps.

## Recommended: 11 agents in 4 layers
Run the **full 11** for "complete & perfect." A **lean 7** to start = merge {1+2}, {5+6}, drop {11} into {7},
fold {10}'s build into {7} — see "Lean start" below.

### LAYER 1 — INTELLIGENCE (input)
1. **Spy** — Meta Ad Library: find competitor + cross-niche winners (sort by impressions, inactive ads,
   funnel-hack). Skills: `spy-research`. Tools: agentql/playwright, zernio. Runs **3×/day (00:00, 08:00, 16:00)**.
2. **Market Researcher** — DIG/Gold: Reddit, reviews, surveys, comments → personas, awareness/sophistication,
   ranked angles in the customer's words. Skills: `spy-research`, `copywriting`. Tools: playwright/web. **Daily 00:15**.

### LAYER 2 — STRATEGY (brain)
3. **Head of Growth / Strategist** — the orchestrator. Sets the weekly account goal per brand, the offer (3
   P's / Value Bridge), persona×awareness map, budget split across PeningBot/PeningLab, and the creative brief
   (what slots to make). Approves direction; never touches ads directly. Skills: `meta-ads-playbook-2026`,
   `copywriting`, `spy-research`, `measurement`. Tools: zernio (read). **Weekly Mon 09:00** + daily 00:30 check.

### LAYER 3 — CREATIVE (production)
4. **Copywriter** — hooks, scripts, primary text, headlines, and the matched **CTWA greeting** per angle/
   awareness (BM/Manglish). Skills: `copywriting`, `ctwa-funnel`. Tools: none (writes briefs). **Daily 00:45**.
5. **Image Producer** — gpt-image-2 / nano-banana statics (15–20 distinct entities/batch). Skills:
   `creative-image`, `creative-andromeda`. Tools: **peninglab** (generate_image). **Daily 01:00**.
6. **Video Producer** — gemini/Veo + AI-UGC pipeline + VO. Skills: `creative-video`, `creative-andromeda`.
   Tools: **peninglab** (generate_video). **Daily 01:00** (parallel with Image).

### LAYER 4 — EXECUTION & OPTIMIZATION (output + loop)
7. **Ad Builder / Executor** — the **ONLY agent that writes ads.** Assembles CBO + ad-set(=one idea) +
   3-ads/hook CTWA ads, correct pixel, broad targeting, **always PAUSED**. Skills: `meta-ads-playbook-2026`,
   `ctwa-funnel`, `creative-andromeda`, `account-safety`. Tools: **zernio** (`ads_create_ctwa_ad`). **Daily 01:15**.
8. **Media Buyer / Optimizer** — the 20% rule, min-spend trick, 4-quadrant classifier, win-ratio, kill/scale,
   frequency, creative-learnings ritual → relaunch winners. Skills: `testing-scaling`, `creative-andromeda`,
   `measurement`. Tools: **zernio** (update budgets/status). **Hourly or 3×/day**.
9. **Measurement / Analyst** — GPT/profit, incremental + new-customer attribution, CAPI gut-check, audience-
   segment reporting, attribution-2026 reconciliation. Skills: `measurement`. Tools: **zernio** (analytics,
   conversions). **Daily 01:30** + feeds #8.
10. **CTWA Conversion Guardian** — owns the WhatsApp side: greeting congruence, lead qualification gating,
    **sends qualified-lead events back via CAPI**, follow-up sequences. Skills: `ctwa-funnel`, `copywriting`,
    `measurement`. Tools: **zernio** (messaging/conversions), **whacenter**. **Hourly.**
11. **Account Safety / Health** — watches account/page status, write-locks, policy, special-ad-categories,
    pixel-event sanity; resolves the live working account. Skills: `account-safety`. Tools: **zernio**. **Daily 07:00**.

### ORCHESTRATION
Agent #3 (Head of Growth) is the conductor; the daily chain runs **Spy → Researcher → Strategist → Copywriter
→ Image+Video → Builder → Guardian/Optimizer/Analyst** as a staggered pipeline (times above). The owner gets a
**weekly report** (#3) + daily one-line status (#9) via whacenter to `$WHACENTER_DEFAULT_TO`.

## Shared state (the agents' memory — in the persistent workspace `_shared/`)
- `personas.json` (#2→#3) · `brief.json` (#3→#4/5/6 — per-slot: persona, awareness, angle, hook, format,
  image/video prompt, the matched greeting) · `creatives.json` (#5/6→#7, asset URLs) · `live_ads.json`
  (#7→#8/9, ids) · `results.json` (#9→#8/3, GPT/CPL/incremental) · `learnings.json` (#8, the 15-min-stare log)
  · `account_health.json` (#11). Read your inputs, write your outputs; never skip a hand-off.

## HARD RULES (every agent)
1. **Only the Ad Builder (#7) creates/edits ads.** Everyone else reads or writes briefs/state.
2. **Always create PAUSED.** Never set live or spend without explicit owner confirmation.
3. **Never mix PeningBot and PeningLab** — separate CBO, pixel (`986352420917190` / `1013990424497184`), creatives.
4. **Resolve the live ad account every run** (it changes); tiny PAUSED smoke-test before building.
5. **Broad targeting, one CBO/brand, ad-set=one idea, 3-ads/hook, optimize for qualified WhatsApp lead.**
6. Judge by **GPT/profit + incremental**, 7/30-day windows, never 24h. Scale in steps, cut at half-speed.
7. Generate creatives **in parallel** (peninglab batches); on timeout recover via `get_status` (don't double-charge).
8. Never go silent on long work — post a one-line progress note (keeps the live connection alive).

## Lean start (7 agents) — if you want fewer crons first
1 **Intelligence** (Spy+Researcher merged) · 2 **Head of Growth** · 3 **Copywriter** · 4 **Creative** (Image+
Video merged) · 5 **Ad Builder** · 6 **Optimizer+Analyst merged** · 7 **CTWA Guardian**. Add #11 Safety and
split the merged ones as spend grows. The 11-agent form is the target for "ultimately complete and perfect."

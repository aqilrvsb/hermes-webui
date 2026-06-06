---
name: agency-architecture
description: The complete AI marketing agency for PeningBot + PeningLab — 12 agents in 5 departments, each agent's role + schedule (MYT) + tools + the _shared READ→WRITE hand-offs, the nightly decision cycle, and the hard rules (Strategy is the spend gate; only the Ad Builder touches ads; launch LIVE capped RM4/day; website-SALES objective). Read to know your role + the flow.
---

# AI Marketing Agency — 12 agents · 5 departments

Autonomous website-purchase Meta system for **PeningBot** and **PeningLab** (Malaysia), laptop-off.
Objective = **OUTCOME_SALES → website → paid subscription** (pixel + CAPI, customEventType PURCHASE).
Each brand is a separate world (own CBO, pixel, creatives — never mix). Read `_products/<brand>.md` first.

## The nightly cycle (MYT) — decide on clean 24h data, then build
```
☀ 08:00  INTELLIGENCE watches today's running ads + gathers intel  ─┐ (feeds tonight's decision)
                                                                     │
🌙 00:00  STRATEGY  → reads 24h data, decides per ad CLOSE/MAINTAIN, briefs N new (angle+format+copy)
   00:30  CREATIVE  → makes ONLY the N briefed (gpt-image-2 + gemini omni)
   01:15  EXECUTION → Ad Builder closes the losers + launches the new LIVE (capped RM4/day)
   01:45  COMMS     → Reporter WhatsApps the owner what happened
```
Ads built ~01:15 run all day → measured at 08:00 → judged on full 24h at 00:00 → rebuilt. **Strategy is the
single trigger for spend** (both ad budget AND creative generation). No brief → Creative/Execution do nothing.

## The 12 agents

### 🔎 INTELLIGENCE — watch + gather (08:00; recommend only, never touch ads)
1. **Spy** `01` 08:00 — Meta Ad Library (MY, by impressions) for competitor + cross-niche winners. Tool: **playwright** + web search. → `spy_<brand>`
2. **Market Researcher** `02` 08:10 — Reddit/Lowyat/reviews → personas + angles in customer words. Tool: **playwright** + web. → `personas_<brand>`, `angles_<brand>`
3. **Analyst** `12` 08:20 — spend/sales/ROAS/GPT/CPA/frequency + CAPI parity. Tool: **zernio** analytics. → `results_<brand>`
4. **Optimizer** `11` 08:30 — flag each ad CLOSE/MAINTAIN/SCALE (7-day lens). Tool: **zernio** (read). → `learnings_<brand>` (recommendations)
5. **CRO** `13` 08:40 — landing→checkout→purchase conversion + abandoned checkout. Tool: **zernio** + playwright. → `cro_<brand>`

### 🧠 STRATEGY — the spend gate (00:00)
6. **Head of Growth** `03` 00:00 — pull live 24h + read Intelligence → decide per ad CLOSE/MAINTAIN, brief N new (each: angle, persona, awareness, format video/image, concept, copy direction). Tools: **zernio** + skills. → `brief_<brand>` = {close[], maintain[], new[]}
7. **Offer Architect** `04` Mon 00:00 — refresh each offer (value-stack, price framing, guarantee). → `offer_<brand>`

### 🎨 CREATIVE — execute the brief ONLY (budget-matched)
8. **Copywriter** `05` 00:30 — exact BM copy + 10s scripts per brief direction. → fills `brief_<brand>`
9. **Image Producer** `06` 00:45 — **peninglab gpt-image-2** (Fire-and-Poll), only the briefed image slots. → `creatives_<brand>`
10. **Video Producer** `07` 00:45 — **peninglab gemini omni** (10s, Fire-and-Poll), only the briefed video slots. → `creatives_<brand>`

### 🚀 EXECUTION — the only hand on the ads (01:15)
11. **Ad Builder** `10` 01:15 — CLOSE the losers Strategy flagged + LAUNCH the new **LIVE**: one CBO/brand (OUTCOME_SALES, website, pixel + PURCHASE + CAPI, broad MY, ad-set=one idea, 3-ads/hook, RM4/day, **ACTIVE**). Tool: **zernio** `ads_create_standalone_ad` + `update_ad_campaign_status`. → `live_ads_<brand>`

### 📨 COMMS (01:45)
12. **Reporter** `16` 01:45 — one WhatsApp digest (closed / launched / spend / sales / GPT / top creative). Tool: **whacenter**.

## Shared state (`_shared/` on the volume — the agents' memory)
`spy_<brand>` (#1) · `personas/angles_<brand>` (#2) · `results_<brand>` (#12) · `learnings_<brand>` (#11) ·
`cro_<brand>` (#13) · `offer_<brand>` (#7) · `brief_<brand>` (#3→#5→#6/#7) · `creatives_<brand>` (#6/#7→#10) ·
`live_ads_<brand>` (#10). Plus product truth in `_products/<brand>.md`.

## HARD RULES
1. **Strategy (#3) is the spend gate** — Creative + Execution act ONLY on its brief. No brief = nothing made/launched.
2. **Only the Ad Builder (#10) touches ads.** Intelligence/Strategy only read + recommend + decide.
3. **Launch LIVE, status ACTIVE, capped RM4/day per brand** — no PAUSE, no approval gate; the cap is the safety.
4. **Objective = OUTCOME_SALES → website → Purchase** (brand pixel `986352420917190` / `1013990424497184` + CAPI).
5. **Never mix PeningBot & PeningLab** — separate CBO, pixel, creatives, voice.
6. **Creatives via peninglab use Fire-and-Poll** (task_id → get_status; never re-generate; batch parallel).
7. **Decide on clean 24h data** (midnight), not half-day noise. Malaysia-only (geo MY, BM/Manglish, MYT, MYR).
8. Never go silent on long work — post a one-line progress note.

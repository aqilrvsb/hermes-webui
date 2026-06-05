---
name: agency-8-agents
description: The 8-agent autonomous Meta-ads "office" structure for PeningBot/PeningLab — what each scheduled agent (cron) does, when, what it reads/writes, and the no-overlap/no-gap rules. Use to set up / run the 8 marketing cron agents and to know which agent owns which job.
---

# The 8-Agent Marketing Agency (Hermes)

A complete Meta-ads team. **One job per agent, one shared workspace file per agent, no
overlap, no gaps** — covering the full funnel intel → create → launch → optimize → convert
→ report → strategize. Every agent reads the **meta-ads-playbook-2026** skill + the
workspace `AGENTS.md` first; uses the **zernio** MCP for ads, **whatsapp-whacenter** for
reports, and a creative generator for images/video. **Only Agent 5 writes/edits Meta ads.**

State lives in the workspace `_shared/` (each agent writes its own file; the next reads it):
`swipe-file.md, intel.md, decisions.json, brief.json, creatives.json, actions.log, funnel.md, plan.json`.

| # | Agent (cron) | Schedule (MYT → UTC cron) | Job | Writes ads? |
|---|---|---|---|---|
| 1 | **Competitor Spy** | 00:00/08:00/16:00 → `0 16,0,8 * * *` | mine Meta Ads Library (sort by impressions), keep a growing swipe-file, "steal/counter" notes | ❌ |
| 2 | **Performance Analyst** | 00:15 → `15 16 * * *` | read yesterday's metrics, kill losers (CTR<0.3% & 0 conv after RM1), slots to fill, scale candidates, diagnose | ❌ |
| 3 | **Creative Strategist** | 00:30 → `30 16 * * *` | a UNIQUE brief per slot (Andromeda diversity + MY copy) → brief.json | ❌ |
| 4 | **Creative Producer** | 00:45 → `45 16 * * *` | generate the images/videos (MY-localized) → creatives.json | ❌ |
| 5 | **Ad Executor** | 01:00 → `0 17 * * *` | pause losers · apply scale targets · create new ads PAUSED (consolidated CBO+ad set, correct pixel) | ✅ ONLY |
| 6 | **Conversion Guardian** | 01:15 → `15 17 * * *` | leads→sales / offer / landing / account-health; flag the #1 fix → funnel.md | ❌ |
| 7 | **Reporter** | 01:30 → `30 17 * * *` | WhatsApp digest (spend, sales, launched-pending-approval, fix) via whacenter | ❌ |
| 8 | **Head of Growth** | Mon 09:00 → `0 1 * * 1` | weekly pattern + scale targets + offer direction → plan.json | ❌ |

## Rules (enforce every run)
- Resolve the LIVE ad account each run (never hardcode): PeningBot pixel `986352420917190`, PeningLab `1013990424497184`, ad account `act_943036532064443` (verify).
- **Create everything PAUSED** → owner approves (Reporter lists pending). RM3/day/project to start.
- **Andromeda:** every new ad = a DIFFERENT visual concept + unique BM copy (15–20 diverse ads/ad set). One consolidated CBO + ad set per pixel; never duplicate campaigns.
- Don't edit an ad set more than once / 7 days (learning phase). Only Agent 5 mutates ads; everyone else is read-only and just writes their state file.
- Judge by incrementality + new-customer results, not raw reported ROAS (see playbook).

## To create these as cron agents
For each row, create a scheduled cron with that schedule + a prompt = "You are Agent N (<role>). Read the meta-ads-playbook-2026 skill + workspace AGENTS.md + your input state file(s); do <job>; write <state file>." Set the model in the Model Routing tab (cheap daily runs → minimax-m3 / gemini-flash; heavier reasoning → a stronger model). Start by running 1→2→3→4→5 once (5 creates PAUSED → review in Ads Manager → activate), then 6+7.

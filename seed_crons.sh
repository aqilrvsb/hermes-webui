#!/bin/sh
# Seed the 17-agent marketing pipeline as Hermes cron jobs on the MARKETER profile.
# Idempotent: skips agents that already exist. Removes the legacy 4-agent crons (replaced).
# Times are Malaysia (TZ=Asia/Kuala_Lumpur, set in the image). Model = marketer profile config (minimax-m3).
H="${HERMES_HOME:-$HOME/.hermes}"
HB=/app/venv/bin/hermes
[ -x "$HB" ] || HB="$(command -v hermes 2>/dev/null)"
[ -n "$HB" ] || { echo "== seed_crons: hermes CLI not found, skip =="; exit 0; }
export TZ=Asia/Kuala_Lumpur

LIST="$("$HB" cron list --profile marketer 2>/dev/null || "$HB" cron list 2>/dev/null || true)"

# --- Replace: remove the legacy agent1..4 crons. Parse the REAL job ids from jobs.json
# (any name starting with "agent<digit>") and remove via the CLI — reliable path. ---
PYBIN=/app/venv/bin/python; [ -x "$PYBIN" ] || PYBIN="$(command -v python3 2>/dev/null || command -v python 2>/dev/null)"
if [ -n "$PYBIN" ]; then
  OLDIDS="$("$PYBIN" - "$H" <<'PY'
import json, glob, os, re, sys
H = sys.argv[1]; pat = re.compile(r'^agent[1-9]', re.I); ids = []
for jf in glob.glob(os.path.join(H, "**", "cron", "jobs.json"), recursive=True):
    try: d = json.load(open(jf, encoding="utf-8"))
    except Exception: continue
    jobs = d.get("jobs") if isinstance(d, dict) else d
    if not isinstance(jobs, list): continue
    for j in jobs:
        if isinstance(j, dict) and pat.search(str(j.get("name", ""))):
            ids.append(str(j.get("id") or j.get("job_id") or j.get("name")))
print("\n".join(i for i in ids if i))
PY
)"
  for ID in $OLDIDS; do
    "$HB" cron remove "$ID" >/dev/null 2>&1 && echo "== removed legacy cron: $ID ==" || true
  done
fi

# mk <name> <cron> <prompt> [--skill X ...]
mk() {
  name="$1"; sched="$2"; prompt="$3"; shift 3
  if echo "$LIST" | grep -q "$name"; then echo "== cron exists: $name (skip) =="; return; fi
  "$HB" cron create "$sched" "$prompt" --name "$name" --profile marketer "$@" >/dev/null 2>&1 \
    && echo "== cron created: $name ==" || echo "== cron FAILED: $name =="
}

PB="Do this for BOTH brands SEPARATELY (PeningBot + PeningLab) — never mix; read _products/<brand>.md."
RULES="Marketer profile. Malaysia only (BM/Manglish, MYT, MYR). Objective=SALES->website->paid subscription. Only the Ad Builder writes ads; you read/write _shared state. Post a one-line progress note."

# ---------- LAYER 0 FOUNDATION ----------
mk "00-product-analyst" "0 4 * * 1" \
"PRODUCT ANALYST (weekly). Study peningbot.com and peninglab.com with playwright. $PB Update each brand's product knowledge (features, pains, offer/pricing, USPs, objections, brand voice). READ: the live sites + _products/<brand>.md. WRITE: _shared/product_<brand>.json. $RULES" \
--skill spy-research

# ---------- LAYER 1 INTELLIGENCE ----------
mk "01-spy" "0 13,20 * * *" \
"SPY. Meta Ad Library (location=Malaysia): find competitor + cross-niche winning ads (sort by impressions, view inactive, funnel-hack their pages). $PB READ: _shared/product_<brand>.json. WRITE: _shared/spy_<brand>.json (ranked angles/offers/hooks to beat). $RULES" \
--skill spy-research

mk "02-market-researcher" "30 20 * * *" \
"MARKET RESEARCHER. Mine Malaysian customer language (Reddit r/malaysia, Lowyat, Shopee/TikTok reviews, FB groups) for pains/desires/objections in real BM/Manglish. Build personas (urgency x stakes) + ranked angles per awareness stage. $PB READ: _shared/product_<brand>.json, _shared/spy_<brand>.json. WRITE: _shared/personas_<brand>.json, _shared/angles_<brand>.json. $RULES" \
--skill spy-research --skill copywriting

# ---------- LAYER 2 STRATEGY ----------
mk "03-head-of-growth" "0 21 * * *" \
"HEAD OF GROWTH (daily conductor). $PB Set tomorrow's goal + budget (RM4/day each), pick today's personas/angles/awareness mix (~50-70/20-30/10-20 TOF/MOF/BOF), and write the creative brief (per slot: brand, persona, awareness, angle, hook, format, which landing page). READ: _shared/results_<brand>.json, spy_<brand>, personas_<brand>, angles_<brand>, offer_<brand>, product_<brand>, funnel_<brand>. WRITE: _shared/brief_<brand>.json. $RULES" \
--skill meta-ads-playbook-2026 --skill measurement --skill offer-design

mk "03b-head-of-growth-weekly" "0 8 * * 1" \
"HEAD OF GROWTH (weekly deep-dive). $PB Review the week's GPT/profit/incremental, decide strategy shifts + rebalance, set the weekly theme. READ: _shared/results_<brand>, learnings_<brand>. WRITE: _shared/strategy_<brand>.json. $RULES" \
--skill meta-ads-playbook-2026 --skill measurement

mk "04-offer-architect" "0 6 * * 1" \
"OFFER ARCHITECT (weekly). $PB Craft/iterate each brand's offer (price framing, value-stack, bonus, guarantee, Hormozi value-eq). READ: _shared/product_<brand>, spy_<brand>. WRITE: _shared/offer_<brand>.json. $RULES" \
--skill offer-design --skill copywriting

# ---------- LAYER 3 CREATIVE ----------
mk "05-copywriter" "30 21 * * *" \
"COPYWRITER. $PB For each brief slot write brand-specific MATCHED copy (hook first-3s, primary text, headline, website CTA) in BM/Manglish per brand voice; for video slots write a 10s timed script (3 beats ~20-25 words). Visual+copy = same angle. READ: _shared/brief_<brand>.json, product_<brand>, angles_<brand>, offer_<brand>. WRITE: update _shared/brief_<brand>.json with copy + image/video prompts. $RULES" \
--skill copywriting --skill creative-concepts

mk "06-image-producer" "0 22 * * *" \
"IMAGE PRODUCER. $PB Generate static creatives via peninglab (gpt-image-2 for text/layout, nano-banana for realism). Use Fire-and-Poll (check task_id in creatives -> get_status; never re-generate; batch 3-4 parallel). 3 live + ~3 reserve per brand. READ: _shared/brief_<brand>.json, prompt_lib_image.json. WRITE: _shared/creatives_<brand>.json (urls + task_id per slot). $RULES" \
--skill creative-image --skill creative-andromeda --skill creative-concepts

mk "07-video-producer" "0 22 * * *" \
"VIDEO PRODUCER. $PB Generate video creatives via peninglab gemini omni (10s, ~20-25 words, 3 beats) + AI-UGC. Fire-and-Poll (task_id -> get_status; never re-generate; batch parallel). READ: _shared/brief_<brand>.json, prompt_lib_video.json. WRITE: _shared/creatives_<brand>.json. $RULES" \
--skill creative-video --skill creative-andromeda --skill creative-concepts

mk "08-creative-rnd" "0 4 * * 2" \
"CREATIVE R&D (weekly, budget-gated). Master gemini omni + gpt-image-2; run small prompt experiments; close the win->prompt loop. $PB READ: _shared/results_<brand>, learnings_<brand>, creatives_<brand>. WRITE: _shared/prompt_lib_video.json, prompt_lib_image.json + a 'make-more/stop' note. Ask before spend > RM5. $RULES" \
--skill creative-rnd

# ---------- LAYER 4 EXECUTION & OPTIMIZATION ----------
mk "09-funnel-builder" "30 6 * * 1" \
"FUNNEL/LANDING BUILDER (weekly, advisory). $PB Ensure congruent landing pages per angle (advertorial/listicle/quiz -> the website); recommend page improvements + which page each angle points to. READ: _shared/product_<brand>, angles_<brand>, offer_<brand>. WRITE: _shared/funnel_<brand>.json. $RULES" \
--skill landing-funnel --skill website-sales-funnel

mk "10-ad-builder" "0 1 * * *" \
"AD BUILDER (01:00 DAILY — the ONLY agent that creates ads). $PB Resolve the live ad account (tiny PAUSED smoke-test for write access). Build ONE CBO per brand (OUTCOME_SALES, website conversion, pixel PeningBot 986352420917190 / PeningLab 1013990424497184 + purchase customEventType), broad Malaysia targeting, ad-set=one idea, 3 ads/set varying only the first-3s hook, using creatives_<brand>.json. ALWAYS PAUSED. Budget RM4/day. Then WhatsApp the owner (\$WHACENTER_DEFAULT_TO) the plan to approve before going live. READ: _shared/creatives_<brand>, brief_<brand>, offer_<brand>, funnel_<brand>, account_health.json. WRITE: _shared/live_ads_<brand>.json. Use zernio ads_create_standalone_ad. $RULES" \
--skill meta-ads-playbook-2026 --skill website-sales-funnel --skill creative-andromeda --skill account-safety

mk "11-optimizer" "0 10,15,21 * * *" \
"MEDIA BUYER/OPTIMIZER. $PB For each brand's live ads apply the 20% rule, min-spend trick, 4-quadrant classifier, win-ratio, frequency; kill losers, scale winners in steps (cut at half-speed); NEVER pause the supportive ad; judge on 7/30-day GPT/incremental, not 24h. Don't exceed RM4/day without owner approval. READ: _shared/live_ads_<brand>, results_<brand>. WRITE: _shared/learnings_<brand>.json (the 15-min-stare log). $RULES" \
--skill testing-scaling --skill creative-andromeda --skill measurement

mk "12-analyst" "30 23 * * *" \
"ANALYST (23:30 — closes the ~24h cycle). $PB Compute GPT/profit, new-customer + incremental attribution, CAPI gut-check (server vs browser purchase parity), audience-segment breakdown. READ: _shared/live_ads_<brand> + zernio analytics. WRITE: _shared/results_<brand>.json. $RULES" \
--skill measurement

mk "13-cro" "0 11,19 * * *" \
"CONVERSION/CHECKOUT CRO. $PB Watch landing->checkout conversion + abandoned checkout; recommend page/checkout fixes; refresh a lean abandoned-checkout retargeting audience. READ: _shared/live_ads_<brand>, results_<brand>, funnel_<brand>. WRITE: _shared/cro_<brand>.json. $RULES" \
--skill website-sales-funnel --skill measurement

mk "14-retention" "0 10 * * *" \
"RETENTION/LIFECYCLE. $PB Post-purchase onboarding, churn-save, upsell, win-back for the subscriptions; broadcast to existing/lapsed customers via zernio messaging / whacenter. READ: zernio customers/purchases + _shared/results_<brand>. WRITE: _shared/retention_<brand>.json. $RULES" \
--skill retention-lifecycle

mk "15-account-safety" "0 5 * * *" \
"ACCOUNT SAFETY (daily). $PB Check each brand's ad account + page status, write-locks, policy, special categories, pixel-event sanity; resolve the live working account; alert the Reporter on issues. WRITE: _shared/account_health.json. $RULES" \
--skill account-safety

# ---------- LAYER 5 COMMS ----------
mk "16-reporter" "0 0 * * *" \
"REPORTER (00:00 daily digest — the single owner-facing voice). $PB Send ONE concise WhatsApp digest to the owner (\$WHACENTER_DEFAULT_TO): spend, purchases, GPT, top creative, what changed, what needs approval. BM/English, no spam. READ: _shared/results_<brand>, learnings_<brand>, account_health.json. $RULES" \
--skill measurement

mk "16b-reporter-weekly" "0 9 * * 1" \
"REPORTER (weekly report, Mon 09:00). $PB WhatsApp the owner (\$WHACENTER_DEFAULT_TO) the week's performance per brand, winners, learnings, next-week plan. READ: _shared/results_<brand>, learnings_<brand>, strategy_<brand>. $RULES" \
--skill measurement

echo "== seed_crons: done =="

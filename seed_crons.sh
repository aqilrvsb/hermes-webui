#!/bin/sh
# Seed the 12-agent marketing pipeline (5 departments) as Hermes cron jobs on the MARKETER profile.
# Idempotent: skips agents that already exist. Removes the legacy 4-agent + the 5 deprecated agents.
# Times are Malaysia (TZ=Asia/Kuala_Lumpur). Model = marketer profile config (OpenCode Go minimax-m3).
# CYCLE: 08:00 INTELLIGENCE (watch today) -> 00:00 STRATEGY (decide close/maintain + brief N new)
#        -> 00:30 CREATIVE (make only N) -> 01:15 EXECUTION (launch LIVE) -> 01:45 COMMS (report).
H="${HERMES_HOME:-$HOME/.hermes}"
HB=/app/venv/bin/hermes
[ -x "$HB" ] || HB="$(command -v hermes 2>/dev/null)"
[ -n "$HB" ] || { echo "== seed_crons: hermes CLI not found, skip =="; exit 0; }
export TZ=Asia/Kuala_Lumpur
export HERMES_PROFILE=marketer   # new crons default to the marketer profile

LIST="$("$HB" cron list --profile marketer 2>/dev/null || "$HB" cron list 2>/dev/null || true)"

# --- Delete deprecated / legacy / weekly crons DIRECTLY from jobs.json. We run BEFORE the gateway starts,
#     so the file edit sticks (the gateway then loads the correct final 12). The old CLI-remove approach
#     failed because the gateway re-wrote jobs.json from memory after seed_crons ran. ---
PYBIN=/app/venv/bin/python; [ -x "$PYBIN" ] || PYBIN="$(command -v python3 2>/dev/null || command -v python 2>/dev/null)"
if [ -n "$PYBIN" ]; then
  "$PYBIN" - "$H" <<'PY' || true
import json, glob, os, re, sys
H = sys.argv[1]
kill = re.compile(r'^(agent[1-9]|00-product-analyst|03b-|08-creative-rnd|09-funnel-builder|14-retention|15-account-safety|16b-)|-weekly$', re.I)
for jf in glob.glob(os.path.join(H, "**", "cron", "jobs.json"), recursive=True):
    try: d = json.load(open(jf, encoding="utf-8"))
    except Exception: continue
    jobs = d.get("jobs") if isinstance(d, dict) else d
    if not isinstance(jobs, list): continue
    keep = [j for j in jobs if not (isinstance(j, dict) and kill.search(str(j.get("name", ""))))]
    if len(keep) != len(jobs):
        if isinstance(d, dict): d["jobs"] = keep
        else: d = keep
        try:
            json.dump(d, open(jf, "w", encoding="utf-8"), indent=2)
            print("== deleted %d deprecated/legacy cron(s) from %s ==" % (len(jobs)-len(keep), jf))
        except Exception: pass
PY
fi

# mk <name> <cron> <prompt> [--skill X ...]
mk() {
  name="$1"; sched="$2"; prompt="$3"; shift 3
  if echo "$LIST" | grep -q "$name"; then echo "== cron exists: $name (skip) =="; return; fi
  "$HB" cron create "$sched" "$prompt" --name "$name" --profile marketer "$@" >/dev/null 2>&1 \
    && echo "== cron created: $name ==" || echo "== cron FAILED: $name =="
}

PB="Do this for BOTH brands SEPARATELY (PeningBot + PeningLab) — never mix; read _products/<brand>.md."
RULES="Marketer profile. Malaysia only (BM/Manglish, MYT, MYR). Objective=SALES->website->paid subscription (pixel+CAPI, customEventType PURCHASE). Only the Ad Builder touches ads. Post a one-line progress note."

# ========== 🔎 INTELLIGENCE (08:00 — watch the current day, feed tonight's Strategy) ==========
mk "01-spy" "0 8 * * *" \
"SPY (Intelligence). Use playwright to scan the Meta Ad Library (facebook.com/ads/library, country=MY, sort by total impressions) for competitor + cross-niche WINNING ads; read their hooks/offers/funnels. $PB WRITE: _shared/spy_<brand>.json (ranked angles/offers/hooks to beat). $RULES" \
--skill spy-research

mk "02-market-researcher" "10 8 * * *" \
"MARKET RESEARCHER (Intelligence). Use playwright + web search to mine Malaysian customer language (Reddit, Lowyat, Shopee/TikTok reviews, FB groups) for pains/desires/objections in real BM/Manglish. Build personas + ranked angles per awareness stage. $PB WRITE: _shared/personas_<brand>.json, _shared/angles_<brand>.json. $RULES" \
--skill spy-research --skill copywriting

mk "12-analyst" "20 8 * * *" \
"ANALYST (Intelligence). Via zernio analytics, measure each brand's live ads: spend, purchases, ROAS/GPT, CPA, frequency, + CAPI parity (server vs browser purchases). $PB WRITE: _shared/results_<brand>.json — the clean data Strategy decides on tonight. $RULES" \
--skill measurement

mk "11-optimizer" "30 8 * * *" \
"OPTIMIZER (Intelligence — RECOMMENDS ONLY, does not touch ads). Via zernio, review each live ad with the 4-quadrant + frequency + win-ratio lens (judge on 7-day, not 24h noise) and FLAG each as CLOSE / MAINTAIN / SCALE candidate. $PB WRITE: _shared/learnings_<brand>.json (recommendations for Strategy). Never pause/edit ads — only the Ad Builder does. $RULES" \
--skill testing-scaling --skill creative-andromeda --skill measurement

mk "13-cro" "40 8 * * *" \
"CRO (Intelligence). Via zernio conversion metrics + a playwright spot-check of the live page, watch landing->checkout->purchase conversion + abandoned checkout; note any leak. $PB WRITE: _shared/cro_<brand>.json. $RULES" \
--skill website-sales-funnel --skill measurement

# ========== 🧠 STRATEGY (00:00 — THE SPEND GATE: decide on full 24h data) ==========
mk "03-head-of-growth" "0 0 * * *" \
"HEAD OF GROWTH (Strategy — THE SPEND GATE; the brain). $PB Pull the live last-24h performance from zernio for each brand, plus read _shared/results, learnings, spy, personas, angles, offer. DECIDE per live ad: CLOSE or MAINTAIN. Then brief HOW MANY NEW ads to make to refill RM4/day each, and for EACH new slot specify: angle, persona, awareness, FORMAT (video=gemini omni / image=gpt-image-2), creative concept, and copy direction. WRITE _shared/brief_<brand>.json = {close:[ad_ids], maintain:[ad_ids], new:[{angle,persona,awareness,format,concept,copy_direction}]}. You are the ONLY trigger for spend — brief 0 new and Creative makes nothing. $RULES" \
--skill meta-ads-playbook-2026 --skill measurement --skill offer-design --skill creative-concepts

mk "04-offer-architect" "0 0 * * 1" \
"OFFER ARCHITECT (Strategy, weekly Mon 00:00). $PB Craft/iterate each brand's offer (price framing, value-stack, bonus, guarantee, Hormozi value-eq) from the product brief + spy. WRITE _shared/offer_<brand>.json. $RULES" \
--skill offer-design --skill copywriting

# ========== 🎨 CREATIVE (executes the brief ONLY — budget-matched, no blind spend) ==========
mk "05-copywriter" "30 0 * * *" \
"COPYWRITER (Creative). Read _shared/brief_<brand>.json. For EACH new slot ONLY, write the exact BM/Manglish copy per Strategy's direction: 3s hook, primary text, headline, website CTA; for video slots a 10s script (3 beats, ~20-25 words). Add the matching image/video prompt. Visual+copy = same angle. $PB Update _shared/brief_<brand>.json with copy + prompts. Make nothing Strategy didn't brief. $RULES" \
--skill copywriting --skill creative-concepts

mk "06-image-producer" "45 0 * * *" \
"IMAGE PRODUCER (Creative). For each IMAGE slot in the brief, generate via peninglab gpt-image-2 (nano-banana only for ultra-real product shots). Fire-and-Poll (check task_id in creatives -> get_status; never re-generate; batch parallel). Generate ONLY the briefed count. $PB WRITE _shared/creatives_<brand>.json (urls + task_id per slot). $RULES" \
--skill creative-image --skill creative-andromeda --skill creative-concepts

mk "07-video-producer" "45 0 * * *" \
"VIDEO PRODUCER (Creative). For each VIDEO slot in the brief, generate via peninglab gemini omni (10s, ~20-25 words, 3 beats) + AI-UGC. Fire-and-Poll (task_id -> get_status; never re-generate; batch parallel). Generate ONLY the briefed count. $PB WRITE _shared/creatives_<brand>.json. $RULES" \
--skill creative-video --skill creative-andromeda --skill creative-concepts

# ========== 🚀 EXECUTION (the ONLY hand on the ads — launches LIVE, capped RM4/day) ==========
mk "10-ad-builder" "15 1 * * *" \
"AD BUILDER (Execution — the ONLY agent that touches ads). $PB Verify write access (read campaigns first). STEP 1 CLOSE: pause the ad_ids in brief.close (zernio update_ad_campaign_status -> PAUSED). STEP 2 LAUNCH LIVE: for the new creatives build one CBO per brand — goal=conversions (OUTCOME_SALES), website conversion, promoted_object.pixelId = PeningBot 986352420917190 / PeningLab 1013990424497184 + customEventType=PURCHASE, CAPI tracking, broad Malaysia, ad-set=one idea, 3 ads/set varying only the first-3s hook, budget RM4/day, status ACTIVE (LIVE-DIRECT — no PAUSE, no approval; the RM4/day cap is the safety). READ _shared/creatives_<brand>, brief_<brand>, offer_<brand>. WRITE _shared/live_ads_<brand>.json. Tool: zernio ads_create_standalone_ad on account act_943036532064443 ('Pening', MYR — resolve live each run). $RULES" \
--skill meta-ads-playbook-2026 --skill website-sales-funnel --skill creative-andromeda --skill account-safety

# ========== 📨 COMMS ==========
mk "16-reporter" "45 1 * * *" \
"REPORTER (Comms — the single voice to the owner). Send ONE WhatsApp digest to \$WHACENTER_DEFAULT_TO for this cycle: what CLOSED, what LAUNCHED live, spend, purchases, ROAS/GPT, top creative. BM/English, concise, no spam. $PB READ _shared/results_<brand>, learnings_<brand>, live_ads_<brand>. Send via whacenter: curl -X POST https://api.whacenter.com/api/send -d \"device_id=\$WHACENTER_DEVICE\" --data-urlencode \"number=\$WHACENTER_DEFAULT_TO\" --data-urlencode \"message=...\". $RULES" \
--skill measurement

# Re-tag my crons to the MARKETER profile (the CLI may file new crons under 'default').
if [ -n "$PYBIN" ]; then
  "$PYBIN" - "$H" <<'PY' || true
import json,glob,os,re,sys
H=sys.argv[1]; mine=re.compile(r'^\d')  # my cron names start with a digit (01..16)
n=0
for jf in glob.glob(os.path.join(H,"**","cron","jobs.json"),recursive=True):
    try: d=json.load(open(jf,encoding="utf-8"))
    except Exception: continue
    jobs=d.get("jobs") if isinstance(d,dict) else d
    if not isinstance(jobs,list): continue
    ch=False
    for j in jobs:
        if isinstance(j,dict) and mine.match(str(j.get("name",""))) and j.get("profile")!="marketer":
            j["profile"]="marketer"; ch=True; n+=1
    if ch:
        try: json.dump(d, open(jf,"w",encoding="utf-8"), indent=2)
        except Exception: pass
print("== cron retag: %d job(s) -> profile marketer ==" % n)
PY
fi
echo "== seed_crons: done (12 agents, 5 departments) =="

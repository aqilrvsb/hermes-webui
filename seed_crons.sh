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
kill = re.compile(r'^(agent[1-9]|[0-9])|-weekly$', re.I)  # delete legacy agents + ALL old numbered (01..16, 00, 03b, 08, 09, 14, 15, 16b) + weekly. New person-named agents start with a letter -> survive.
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
RULES="Marketer profile. Malaysia only (BM/Manglish, MYT, MYR). Objective=SALES->website->paid subscription (pixel+CAPI, customEventType PURCHASE). Only the Ad Builder touches ads. Post a one-line progress note. AT THE END: append a dated (## YYYY-MM-DD), human-readable report to _shared/reports/<your agent name>.md (create the folder/file if missing) — what you researched, the info/data you collected, what you did/decided, key findings, and what you recommend — so the owner can review your daily work in the Files panel."

# Learning-phase guardrail (Strategy + Optimizer) — stops premature kills AND budget creep (one campaign per brand).
GUARD="LEARNING-PHASE GUARDRAIL: NEVER close a campaign/ad in its first 3 days, or before it has >=50 link clicks OR >=RM12 spend. Days 1-3 = MAINTAIN only; judge ONLY leading metrics (CTR, CPC, LP views, thumbstop) — NOT purchases (too sparse at RM4/day to be significant). After day 3 AND the data floor is met, cut the worst by leading metrics and shift budget to the best. Close on CPA/ROAS ONLY once an ad has >=3 purchases. Pause (not delete) broken ads anytime only if: disapproved, zero delivery, or CPC >=3x the set average. At RM4/day CBO Meta serves only 1-2 of the ads in a set — that is normal, do NOT treat low-impression ads as failures. BUDGET LOCK (CRITICAL): each brand must run EXACTLY ONE active campaign at RM4/day total — never two. Do NOT brief new ads that would spin up a second campaign. While ANY ad is still in its 3-day learning window, OR whenever you are closing 0 ads, set new=[] (brief ZERO new) so nothing new launches. Only brief new creatives to REPLACE ads you are closing in the SAME run, so the brand always stays at one RM4/day campaign. If you already see 2+ active campaigns for a brand, brief 0 new and recommend consolidating to one."
# Auto-publish creatives to the Creatives gallery (producers).
PUB="AFTER generating, PUBLISH each new asset to the Creatives gallery: append an item {brand,slot,type,url,headline,primary} to creatives.json in the github repo aqilrvsb/hermes-inbox (github MCP: get_file_contents creatives.json for its sha -> create_or_update_file on branch main, MERGING with the existing items array, message 'publish creatives'). Keep all prior items."
# Idempotent ad creation (Ad Builder) — zernio create is slow; never blind-retry (dupes) + ONE campaign per brand (no budget creep).
IDEMP="IDEMPOTENT CREATE: create each ad ONCE. zernio ads_create can be slow and may time out even though Meta DID create the ad, so on ANY error/timeout do NOT blind-retry — first call ads_list_ads to check whether that creative already has an ad, and create only if genuinely missing. ONE CAMPAIGN PER BRAND (CRITICAL — prevents RM8/day): BEFORE creating anything, list the brand's campaigns; if an ACTIVE campaign already exists for that brand, do NOT create a new campaign — add the briefed new ads as a new ad set INSIDE that existing campaign; if brief.new is empty, create NOTHING. NEVER run two concurrent campaigns for one brand — total must stay RM4/day per brand. End each ad set at exactly the briefed ad count, delete duplicates, then STOP."

# ========== 🔎 INTELLIGENCE (08:00 — watch the current day, feed tonight's Strategy) ==========
mk "Aiman (Spy)" "0 8 * * *" \
"SPY (Intelligence). Use scrapling (its StealthyFetcher bypasses the Ad Library's anti-bot; adaptive selectors) to scan the Meta Ad Library (facebook.com/ads/library, country=MY, sort by total impressions) for competitor + cross-niche WINNING ads; read their hooks/offers/funnels. $PB WRITE: _shared/spy_<brand>.json (ranked angles/offers/hooks to beat). $RULES" \
--skill spy-research

mk "Nadia (Market Researcher)" "10 8 * * *" \
"MARKET RESEARCHER (Intelligence). Use scrapling (StealthyFetcher) + web search to mine Malaysian customer language (Reddit, Lowyat, Shopee/TikTok reviews, FB groups) for pains/desires/objections in real BM/Manglish. Build personas + ranked angles per awareness stage. $PB WRITE: _shared/personas_<brand>.json, _shared/angles_<brand>.json. $RULES" \
--skill spy-research --skill copywriting

mk "Faiz (Analyst)" "20 8 * * *" \
"ANALYST (Intelligence). Via zernio analytics, measure each brand's live ads: spend, purchases, ROAS/GPT, CPA, frequency, + CAPI parity (server vs browser purchases). $PB WRITE: _shared/results_<brand>.json — the clean data Strategy decides on tonight. $RULES" \
--skill measurement

mk "Hafiz (Optimizer)" "30 8 * * *" \
"OPTIMIZER (Intelligence — RECOMMENDS ONLY, does not touch ads). Via zernio, review each live ad with the 4-quadrant + frequency + win-ratio lens (judge on 7-day, not 24h noise) and FLAG each as CLOSE / MAINTAIN / SCALE candidate. $PB WRITE: _shared/learnings_<brand>.json (recommendations for Strategy). Never pause/edit ads — only the Ad Builder does. $RULES" \
--skill testing-scaling --skill creative-andromeda --skill measurement

mk "Liyana (CRO)" "40 8 * * *" \
"CRO (Intelligence). Via zernio conversion metrics + a playwright spot-check of the live page, watch landing->checkout->purchase conversion + abandoned checkout; note any leak. $PB WRITE: _shared/cro_<brand>.json. $RULES" \
--skill website-sales-funnel --skill measurement

# ========== 🧠 STRATEGY (00:00 — THE SPEND GATE: decide on full 24h data) ==========
mk "Danish (Head of Growth)" "0 0 * * *" \
"HEAD OF GROWTH (Strategy — THE SPEND GATE; the brain). $PB Pull the live last-24h performance from zernio for each brand, plus read _shared/results, learnings, spy, personas, angles, offer. DECIDE per live ad: CLOSE or MAINTAIN. Then brief HOW MANY NEW ads to make to refill RM4/day each, and for EACH new slot specify: angle, persona, awareness, FORMAT (video=gemini omni / image=gpt-image-2), creative concept, and copy direction. WRITE _shared/brief_<brand>.json = {close:[ad_ids], maintain:[ad_ids], new:[{angle,persona,awareness,format,concept,copy_direction}]}. You are the ONLY trigger for spend — brief 0 new and Creative makes nothing. $RULES" \
--skill meta-ads-playbook-2026 --skill measurement --skill offer-design --skill creative-concepts

mk "Sofea (Offer Architect)" "0 0 * * 1" \
"OFFER ARCHITECT (Strategy, weekly Mon 00:00). $PB Craft/iterate each brand's offer (price framing, value-stack, bonus, guarantee, Hormozi value-eq) from the product brief + spy. WRITE _shared/offer_<brand>.json. $RULES" \
--skill offer-design --skill copywriting

# ========== 🎨 CREATIVE (executes the brief ONLY — budget-matched, no blind spend) ==========
mk "Iman (Copywriter)" "30 0 * * *" \
"COPYWRITER (Creative). Read _shared/brief_<brand>.json. For EACH new slot ONLY, write the exact BM/Manglish copy per Strategy's direction: 3s hook, primary text, headline, website CTA; for video slots a 10s script (3 beats, ~24-28 words). Add the matching image/video prompt. Visual+copy = same angle. $PB Update _shared/brief_<brand>.json with copy + prompts. Make nothing Strategy didn't brief. $RULES" \
--skill copywriting --skill creative-concepts

mk "Aisyah (Image Producer)" "45 0 * * *" \
"IMAGE PRODUCER (Creative). For each IMAGE slot in the brief, generate via peninglab gpt-image-2 (nano-banana only for ultra-real product shots). Fire-and-Poll (check task_id in creatives -> get_status; never re-generate; batch parallel). Generate ONLY the briefed count. $PB WRITE _shared/creatives_<brand>.json (urls + task_id per slot). $RULES" \
--skill creative-image --skill creative-andromeda --skill creative-concepts

mk "Zikri (Video Producer)" "45 0 * * *" \
"VIDEO PRODUCER (Creative). For each VIDEO slot in the brief, generate via peninglab gemini omni (10s, ~24-28 words, 3 beats) + AI-UGC. Fire-and-Poll (task_id -> get_status; never re-generate; batch parallel). Generate ONLY the briefed count. $PB WRITE _shared/creatives_<brand>.json. $RULES" \
--skill creative-video --skill creative-andromeda --skill creative-concepts

# ========== 🚀 EXECUTION (the ONLY hand on the ads — launches LIVE, capped RM4/day) ==========
mk "Adam (Ad Builder)" "15 1 * * *" \
"AD BUILDER (Execution — the ONLY agent that touches ads). $PB Verify write access (read campaigns first). STEP 1 CLOSE: pause the ad_ids in brief.close (zernio update_ad_campaign_status -> PAUSED). STEP 2 LAUNCH LIVE: for the new creatives build one CBO per brand — goal=conversions (OUTCOME_SALES), website conversion, promoted_object.pixelId = PeningBot 986352420917190 / PeningLab 1013990424497184 + customEventType=PURCHASE, CAPI tracking, broad Malaysia, ad-set=one idea, 3 ads/set varying only the first-3s hook, budget RM4/day, status ACTIVE (LIVE-DIRECT — no PAUSE, no approval; the RM4/day cap is the safety). READ _shared/creatives_<brand>, brief_<brand>, offer_<brand>. WRITE _shared/live_ads_<brand>.json. Tool: zernio ads_create_standalone_ad on account act_943036532064443 ('Pening', MYR — resolve live each run). $RULES" \
--skill meta-ads-playbook-2026 --skill website-sales-funnel --skill creative-andromeda --skill account-safety

# ========== 📨 COMMS ==========
mk "Mia (Reporter)" "45 1 * * *" \
"REPORTER (Comms — the single voice to the owner). Send ONE WhatsApp digest to \$WHACENTER_DEFAULT_TO for this cycle: what CLOSED, what LAUNCHED live, spend, purchases, ROAS/GPT, top creative. BM/English, concise, no spam. $PB READ _shared/results_<brand>, learnings_<brand>, live_ads_<brand>. Send via whacenter: curl -X POST https://api.whacenter.com/api/send -d \"device_id=\$WHACENTER_DEVICE\" --data-urlencode \"number=\$WHACENTER_DEFAULT_TO\" --data-urlencode \"message=...\". $RULES" \
--skill measurement

# Re-tag my crons to the MARKETER profile (the CLI may file new crons under 'default').
if [ -n "$PYBIN" ]; then
  "$PYBIN" - "$H" <<'PY' || true
import json,glob,os,re,sys
H=sys.argv[1]; mine=re.compile(r'^\S+ \((Spy|Market|Analyst|Optimizer|CRO|Head|Offer|Copywriter|Image|Video|Ad Builder|Reporter)', re.I)  # my agents are "Firstname (Role...)" — NO trailing \) so multi-word roles (Market Researcher, Head of Growth, Offer/Image/Video ...) also match
n=0
for jf in glob.glob(os.path.join(H,"**","cron","jobs.json"),recursive=True):
    try: d=json.load(open(jf,encoding="utf-8"))
    except Exception: continue
    jobs=d.get("jobs") if isinstance(d,dict) else d
    if not isinstance(jobs,list): continue
    ch=False
    for j in jobs:
        if isinstance(j,dict) and mine.search(str(j.get("name",""))) and j.get("profile")!="marketer":
            j["profile"]="marketer"; ch=True; n+=1
    if ch:
        try: json.dump(d, open(jf,"w",encoding="utf-8"), indent=2)
        except Exception: pass
print("== cron retag: %d job(s) -> profile marketer ==" % n)
PY
fi
# --- PATCH EXISTING jobs: mk() skips agents that already exist, so their prompts in jobs.json keep the
#     OLD text. Inject the guardrail / publish / idempotency rules into the live jobs directly (runs before
#     the gateway, so edits stick). Idempotent: only appends if the rule's marker isn't already present. ---
if [ -n "$PYBIN" ]; then
  "$PYBIN" - "$H" "$GUARD" "$PUB" "$IDEMP" <<'PY' || true
import json,glob,os,re,sys
H,GUARD,PUB,IDEMP=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]
def extra_for(name):
    if re.search(r'Head of Growth|Optimizer', name, re.I): return GUARD
    if re.search(r'Image Producer|Video Producer', name, re.I): return PUB
    if re.search(r'Ad Builder', name, re.I): return IDEMP
    return None
# Plain substring replacements applied to EVERY agent's prompt (e.g. tuning the video word count).
REPL=[("~20-25 words","~24-28 words"),("20-25 words","24-28 words"),("Use playwright","Use scrapling"),("playwright","scrapling"),("Playwright","scrapling")]
n=0
for jf in glob.glob(os.path.join(H,"**","cron","jobs.json"),recursive=True):
    try: d=json.load(open(jf,encoding="utf-8"))
    except Exception: continue
    jobs=d.get("jobs") if isinstance(d,dict) else d
    if not isinstance(jobs,list): continue
    ch=False
    for j in jobs:
        if not isinstance(j,dict): continue
        pk=None
        for key in ("prompt","task","message","instruction","text"):
            if isinstance(j.get(key),str) and j.get(key).strip(): pk=key; break
        if not pk: continue
        v=j[pk]; orig=v
        for a,b in REPL: v=v.replace(a,b)            # global text tweaks (all agents)
        extra=extra_for(str(j.get("name","")))       # rule injection (specific agents)
        if extra:
            marker=extra[:28]  # stable prefix, constant across rule versions -> find+replace the old text
            idx=v.find(marker)
            v=(v[:idx].rstrip()+" "+extra) if idx>=0 else (v.rstrip()+" "+extra)
        if v!=orig: j[pk]=v; ch=True; n+=1
    if ch:
        try: json.dump(d, open(jf,"w",encoding="utf-8"), indent=2)
        except Exception: pass
print("== rule patch (guardrail/publish/idempotent): %d job(s) updated ==" % n)
PY
fi
echo "== seed_crons: done (12 agents, 5 departments) =="

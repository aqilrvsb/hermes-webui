# Runs at boot. Writes mcp_servers + skills.external_dirs into EVERY profile's config.yaml.
# Calls the PRE-INSTALLED binaries in /opt/node/bin directly (NOT npx) for fast, reliable,
# stdio-clean MCP startup. Tokens read from env => add a Railway var + restart to activate.
import os
try:
    import yaml
except Exception:
    raise SystemExit(0)
HOME = os.path.expanduser("~/.hermes")
BIN = "/opt/node/bin/"
PATHV = "/opt/node/bin:" + os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")
def E(*keys):
    e = {"PATH": PATHV, "NO_UPDATE_NOTIFIER": "1", "NODE_NO_WARNINGS": "1", "npm_config_update_notifier": "false"}
    for k in keys:
        v = os.environ.get(k)
        if v:
            e[k] = v
    return e
# ── 100% GoLogin. Zernio + Scrapling MCPs REMOVED (user: "remove zernio and other mcp so no conflict,
# 100% rely on gologin"). Posting AND scraping now happen through the GoLogin cloud browser (one real
# logged-in Chrome per client). peninglab stays — it's the CONTENT engine (image/video generation for
# post creatives), not a browser/posting tool, so it does not conflict.
# Admin keys live in SUPABASE admin_settings (never in git): fetch them at boot. Env still wins.
def _supa_settings():
    import json as _sj, urllib.request as _sr
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.environ.get("SUPABASE_SERVICE_KEY") or "").strip()
    if not url or not key:
        return {}
    try:
        req = _sr.Request(url + "/rest/v1/admin_settings?select=key,value")
        req.add_header("apikey", key); req.add_header("Authorization", "Bearer " + key)
        with _sr.urlopen(req, timeout=15) as resp:
            rows = _sj.loads(resp.read().decode("utf-8"))
        return {r["key"]: (r.get("value") or "") for r in rows if isinstance(r, dict)}
    except Exception as e:
        print("== mcp_setup: supabase settings fetch failed:", e, "==")
        return {}
def _supa_clients():
    """Map hermes_profile -> that client's own OpenRouter key (for mode='client')."""
    import json as _sj, urllib.request as _sr
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.environ.get("SUPABASE_SERVICE_KEY") or "").strip()
    if not url or not key:
        return {}
    try:
        req = _sr.Request(url + "/rest/v1/clients?select=hermes_profile,openrouter_key")
        req.add_header("apikey", key); req.add_header("Authorization", "Bearer " + key)
        with _sr.urlopen(req, timeout=15) as resp:
            rows = _sj.loads(resp.read().decode("utf-8"))
        return {r["hermes_profile"]: (r.get("openrouter_key") or "")
                for r in rows if isinstance(r, dict) and r.get("hermes_profile")}
    except Exception as e:
        print("== mcp_setup: supabase clients fetch failed:", e, "==")
        return {}
_SUPA = _supa_settings()
GOLOGIN_TOKEN = (os.environ.get("GOLOGIN_API_TOKEN") or os.environ.get("GOLOGIN_TOKEN")
                 or _SUPA.get("gologin_token", "")).strip()
# OpenRouter key: env first, else the Admin-managed shared key from Supabase.
OPENROUTER_KEY = (os.environ.get("OPENROUTER_API_KEY") or _SUPA.get("openrouter_key", "")).strip()
# Mode: 'admin' = everyone uses the shared key; 'client' = each client's own key (from their Settings).
OPENROUTER_MODE = (_SUPA.get("openrouter_mode") or "admin").strip()
_CLIENT_OR_KEYS = _supa_clients() if OPENROUTER_MODE == "client" else {}
servers = {
    "peninglab": {"command": BIN+"peninglab-mcp", "args": [], "env": E("PENINGLAB_API_KEY"), "timeout": 900, "connect_timeout": 60},  # generate_* BLOCK minutes; keep 900s so they finish + don't double-charge
}
# GoLogin MCP — manage profiles/proxies/fingerprints + start/stop cloud browsers (env API_TOKEN).
# The actual posting/scraping is driven by the app backend via the GoLogin cloud browser (CDP) — this
# MCP just lets the chat agent manage the client's profile conversationally. Gated on the token existing.
if GOLOGIN_TOKEN:
    _genv = E()
    _genv["API_TOKEN"] = GOLOGIN_TOKEN
    servers["gologin"] = {"command": BIN+"gologin-mcp", "args": [], "env": _genv, "timeout": 300, "connect_timeout": 60}
# Per-profile skill scoping: each role sees ONLY its relevant skills (cleaner Skills tab).
# Dirs are category-preserving bundles built in Dockerfile.railway.
# /opt/skills-common holds skills EVERY profile should have (e.g. whatsapp-whacenter messaging).
COMMON = ["/opt/skills-common"]
# GENERAL = superpowers, shared to EVERY profile. marketer also gets it now (user: "full general across profile").
SKILLS_BY_PROFILE = {
    # marketer: ONLY the 2 marketing skills (meta-ads-playbook-2026 + agency-8-agents). No general/
    # superpowers/common — it works directly via the zernio MCP; whacenter usage is in the SOUL.
    "marketer":  ["/opt/skills-mkt"],
    "developer": ["/opt/skills/superpowers/skills", "/opt/skills-dev"] + COMMON,   # general + dev + cavecrew + messaging
}
SKILLS_DEFAULT = []  # CLEARED: no skills loaded (internal Social Media Manager — agent works via MCPs + its instructions)
def homes():
    out = [HOME]
    pdir = os.path.join(HOME, "profiles")
    if os.path.isdir(pdir):
        for n in sorted(os.listdir(pdir)):
            ph = os.path.join(pdir, n)
            if os.path.isdir(ph):
                out.append(ph)
    return out
done = []
for home in homes():
    name = os.path.basename(home) if home != HOME else "default"
    p = os.path.join(home, "config.yaml")
    cfg = {}
    if os.path.exists(p):
        try:
            cfg = yaml.safe_load(open(p, encoding="utf-8").read()) or {}
        except Exception:
            cfg = {}
    if not isinstance(cfg, dict):
        cfg = {}
    ex = cfg.get("mcp_servers") or {}
    ex.pop("meta_ads", None)
    ex.pop("vercel", None)  # prune the broken stdio vercel server persisted in the volume; Vercel is CLI-only now
    ex.update(servers)
    cfg["mcp_servers"] = ex
    # Per-profile skills: REPLACE external_dirs so each role only sees its own skills.
    sk = cfg.get("skills") or {}
    sk["external_dirs"] = list(SKILLS_BY_PROFILE.get(name, SKILLS_DEFAULT))
    cfg["skills"] = sk
    # Clarify timeout: default 120s gave up while the user was still typing.
    # This is an interactive web chat (a human is present), so make it effectively
    # NEVER time out — ~1 year. (Code treats <=0 as "use default 120", so we can't
    # set 0; a huge positive value = no timeout in practice, like Claude Code.)
    cl = cfg.get("clarify") or {}
    cl["timeout"] = 31536000
    cfg["clarify"] = cl
    # Belt-and-suspenders: the agent block has its OWN clarify_timeout (default 600s) that some
    # code paths use — set it huge too so clarifications never time out in the web chat.
    ag = cfg.get("agent") or {}
    ag["clarify_timeout"] = 31536000
    cfg["agent"] = ag
    # Default task env cwd: point at the PERSISTENT volume workspace, not ephemeral /app
    # (the "local environment for task default" was defaulting to /app -> writes lost on restart).
    tm = cfg.get("terminal") or {}
    tm["cwd"] = os.path.join(HOME, "workspace")
    cfg["terminal"] = tm
    # ── MAIN provider = OpenCode Go (low-cost open coding models, OpenAI-compatible /chat/completions),
    # default minimax-m3. OpenRouter + GRSAI stay as alternates/fallback (GRSAI also = image/PDF vision).
    # All in THIS config.yaml on the volume (editable; model switchable in the Model Routing tab/dropdown).
    # Keys are env-refs (never hit git). Gated on a key existing -> safe rollback.
    #   opencode   -> https://opencode.ai/zen/go/v1 (key ${OPENCODE_API_KEY})  [MAIN: minimax-m3]
    #   openrouter -> https://openrouter.ai/api/v1   (key ${OPENROUTER_API_KEY}) [alternate + fallback/auto]
    #   grsai      -> https://grsaiapi.com/v1        (key ${GRSAI_API_KEY})      [image/PDF gemini + fallback]
    HAS_OC = bool(os.environ.get("OPENCODE_API_KEY", "").strip())
    # Per-profile effective key: client's own (mode='client') else the shared admin key.
    _PROF_OR = ((_CLIENT_OR_KEYS.get(name, "") or "").strip() if OPENROUTER_MODE == "client" else "") \
        or OPENROUTER_KEY
    HAS_OR = bool(_PROF_OR)
    HAS_GR = bool(os.environ.get("GRSAI_API_KEY", "").strip())
    HAS_AM = bool(os.environ.get("AIMURAH_API_KEY", "").strip())   # AIMurah (aimurah.my.id) — OpenAI-compatible; FREE claude-sonnet-4.5/haiku-4.5
    if HAS_OR:
        OR_BASE = "https://openrouter.ai/api/v1"
        # Pickable models — shown in the chat model dropdown (dynamic pick, live per-chat + per-agent).
        # Add/remove any OpenRouter model id freely; the DEFAULT below is just the startup model.
        OR_MODELS = ["openai/gpt-4.1", "openai/gpt-4.1-mini", "anthropic/claude-sonnet-4.5",
                     "openrouter/auto", "google/gemini-2.5-pro", "google/gemini-2.5-flash",
                     "openai/gpt-5.4", "deepseek/deepseek-chat"]
        OR_DEFAULT = os.environ.get("OPENROUTER_DEFAULT_MODEL", "").strip() or "openai/gpt-4.1"
        # Use the literal key so it works whether it came from env, the Admin panel, or the client's
        # own Settings; env-ref "${OPENROUTER_API_KEY}" would NOT resolve for a DB-provided key.
        OR_KEY = _PROF_OR or "${OPENROUTER_API_KEY}"
        # Drop any previously-persisted providers we no longer use (minimax/opencode/grsai/aimurah/apipod).
        cps = [c for c in (cfg.get("custom_providers") or [])
               if isinstance(c, dict) and str(c.get("name") or "").lower()
               not in ("apipod", "apipod-gpt", "opencode", "grsai", "aimurah")]
        or_entry = {"name": "openrouter", "base_url": OR_BASE,
                    "api_key": OR_KEY, "models": OR_MODELS}
        found = False
        for c in cps:
            if isinstance(c, dict) and str(c.get("name") or "").lower() == "openrouter":
                c.update(or_entry); found = True   # refresh the pick-list (drop stale minimax etc.)
        if not found:
            cps.append(or_entry)
        cfg["custom_providers"] = cps
        # DEFAULT model (chat + agents). Switchable live in the dropdown; override via OPENROUTER_DEFAULT_MODEL.
        cfg["model"] = {"provider": "openrouter", "base_url": OR_BASE,
                        "api_key": OR_KEY, "default": OR_DEFAULT}
        # Fallback on error -> OpenRouter auto-routing.
        cfg["fallback_providers"] = [{"provider": "openrouter", "model": "openrouter/auto",
                                      "base_url": OR_BASE, "api_key": OR_KEY}]
        # VISION model: agents "look" at Storage images to caption them. Use CHEAP gemini flash
        # (vision-capable) instead of the pricier main model. Also point the other light auxiliary
        # tasks (titles/extraction) at it to keep costs down.
        aux = cfg.get("auxiliary") if isinstance(cfg.get("auxiliary"), dict) else {}
        _flash = {"provider": "openrouter", "model": "google/gemini-2.5-flash",
                  "base_url": OR_BASE, "api_key": OR_KEY}
        for _slot in ("vision", "web_extract", "title_generation"):
            aux[_slot] = dict(_flash)
        cfg["auxiliary"] = aux
    try:
        os.makedirs(home, exist_ok=True)
        yaml.safe_dump(cfg, open(p, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
        done.append(os.path.basename(home) if home != HOME else "default")
    except Exception:
        pass
print("== mcp_setup: direct-bin servers, profiles:", ", ".join(done), "==")

# NOTE: agent (cron) models are NOT auto-forced here anymore. Set each agent's model in the
# Model Routing tab (/static/model-config.html) or Scheduled Jobs — that's the source of truth.
# Optional one-shot ONLY: if MIGRATE_AGENT_MODEL is set, rewrite crons pointing at a now-removed
# provider (apipod*) to it, so no agent is left on a dead provider. Never touches your chosen models.
_mig = os.environ.get("MIGRATE_AGENT_MODEL", "").strip()
if _mig:
    import glob as _cg, json as _cj
    _seen_jf = set()
    for _pat in (os.path.join(HOME, "cron", "jobs.json"), os.path.join(HOME, "**", "cron", "jobs.json")):
        for jf in _cg.glob(_pat, recursive=True):
            if jf in _seen_jf:
                continue
            _seen_jf.add(jf)
            try:
                _d = _cj.load(open(jf, encoding="utf-8"))
                _jobs = _d.get("jobs") if isinstance(_d, dict) else _d
                _ch = False
                for _jb in (_jobs or []):
                    _m = str(_jb.get("model") or "").lower() if isinstance(_jb, dict) else ""
                    if _m.startswith("apipod") or _m.startswith("claude-"):  # dead APIPod providers only
                        _jb["model"] = _mig
                        _ch = True
                if _ch:
                    _cj.dump(_d, open(jf, "w", encoding="utf-8"), indent=2)
                    print("== migrated dead-provider agents -> %s in %s ==" % (_mig, jf))
            except Exception:
                pass

# ---- Heal workspace paths: /app/<x> (ephemeral, wiped on redeploy) -> /workspace/<x> (persistent) ----
# Spaces saved with an absolute /app path fail with "Path does not exist" after a redeploy.
import glob as _glob, json as _json
VOL = os.path.join(HOME, "workspace")  # the persistent volume workspace root
def _to_vol(pth):
    """Rewrite an ephemeral /app/* or /workspace/* path onto the persistent volume."""
    for pre in ("/app/", "/workspace/"):
        if pth.startswith(pre) and not pth.startswith(VOL):
            return os.path.join(VOL, os.path.basename(pth.rstrip("/")))
    return pth
def _heal_workspaces():
    os.makedirs(VOL, exist_ok=True)
    wfiles = set(_glob.glob(os.path.join(HOME, "**", "workspaces.json"), recursive=True))
    sd = os.environ.get("HERMES_WEBUI_STATE_DIR")
    if sd:
        wfiles.add(os.path.join(sd, "workspaces.json"))
    healed = 0
    for wf in wfiles:
        try:
            data = _json.load(open(wf, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        ch = False
        for e in data:
            if not isinstance(e, dict):
                continue
            pth = str(e.get("path") or "")
            nv = _to_vol(pth)
            if nv != pth:
                e["path"] = nv
                ch = True
            if e.get("path"):
                try:
                    os.makedirs(e["path"], exist_ok=True)
                except Exception:
                    pass
        if ch:
            try:
                _json.dump(data, open(wf, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                healed += 1
            except Exception:
                pass
    for lf in _glob.glob(os.path.join(HOME, "**", "last_workspace.txt"), recursive=True):
        try:
            v = open(lf, encoding="utf-8").read().strip()
            nv = _to_vol(v)
            if nv != v:
                os.makedirs(nv, exist_ok=True)
                open(lf, "w", encoding="utf-8").write(nv)
        except Exception:
            pass
    print("== workspace heal: rewrote %d file(s) to volume (%s) ==" % (healed, VOL))
try:
    _heal_workspaces()
except Exception:
    pass

# ---- Heal skills: fold any agent-created local 'marketer' category into 'marketing' ----
# The agent sometimes authors skills under <profile>/skills/marketer/* which then show as a
# separate "MARKETER" group. The user wants one "MARKETING" group, so move them.
import shutil as _shutil
def _heal_skill_categories():
    for home in homes():
        sk_dir = os.path.join(home, "skills")
        src = os.path.join(sk_dir, "marketer")
        if not os.path.isdir(src):
            continue
        dst = os.path.join(sk_dir, "marketing")
        os.makedirs(dst, exist_ok=True)
        for name in os.listdir(src):
            try:
                target = os.path.join(dst, name)
                if os.path.exists(target):
                    continue
                _shutil.move(os.path.join(src, name), target)
            except Exception:
                pass
        try:
            os.rmdir(src)  # only succeeds if now empty
        except Exception:
            pass
    print("== skill heal: folded local marketer -> marketing ==")
try:
    _heal_skill_categories()
except Exception:
    pass

# ---- Prune OLD agent-created marketing skills (the legacy 4-agent system + duplicate playbook/
# zernio docs). Superseded by the 8-agent bundle: agency-8-agents + meta-ads-playbook-2026 (external
# /opt/skills-mkt). These legacy skills were authored by the agent and live on the volume under
# <home>/skills/**, so the Dockerfile bundle can't remove them — prune by name here. Idempotent;
# matches BOTH the folder basename and the SKILL.md `name:` field so renames/category moves still hit. ----
_KILL_SKILLS = {
    "hermes-4agent-ads-system",
    "peningbot-peninglab-marketing-playbook",
    "zernio-ads-rest-api",
    "zernio-meta-ads-patterns", "zernio-meta-patterns",
    "agent2-actor-4agent-flow",
    "agent3-reporter-4agent-flow",
    "agent4-marketing-intel-4agent-flow",
    "hermes-fb-ads-marketing",
}
def _skill_name(skill_md):
    try:
        for ln in open(skill_md, encoding="utf-8"):
            s = ln.strip()
            if s.lower().startswith("name:"):
                return s.split(":", 1)[1].strip().strip('"').strip("'").lower()
            if s and not s.startswith("---") and ":" not in s:
                break  # past the frontmatter
    except Exception:
        pass
    return ""
def _prune_old_skills():
    removed = []
    # Agent-created skills aren't always under <home>/skills — they may live in the webui
    # state dir (~/.hermes/webui/**) or elsewhere on the volume. Scan the whole ~/.hermes tree
    # (+ the state dir) recursively for any SKILL.md whose folder/name is on the denylist.
    roots = {HOME}
    sd = os.environ.get("HERMES_WEBUI_STATE_DIR")
    if sd:
        roots.add(sd)
    seen = set()
    for root in roots:
        if not os.path.isdir(root):
            continue
        for md in _glob.glob(os.path.join(root, "**", "SKILL.md"), recursive=True):
            if md in seen:
                continue
            seen.add(md)
            low = md.replace("\\", "/").lower()
            # don't traverse user project files / dep trees
            if "/workspace/" in low or "/node_modules/" in low or "/.git/" in low:
                continue
            d = os.path.dirname(md)
            base = os.path.basename(d).lower()
            nm = _skill_name(md)
            if base in _KILL_SKILLS or (nm and nm in _KILL_SKILLS):
                try:
                    _shutil.rmtree(d)
                    removed.append(base or nm)
                except Exception:
                    pass
    print("== skill prune: removed %d legacy skill(s): %s ==" % (len(removed), ", ".join(removed) or "none"))
try:
    _prune_old_skills()
except Exception:
    pass

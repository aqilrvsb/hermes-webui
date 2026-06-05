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
MKT_TOOLS = [
 "ad_audiences_list_ad_audiences","ad_audiences_create_ad_audience","ad_audiences_get_ad_audience","ad_audiences_delete_ad_audience","ad_audiences_add_users_to_ad_audience",
 "ad_campaigns_list_ad_campaigns","ad_campaigns_update_ad_campaign_status","ad_campaigns_update_ad_campaign","ad_campaigns_delete_ad_campaign","ad_campaigns_bulk_update_ad_campaign_status","ad_campaigns_duplicate_ad_campaign","ad_campaigns_update_ad_set","ad_campaigns_update_ad_set_status","ad_campaigns_get_ad_tree","ad_campaigns_get_ads_timeline",
 "ads_list_ads","ads_get_ad","ads_update_ad","ads_delete_ad","ads_get_ad_analytics","ads_get_ad_comments","ads_list_ads_business_centers","ads_list_ad_accounts","ads_boost_post","ads_create_standalone_ad","ads_create_ctwa_ad",
 "ads_list_leads","ads_list_lead_forms","ads_create_lead_form","ads_get_lead_form","ads_archive_lead_form","ads_list_form_leads","ads_create_test_lead",
 "ads_search_ad_interests","ads_search_ad_targeting","ads_estimate_ad_reach",
 "ads_send_conversions","ads_list_conversion_destinations","ads_create_conversion_destination","ads_get_conversion_destination","ads_update_conversion_destination","ads_delete_conversion_destination","ads_list_conversion_associations","ads_add_conversion_associations","ads_remove_conversion_associations","ads_get_conversion_metrics",
 "analytics_get_analytics","analytics_get_facebook_page_insights","analytics_get_instagram_account_insights","analytics_get_tik_tok_account_insights","analytics_get_daily_metrics","analytics_get_best_time_to_post","analytics_get_post_timeline","analytics_get_content_decay",
 "accounts_list","accounts_list_accounts","accounts_get_account_health","accounts_get_all_accounts_health",
 "connect_ads","connect_get_connect_url","connect_list_facebook_pages","connect_select_facebook_page",
 "contacts_create_contact","contacts_list_contacts","contacts_get_contact","contacts_bulk_create_contacts",
 "messages_list_inbox_conversations","messages_create_inbox_conversation","messages_send_inbox_message","messages_get_inbox_conversation_messages",
 "broadcasts_list_broadcasts","broadcasts_create_broadcast","broadcasts_add_broadcast_recipients","broadcasts_send_broadcast","broadcasts_schedule_broadcast",
 "whatsapp_get_whats_app_templates","whatsapp_create_whats_app_template","whatsapp_get_whats_app_business_profile","whatsapp_phone_numbers_get_whats_app_phone_numbers",
]
# Trim railway to deploy-relevant tools (was 150 -> ~30) to cut startup load + tool bloat
RAILWAY_TOOLS = [
 "project_list","project_info","project_create","project_environments",
 "service_list","service_info","service_create_from_repo","service_create_from_image","service_update","service_delete","service_restart",
 "deployment_list","deployment_trigger","deployment_logs","deployment_status",
 "environment_list","environment_info","environment_create",
 "domain_list","domain_create","domain_update","domain_delete","custom_domain_list","custom_domain_create",
 "variable_set","variable_delete","variable_bulk_set","list_service_variables",
 "volume_list","volume_create","volume_update","logs_build","logs_deployment","logs_http","metrics_get",
 "github_repo_list","github_repo_deploy","github_repo_link","database_list_types","database_deploy_from_template",
]
servers = {
    "supabase":  {"command": BIN+"mcp-server-supabase", "args": [], "env": E("SUPABASE_ACCESS_TOKEN")},
    "github":    {"command": BIN+"mcp-server-github",    "args": [], "env": E("GITHUB_PERSONAL_ACCESS_TOKEN")},
    "agentql":   {"command": BIN+"agentql-mcp",          "args": [], "env": E("AGENTQL_API_KEY")},
    "railway":   {"command": BIN+"railway-mcp",          "args": [], "env": E("RAILWAY_API_TOKEN","RAILWAY_TOKEN"), "tools": {"include": RAILWAY_TOOLS}},
    # vercel: NO MCP server. The vercel-mcp npm package exits on launch (failed every boot).
    # Developer role deploys via the Vercel CLI instead (baked into image, VERCEL_TOKEN in env) -> fully headless, reliable.
    "peninglab": {"command": BIN+"peninglab-mcp",        "args": [], "env": E("PENINGLAB_API_KEY"), "timeout": 900, "connect_timeout": 60},  # generate_* BLOCK minutes; default 120s MCP timeout cut them off + charged credits
    "zernio":    {"url": "https://mcp.zernio.com/mcp", "headers": {"Authorization": "Bearer %s" % (os.environ.get("ZERNIO_API_KEY") or "${ZERNIO_API_KEY}")}, "tools": {"include": MKT_TOOLS}},
    "playwright":{"command": BIN+"playwright-mcp", "args": ["--headless","--browser","chromium","--no-sandbox"], "env": dict(E(), PLAYWRIGHT_BROWSERS_PATH="/opt/pw-browsers")},
}
# Per-profile skill scoping: each role sees ONLY its relevant skills (cleaner Skills tab).
# Dirs are category-preserving bundles built in Dockerfile.railway.
# /opt/skills-common holds skills EVERY profile should have (e.g. whatsapp-whacenter messaging).
COMMON = ["/opt/skills-common"]
# GENERAL = superpowers, shared to EVERY profile. marketer also gets it now (user: "full general across profile").
SKILLS_BY_PROFILE = {
    "marketer":  ["/opt/skills/superpowers/skills", "/opt/skills-mkt"] + COMMON,   # general + marketing + meta-ads + messaging
    "developer": ["/opt/skills/superpowers/skills", "/opt/skills-dev"] + COMMON,   # general + dev + cavecrew + messaging
}
SKILLS_DEFAULT = ["/opt/skills/superpowers/skills", "/opt/skills-extra"] + COMMON  # default = everything + messaging
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
    # ── GRSAI as the model provider (OpenAI-compatible; GPT-5.5/5.4 + Gemini 3.x/2.5, cheap),
    # with OpenRouter as the cascade fallback. Stored in THIS config.yaml on the volume (editable
    # in Hermes, model switchable live from the chat dropdown). Keys are env-refs (never hit git).
    # Gated on GRSAI_API_KEY existing -> safe rollback (remove the env var to fall back to minimax).
    #   grsai      -> https://grsaiapi.com/v1  (key ${GRSAI_API_KEY})  [GPT + Gemini; Gemini = vision]
    #   openrouter -> fallback on error        (key ${OPENROUTER_API_KEY})
    # MAIN (chat + agents) = grsai/gpt-5.5 ; image/PDF -> a gemini-* model (cheap, multimodal).
    if os.environ.get("GRSAI_API_KEY", "").strip():
        GRSAI_BASE = "https://grsaiapi.com/v1"
        OR_BASE = "https://openrouter.ai/api/v1"
        GRSAI_MODELS = ["gpt-5.5", "gpt-5.4",
                        "gemini-3.1-pro", "gemini-3.1-flash-lite", "gemini-3.5-flash",
                        "gemini-3-pro", "gemini-3-flash", "gemini-2.5-pro", "gemini-2.5-flash"]
        cps = [c for c in (cfg.get("custom_providers") or [])
               if isinstance(c, dict) and str(c.get("name") or "").lower()
               not in ("apipod", "apipod-gpt")]   # drop the old APIPod providers
        have = {str(c.get("name") or "").lower() for c in cps if isinstance(c, dict)}
        if "grsai" not in have:
            cps.append({"name": "grsai", "base_url": GRSAI_BASE,
                        "api_key": "${GRSAI_API_KEY}", "models": GRSAI_MODELS})
        if "openrouter" not in have:
            cps.append({"name": "openrouter", "base_url": OR_BASE, "api_key": "${OPENROUTER_API_KEY}"})
        cfg["custom_providers"] = cps
        # MAIN (chat default) = GRSAI gpt-5.5. Switch live per-chat in the dropdown —
        # e.g. pick gemini-2.5-flash / gemini-3.1-pro for image/PDF reading (cheap vision).
        cfg["model"] = {"provider": "grsai", "base_url": GRSAI_BASE,
                        "api_key": "${GRSAI_API_KEY}", "default": "gpt-5.5"}
        # FALLBACK on any provider error -> OpenRouter (applies to chat AND agents).
        cfg["fallback_providers"] = [
            {"provider": "openrouter", "model": "openrouter/auto", "base_url": OR_BASE,
             "api_key": "${OPENROUTER_API_KEY}"},
        ]
    try:
        os.makedirs(home, exist_ok=True)
        yaml.safe_dump(cfg, open(p, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
        done.append(os.path.basename(home) if home != HOME else "default")
    except Exception:
        pass
print("== mcp_setup: direct-bin servers, profiles:", ", ".join(done), "==")

# ── ALL AGENTS -> GPT-5.5 (GRSAI). One-time migration: rewrite any cron still on the OLD minimax
# default to the agent model. Only touches minimax/* models, so a model you later pick per-agent in
# the Scheduled Jobs UI is preserved. Gated on GRSAI_API_KEY (so we only switch when the provider works).
if os.environ.get("GRSAI_API_KEY", "").strip():
    import glob as _cg, json as _cj
    AGENT_MODEL = os.environ.get("AGENT_MODEL", "gpt-5.5").strip()
    _seen_jf = set()
    for _pat in (os.path.join(HOME, "cron", "jobs.json"),
                 os.path.join(HOME, "**", "cron", "jobs.json")):
        for jf in _cg.glob(_pat, recursive=True):
            if jf in _seen_jf:
                continue
            _seen_jf.add(jf)
            try:
                _d = _cj.load(open(jf, encoding="utf-8"))
                _jobs = _d.get("jobs") if isinstance(_d, dict) else _d
                _ch = False
                for _jb in (_jobs or []):
                    if isinstance(_jb, dict) and str(_jb.get("model") or "").lower().startswith("minimax"):
                        _jb["model"] = AGENT_MODEL
                        _ch = True
                if _ch:
                    _cj.dump(_d, open(jf, "w", encoding="utf-8"), indent=2)
                    print("== agents -> %s in %s ==" % (AGENT_MODEL, jf))
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

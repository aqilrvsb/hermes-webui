# Runs at container boot. Merges MCP servers + external skills into ~/.hermes/config.yaml.
# Tokens are read from the environment at boot, so adding a Railway env var + restart
# activates that server (no rebuild needed).
import os
try:
    import yaml
except Exception:
    raise SystemExit(0)
H = os.path.expanduser("~/.hermes")
p = os.path.join(H, "config.yaml")
cfg = {}
if os.path.exists(p):
    try:
        cfg = yaml.safe_load(open(p, encoding="utf-8").read()) or {}
    except Exception:
        cfg = {}
if not isinstance(cfg, dict):
    cfg = {}
NB = "/opt/node/bin"
NPX = NB + "/npx"
PATHV = NB + ":" + os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")
def E(*keys):
    e = {"PATH": PATHV}
    for k in keys:
        v = os.environ.get(k)
        if v:
            e[k] = v
    return e
ADS_TOOLS = ['ad_audiences_list_ad_audiences', 'ad_audiences_create_ad_audience', 'ad_audiences_get_ad_audience', 'ad_audiences_delete_ad_audience', 'ad_audiences_add_users_to_ad_audience', 'ad_campaigns_list_ad_campaigns', 'ad_campaigns_update_ad_campaign_status', 'ad_campaigns_update_ad_campaign', 'ad_campaigns_delete_ad_campaign', 'ad_campaigns_bulk_update_ad_campaign_status', 'ad_campaigns_duplicate_ad_campaign', 'ad_campaigns_update_ad_set', 'ad_campaigns_update_ad_set_status', 'ad_campaigns_get_ad_tree', 'ad_campaigns_get_ads_timeline', 'ads_list_ads', 'ads_get_ad', 'ads_update_ad', 'ads_delete_ad', 'ads_get_ad_analytics', 'ads_get_ad_comments', 'ads_list_ads_business_centers', 'ads_list_ad_accounts', 'ads_boost_post', 'ads_create_standalone_ad', 'ads_create_ctwa_ad', 'ads_list_leads', 'ads_list_lead_forms', 'ads_create_lead_form', 'ads_get_lead_form', 'ads_archive_lead_form', 'ads_list_form_leads', 'ads_create_test_lead', 'ads_search_ad_interests', 'ads_search_ad_targeting', 'ads_estimate_ad_reach', 'ads_send_conversions', 'ads_list_conversion_destinations', 'ads_create_conversion_destination', 'ads_get_conversion_destination', 'ads_update_conversion_destination', 'ads_delete_conversion_destination', 'ads_list_conversion_associations', 'ads_add_conversion_associations', 'ads_remove_conversion_associations', 'ads_get_conversion_metrics', 'connect_ads']
servers = {
    "supabase": {"command": NPX, "args": ["-y", "--prefer-offline", "@supabase/mcp-server-supabase@latest"], "env": E("SUPABASE_ACCESS_TOKEN")},
    "github": {"command": NPX, "args": ["-y", "--prefer-offline", "@modelcontextprotocol/server-github"], "env": E("GITHUB_PERSONAL_ACCESS_TOKEN")},
    "agentql": {"command": NPX, "args": ["-y", "--prefer-offline", "agentql-mcp"], "env": E("AGENTQL_API_KEY")},
    "railway": {"command": NPX, "args": ["-y", "--prefer-offline", "railway-mcp"], "env": E("RAILWAY_API_TOKEN", "RAILWAY_TOKEN")},
    "vercel": {"command": NPX, "args": ["-y", "--prefer-offline", "vercel-mcp"], "env": E("VERCEL_TOKEN", "VERCEL_API_TOKEN")},
    "zernio": {"url": "https://mcp.zernio.com/mcp", "headers": {"Authorization": "Bearer %s" % (os.environ.get("ZERNIO_API_KEY") or "${ZERNIO_API_KEY}")}, "tools": {"include": ADS_TOOLS}},
    "peninglab": {"command": NPX, "args": ["-y", "--prefer-offline", "peninglab-mcp"], "env": E("PENINGLAB_API_KEY")},
    "playwright": {"command": NPX, "args": ["-y", "--prefer-offline", "@playwright/mcp@latest", "--headless", "--browser", "chromium", "--no-sandbox"], "env": dict(E(), PLAYWRIGHT_BROWSERS_PATH="/opt/pw-browsers")},
}
existing = cfg.get("mcp_servers") or {}
existing.pop("meta_ads", None)        # drop deprecated server, keep everything else
existing.update(servers)              # refresh our managed servers; preserve user-added ones
cfg["mcp_servers"] = existing
sk = cfg.get("skills") or {}
ed = sk.get("external_dirs") or []
for d in ("/opt/skills/superpowers/skills", "/opt/skills-extra"):
    if d not in ed:
        ed.append(d)
sk["external_dirs"] = ed
cfg["skills"] = sk
yaml.safe_dump(cfg, open(p, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
print("== mcp_setup: 8 servers + external skills written ==")

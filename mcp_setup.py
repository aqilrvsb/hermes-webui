# Runs at boot. Writes mcp_servers + skills.external_dirs into EVERY profile's config.yaml
# (default + ~/.hermes/profiles/*), so all roles get the same tools + skills.
# Tokens are read from env at boot, so adding a Railway var + restart activates a server.
import os
try:
    import yaml
except Exception:
    raise SystemExit(0)
HOME = os.path.expanduser("~/.hermes")
NB = "/opt/node/bin"; NPX = NB + "/npx"
PATHV = NB + ":" + os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")
def E(*keys):
    e = {"PATH": PATHV}
    for k in keys:
        v = os.environ.get(k)
        if v:
            e[k] = v
    return e
# Zernio tools for the marketer role: ADS + ANALYTICS + WhatsApp/messaging (reporting) + accounts/connect
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
servers = {
    "supabase": {"command": NPX, "args": ["-y", "--prefer-offline", "@supabase/mcp-server-supabase@latest"], "env": E("SUPABASE_ACCESS_TOKEN")},
    "github": {"command": NPX, "args": ["-y", "--prefer-offline", "@modelcontextprotocol/server-github"], "env": E("GITHUB_PERSONAL_ACCESS_TOKEN")},
    "agentql": {"command": NPX, "args": ["-y", "--prefer-offline", "agentql-mcp"], "env": E("AGENTQL_API_KEY")},
    "railway": {"command": NPX, "args": ["-y", "--prefer-offline", "railway-mcp"], "env": E("RAILWAY_API_TOKEN", "RAILWAY_TOKEN")},
    "vercel": {"command": NPX, "args": ["-y", "--prefer-offline", "vercel-mcp"], "env": E("VERCEL_TOKEN", "VERCEL_API_TOKEN")},
    "peninglab": {"command": NPX, "args": ["-y", "--prefer-offline", "peninglab-mcp"], "env": E("PENINGLAB_API_KEY")},
    "zernio": {"url": "https://mcp.zernio.com/mcp", "headers": {"Authorization": "Bearer %s" % (os.environ.get("ZERNIO_API_KEY") or "${ZERNIO_API_KEY}")}, "tools": {"include": MKT_TOOLS}},
    "playwright": {"command": NPX, "args": ["-y", "--prefer-offline", "@playwright/mcp@latest", "--headless", "--browser", "chromium", "--no-sandbox"], "env": dict(E(), PLAYWRIGHT_BROWSERS_PATH="/opt/pw-browsers")},
}
EXT_SKILLS = ["/opt/skills/superpowers/skills", "/opt/skills-extra"]
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
    ex.update(servers)
    cfg["mcp_servers"] = ex
    sk = cfg.get("skills") or {}
    ed = sk.get("external_dirs") or []
    for d in EXT_SKILLS:
        if d not in ed:
            ed.append(d)
    sk["external_dirs"] = ed
    cfg["skills"] = sk
    try:
        os.makedirs(home, exist_ok=True)
        yaml.safe_dump(cfg, open(p, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
        done.append(os.path.basename(home) if home != HOME else "default")
    except Exception:
        pass
print("== mcp_setup: configured profiles:", ", ".join(done), "==")

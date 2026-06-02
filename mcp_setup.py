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
servers = {
    "supabase": {"command": NPX, "args": ["-y", "@supabase/mcp-server-supabase@latest"], "env": E("SUPABASE_ACCESS_TOKEN")},
    "github": {"command": NPX, "args": ["-y", "@modelcontextprotocol/server-github"], "env": E("GITHUB_PERSONAL_ACCESS_TOKEN")},
    "agentql": {"command": NPX, "args": ["-y", "agentql-mcp"], "env": E("AGENTQL_API_KEY")},
    "railway": {"command": NPX, "args": ["-y", "railway-mcp"], "env": E("RAILWAY_API_TOKEN", "RAILWAY_TOKEN")},
    "vercel": {"command": NPX, "args": ["-y", "vercel-mcp"], "env": E("VERCEL_TOKEN", "VERCEL_API_TOKEN")},
    "meta_ads": {"command": NPX, "args": ["-y", "meta-ads-mcp"], "env": E("META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID", "META_PAGE_ID", "META_APP_ID", "META_APP_SECRET")},
    "zernio": {"url": "https://mcp.zernio.com/mcp", "headers": {"Authorization": "Bearer %s" % (os.environ.get("ZERNIO_API_KEY") or "${ZERNIO_API_KEY}")}},
    "playwright": {"command": NPX, "args": ["-y", "@playwright/mcp@latest", "--headless", "--browser", "chromium", "--no-sandbox"], "env": dict(E(), PLAYWRIGHT_BROWSERS_PATH="/opt/pw-browsers")},
}
m = cfg.get("mcp_servers") or {}
m.update(servers)
cfg["mcp_servers"] = m
sk = cfg.get("skills") or {}
ed = sk.get("external_dirs") or []
for d in ("/opt/skills/superpowers/skills", "/opt/skills-extra"):
    if d not in ed:
        ed.append(d)
sk["external_dirs"] = ed
cfg["skills"] = sk
yaml.safe_dump(cfg, open(p, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
print("== mcp_setup: 8 servers + external skills written ==")

"""SaaS layer — Hermes Social Posting Manager (100% GoLogin + Supabase).

1 client = 1 Supabase auth user = 1 Hermes profile (+workspace) = 1 GoLogin cloud
browser profile with a Malaysia-RESIDENTIAL proxy. Admin keys live in Supabase
admin_settings (NEVER in git). This module provides:

  auth:      /api/saas/register /api/saas/login /api/saas/logout /api/saas/me
  admin:     /api/saas/admin/settings (GET/POST)  /api/saas/admin/clients
  social:    /api/social/status /connect /check /stop   (GoLogin cloud browser)
  reporting: /api/reports/posts  (Supabase posts + profile-local jsonl)

Session→client binding is SERVER-side (.saas_sessions.json keyed by the hermes
session cookie hash), so a tampered hermes_profile cookie can never cross tenants:
bind_profile() re-forces the thread-local profile from the server-side mapping.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

from api.auth import create_session, parse_cookie, set_auth_cookie, invalidate_session
from api.config import STATE_DIR
from api.helpers import j, bad, get_profile_cookie_name
from api.profiles import (
    set_request_profile,
    _resolve_profile_home_for_name,
    create_profile_api,
)

logger = logging.getLogger(__name__)

_SOCIAL_PLATFORMS = ("facebook", "threads", "tiktok", "instagram")
_MAX_PROFILES = 10          # each client can utilise their full BYO GoLogin plan (10 identities)
_GOLOGIN_API = "https://api.gologin.com"
_SETTINGS_CACHE: dict = {"at": 0.0, "data": {}}
_SESS_LOCK = threading.Lock()


# ── Supabase REST ────────────────────────────────────────────────────────────

def _supa_env():
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    service = (os.environ.get("SUPABASE_SERVICE_KEY") or "").strip()
    anon = (os.environ.get("SUPABASE_ANON_KEY") or service).strip()
    return url, service, anon


def _supa(method, path, payload=None, key="service", prefer=None):
    url, service, anon = _supa_env()
    if not url or not service:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_KEY not set")
    k = service if key == "service" else anon
    req = urllib.request.Request(url + path, method=method)
    req.add_header("apikey", k)
    req.add_header("Authorization", "Bearer " + k)
    req.add_header("Content-Type", "application/json")
    if prefer:
        req.add_header("Prefer", prefer)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:  # noqa: PERF203
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw[:400]}


# ── Admin settings (Supabase admin_settings; env fallback) ──────────────────

def settings_all(max_age=60.0) -> dict:
    now = time.time()
    if now - _SETTINGS_CACHE["at"] < max_age and _SETTINGS_CACHE["data"]:
        return _SETTINGS_CACHE["data"]
    try:
        st, rows = _supa("GET", "/rest/v1/admin_settings?select=key,value")
        if st == 200 and isinstance(rows, list):
            _SETTINGS_CACHE["data"] = {r["key"]: r.get("value") or "" for r in rows}
            _SETTINGS_CACHE["at"] = now
    except Exception as e:  # noqa: BLE001
        logger.warning("settings fetch failed: %s", e)
    return _SETTINGS_CACHE["data"]


def setting(key: str, default: str = "") -> str:
    env = (os.environ.get(key.upper()) or "").strip()
    if env:
        return env
    return (settings_all().get(key) or default).strip()


def _gologin_token() -> str:
    return setting("gologin_token") or (os.environ.get("GOLOGIN_API_TOKEN") or "").strip()


# ── GoLogin REST ─────────────────────────────────────────────────────────────

def _gologin(method, path, payload=None, timeout=60):
    tok = _gologin_token()
    if not tok:
        raise RuntimeError("gologin_token not set (Admin Settings)")
    req = urllib.request.Request(_GOLOGIN_API + path, method=method)
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw[:400]}


def gologin_create_client_profile(email: str) -> str:
    """Create the client's ONE GoLogin profile + attach the MY residential proxy."""
    st, prof = _gologin("POST", "/browser/quick", {"os": "win", "name": email})
    if st not in (200, 201):
        raise RuntimeError("gologin profile create failed (%s): %s" % (st, prof))
    pid = prof.get("id") or prof.get("_id") or ""
    if not pid:
        raise RuntimeError("gologin returned no profile id")
    country = setting("gologin_proxy_country", "MY") or "MY"
    _cname = {"MY": "Malaysia"}.get(country.upper(), country.upper())
    st2, px = _gologin("POST", "/users-proxies/mobile-proxy", {
        "countryCode": country, "isDc": False, "isMobile": False,
        "profileIdToLink": pid, "customName": _cname,   # best-effort clean dashboard label
    })
    if st2 not in (200, 201):
        # profile exists but proxy failed — keep the profile, surface the warning
        logger.warning("gologin proxy attach failed (%s): %s", st2, px)
    return pid


# ── Server-side session→client mapping (tamper-proof profile binding) ───────

def _sess_path() -> Path:
    return Path(STATE_DIR) / ".saas_sessions.json"


def _sess_load() -> dict:
    try:
        with open(_sess_path(), encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _sess_save(d: dict) -> None:
    try:
        p = _sess_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = str(p) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, p)
        try:
            os.chmod(p, 0o600)
        except Exception:
            pass
    except Exception as e:  # noqa: BLE001
        logger.warning("saas session save failed: %s", e)


def _cookie_key(cookie_value: str) -> str:
    return hashlib.sha256(cookie_value.encode("utf-8")).hexdigest()


def _sess_put(cookie_value: str, info: dict) -> None:
    with _SESS_LOCK:
        d = _sess_load()
        now = time.time()
        # prune expired (30d) + cap
        d = {k: v for k, v in d.items() if (v.get("exp") or 0) > now}
        info["exp"] = now + 30 * 86400
        d[_cookie_key(cookie_value)] = info
        _sess_save(d)


def session_info(handler) -> dict | None:
    cookie_value = parse_cookie(handler)
    if not cookie_value:
        return None
    info = _sess_load().get(_cookie_key(cookie_value))
    if info and (info.get("exp") or 0) > time.time():
        return info
    return None


def bind_profile(handler) -> dict | None:
    """Force the request's profile from the SERVER-side session mapping.

    Called at the top of every routes dispatch. Overrides whatever the
    (client-editable) hermes_profile cookie said, so tenants can't cross."""
    info = session_info(handler)
    if info and info.get("profile"):
        set_request_profile(info["profile"])
    return info


def require_admin(handler) -> dict | None:
    info = session_info(handler)
    if info and info.get("is_admin"):
        return info
    bad(handler, "admin only", 403)
    return None


# ── Client provisioning ──────────────────────────────────────────────────────

def _slug(email: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", email.split("@")[0].lower()).strip("-")
    s = re.sub(r"-{2,}", "-", s) or "client"
    return ("c-" + s)[:40]


def _unique_slug(email: str) -> str:
    base = _slug(email)
    st, rows = _supa("GET", "/rest/v1/clients?select=hermes_profile&hermes_profile=like.%s*" % urllib.parse.quote(base))
    taken = {r.get("hermes_profile") for r in rows} if st == 200 and isinstance(rows, list) else set()
    if base not in taken:
        return base
    i = 2
    while ("%s-%d" % (base, i)) in taken:
        i += 1
    return "%s-%d" % (base, i)


def _client_soul(email: str, gologin_pid: str) -> str:
    return (
        "# SOUL — Social Media Agent for %s\n\n"
        "You are this client's personal social-media agent. Their ONE GoLogin cloud browser "
        "(profile id `%s`) is logged into their Facebook / Instagram / TikTok / Threads.\n\n"
        "## How you act on social media (posting, scraping, checking)\n"
        "Use the GoLogin helper CLI from the terminal. The helper is at /apptoo/gologin_helper.js "
        "($GOLOGIN_HELPER). If GOLOGIN_API_TOKEN / GOLOGIN_PROFILE_ID are not in your env, load them "
        "first from your profile home: `set -a; . ~/.hermes/profiles/*/.env 2>/dev/null || . $HERMES_HOME/.env; set +a` "
        "(they are written in your profile's .env file).\n"
        "- Check logins:   `node $GOLOGIN_HELPER login-status`\n"
        "- Pull the next unused image from the client's Storage for your platform:\n"
        "    `node $GOLOGIN_HELPER next-image <platform>`  -> JSON {image:{mediaId,path,url,filename}} or {image:null}\n"
        "- Post it (auto-marks the image done for that platform + logs to Reporting):\n"
        "    write the caption to a file, then `node $GOLOGIN_HELPER post <platform> /path/caption.txt <image.path> <mediaId>`\n"
        "- Scrape a page (logged-in view): `node $GOLOGIN_HELPER scrape <url> [css-selector]`\n"
        "- Screenshot:     `node $GOLOGIN_HELPER screenshot <url> /path/out.png`\n"
        "Every successful post is auto-logged for the Reporting tab and stamped on the Storage image.\n\n"
        "## You have two sides: THINKING (fixed) + EXECUTION (grows)\n"
        "THINKING = your task, content and behaviour above — this is FIXED and defines you; it never "
        "changes from experience. EXECUTION = your own private memory of HOW to operate the site; it "
        "GROWS so you get smoother every run. They never mix.\n\n"
        "## Self-learning (EXECUTION only — get faster every run, stop hitting walls)\n"
        "You have your OWN execution memory (independent from every other agent). The `post` command "
        "automatically remembers the selectors that worked and reuses them next time (fast path), only "
        "re-discovering when the site changed. BEFORE you act on a platform, recall what you learned:\n"
        "  `node $GOLOGIN_HELPER get-notes <platform>`  -> {notes, runs, learned}\n"
        "If you hit something new (a popup to dismiss, a changed button label, a locale quirk), record "
        "it so future runs are smoother:\n"
        "  `node $GOLOGIN_HELPER add-note <platform> \"the lesson in one line\"`\n"
        "STRICT SCOPE — learning is for EXECUTION ONLY. Notes may ONLY describe how to operate the "
        "browser (selectors, buttons, popups, navigation steps, timing). NEVER record or change WHAT to "
        "post — topic, tone, language, hashtags, strategy or scope. Your content is fixed by your task "
        "and must not be altered by anything you learn. Get more expert at DOING the task, never at "
        "deciding the content.\n\n"
        "## Content creation\n"
        "Use the peninglab MCP tools (generate_image / generate_video) for creatives.\n\n"
        "## Rules\n"
        "- Work ONLY inside this client's workspace and browser. Never touch other clients' data.\n"
        "- Human pace: no mass actions, no spam. Quality posts only.\n"
        "- When asked to post 'now', do it immediately and reply with the post link.\n"
    ) % (email, gologin_pid)


def _write_profile_env(profile_home: Path, gologin_pid: str, client_id: str = "") -> None:
    """Give the client's agent its GoLogin + Storage env (helper path + ids)."""
    helper = os.environ.get("HERMES_GOLOGIN_HELPER") or "/apptoo/gologin_helper.js"
    url, service, _anon = _supa_env()
    lines = {
        "GOLOGIN_API_TOKEN": _gologin_token(),
        "GOLOGIN_PROFILE_ID": gologin_pid,
        "GOLOGIN_HELPER": helper,
        "CLIENT_ID": client_id,               # scopes Storage image queries to this client
        "SUPABASE_URL": url,
        "SUPABASE_SERVICE_KEY": service,
    }
    try:
        profile_home.mkdir(parents=True, exist_ok=True)
        envp = profile_home / ".env"
        existing = ""
        try:
            existing = envp.read_text(encoding="utf-8")
        except Exception:
            existing = ""
        out = [ln for ln in existing.splitlines()
               if not any(ln.startswith(k + "=") for k in lines)]
        out += ["%s=%s" % (k, v) for k, v in lines.items() if v]
        envp.write_text("\n".join(out) + "\n", encoding="utf-8")
        (profile_home / "SOUL.md").write_text(
            _client_soul(profile_home.name, gologin_pid), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        logger.warning("profile env write failed: %s", e)


def _apply_boot_config() -> None:
    """Re-run mcp_setup so a freshly created profile gets model + MCP config."""
    import sys
    for cand in ("/opt/mcp_setup.py", "/apptoo/mcp_setup.py", "/app/mcp_setup.py"):
        if os.path.exists(cand):
            try:
                subprocess.run([sys.executable, cand], timeout=60, capture_output=True)
            except Exception as e:  # noqa: BLE001
                logger.warning("mcp_setup re-run failed: %s", e)
            return


def provision_client(user_id: str, email: str) -> dict:
    """The full chain: Hermes profile+workspace -> GoLogin profile (MY residential) -> clients row."""
    prof = _unique_slug(email)
    try:
        create_profile_api(prof)
    except Exception as e:  # noqa: BLE001
        if "exists" not in str(e).lower():
            raise
    home = _resolve_profile_home_for_name(prof)
    # NO auto-created GoLogin profile — the client adds their own identities (named) in Social Connect.
    _write_profile_env(home, "", user_id)
    row = {"id": user_id, "email": email, "hermes_profile": prof,
           "gologin_profile_id": "",
           "is_admin": email.lower() in _admin_emails()}
    st, res = _supa("POST", "/rest/v1/clients", row,
                    prefer="resolution=merge-duplicates,return=representation")
    if st not in (200, 201):
        raise RuntimeError("clients insert failed (%s): %s" % (st, res))
    _apply_boot_config()
    return res[0] if isinstance(res, list) and res else row


def _admin_emails() -> set:
    raw = setting("admin_emails", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _client_by_id(user_id: str) -> dict | None:
    st, rows = _supa("GET", "/rest/v1/clients?select=*&id=eq." + urllib.parse.quote(user_id))
    if st == 200 and isinstance(rows, list) and rows:
        return rows[0]
    return None


# ── Auth endpoints ───────────────────────────────────────────────────────────

def _grant(handler, client: dict, payload_extra=None) -> None:
    """Issue the Hermes session + profile cookies and reply with the client info."""
    cookie_value = create_session()
    is_admin = bool(client.get("is_admin")) or (client.get("email", "").lower() in _admin_emails())
    _sess_put(cookie_value, {
        "id": client.get("id"), "email": client.get("email"),
        "profile": client.get("hermes_profile"),
        "gologin": client.get("gologin_profile_id") or "",
        "is_admin": is_admin,
    })
    payload = {"ok": True, "email": client.get("email"),
               "profile": client.get("hermes_profile"),
               "gologin_profile_id": client.get("gologin_profile_id") or "",
               "is_admin": is_admin}
    if payload_extra:
        payload.update(payload_extra)
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    # hermes_session (auth) — reuse core cookie writer for flags parity
    set_auth_cookie(handler, cookie_value)
    # hermes_profile (per-request profile context; server-side mapping still wins)
    secure = "; Secure" if (handler.headers.get("X-Forwarded-Proto", "") == "https") else ""
    handler.send_header("Set-Cookie",
                        "%s=%s; Path=/; Max-Age=%d; SameSite=Lax%s"
                        % (get_profile_cookie_name(), client.get("hermes_profile") or "default",
                           30 * 86400, secure))
    handler.end_headers()
    handler.wfile.write(body)


def saas_register(handler, body):
    email = str((body or {}).get("email") or "").strip().lower()
    password = str((body or {}).get("password") or "")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) or len(password) < 6:
        bad(handler, "valid email + password (min 6 chars) required", 400)
        return
    # Create the auth user (service role; no email-confirm friction)
    st, res = _supa("POST", "/auth/v1/admin/users",
                    {"email": email, "password": password, "email_confirm": True})
    if st in (400, 422) and "already" in json.dumps(res).lower():
        bad(handler, "email already registered — please log in", 409)
        return
    if st not in (200, 201):
        bad(handler, "signup failed (%s): %s" % (st, json.dumps(res)[:200]), 502)
        return
    user_id = res.get("id") or (res.get("user") or {}).get("id")
    if not user_id:
        bad(handler, "signup returned no user id", 502)
        return
    try:
        client = provision_client(user_id, email)
    except Exception as e:  # noqa: BLE001
        bad(handler, "provisioning failed: %s" % e, 502)
        return
    _grant(handler, client)


def saas_login(handler, body):
    email = str((body or {}).get("email") or "").strip().lower()
    password = str((body or {}).get("password") or "")
    if not email or not password:
        bad(handler, "email and password required", 400)
        return
    st, res = _supa("POST", "/auth/v1/token?grant_type=password",
                    {"email": email, "password": password}, key="anon")
    if st != 200:
        bad(handler, "invalid email or password", 401)
        return
    user_id = (res.get("user") or {}).get("id")
    if not user_id:
        bad(handler, "login returned no user", 502)
        return
    client = _client_by_id(user_id)
    if not client:
        # auth user exists but was never provisioned — heal now
        try:
            client = provision_client(user_id, email)
        except Exception as e:  # noqa: BLE001
            bad(handler, "provisioning failed: %s" % e, 502)
            return
    _grant(handler, client)


def saas_logout(handler):
    cookie_value = parse_cookie(handler)
    if cookie_value:
        try:
            invalidate_session(cookie_value)
        except Exception:
            pass
        with _SESS_LOCK:
            d = _sess_load()
            d.pop(_cookie_key(cookie_value), None)
            _sess_save(d)
    j(handler, {"ok": True})


def saas_me(handler):
    info = session_info(handler)
    if not info:
        j(handler, {"authenticated": False})
        return
    j(handler, {"authenticated": True, "email": info.get("email"),
                "profile": info.get("profile"),
                "gologin_profile_id": info.get("gologin"),
                "is_admin": bool(info.get("is_admin"))})


# ── Admin endpoints ──────────────────────────────────────────────────────────

# Admin manages: GoLogin token, shared OpenRouter + PeningLab keys, and each key's MODE.
# mode 'admin' -> every client uses the shared key; mode 'client' -> each client fills their own
# key in their Settings. (proxy country defaults to MY, admin_emails seeded server-side.)
_ADMIN_KEYS = ("gologin_token", "openrouter_key", "openrouter_mode",
               "peninglab_key", "peninglab_mode")

# Per-client key config: (admin_setting_mode, admin_setting_shared, clients_column)
_CLIENT_KEY_SPECS = {
    "openrouter": ("openrouter_mode", "openrouter_key", "openrouter_key"),
    "peninglab":  ("peninglab_mode", "peninglab_key", "peninglab_key"),
}


def _client_key_for(kind: str, client_info) -> str:
    """Resolve a client's key for `kind` (openrouter/peninglab) per the admin mode."""
    mode_k, shared_k, col = _CLIENT_KEY_SPECS[kind]
    if setting(mode_k, "admin") == "client" and client_info and client_info.get("id"):
        c = _client_by_id(client_info["id"])
        k = ((c or {}).get(col) or "").strip()
        if k:
            return k
    return setting(shared_k)


def openrouter_key_for(client_info) -> str:
    return _client_key_for("openrouter", client_info)


def saas_admin_settings_get(handler):
    if not require_admin(handler):
        return
    s = settings_all(max_age=0)
    out = {}
    for k in _ADMIN_KEYS:
        v = s.get(k) or ""
        # mask secrets in transit; POST with a new value to change
        out[k] = ("*" * 8 + v[-6:]) if ("token" in k or "key" in k) and len(v) > 10 else v
    j(handler, {"settings": out, "keys": list(_ADMIN_KEYS)})


def saas_admin_settings_post(handler, body):
    if not require_admin(handler):
        return
    updates = (body or {}).get("settings") or {}
    saved = []
    for k, v in updates.items():
        if k not in _ADMIN_KEYS or not isinstance(v, str) or v.startswith("********"):
            continue
        st, _res = _supa("POST", "/rest/v1/admin_settings",
                         {"key": k, "value": v.strip()},
                         prefer="resolution=merge-duplicates")
        if st in (200, 201):
            saved.append(k)
    _SETTINGS_CACHE["at"] = 0.0
    j(handler, {"ok": True, "saved": saved})


def saas_admin_clients(handler):
    if not require_admin(handler):
        return
    st, rows = _supa("GET", "/rest/v1/clients?select=id,email,hermes_profile,gologin_profile_id,is_admin,created_at&order=created_at.desc")
    j(handler, {"clients": rows if isinstance(rows, list) else []})


def saas_admin_user_create(handler, body):
    if not require_admin(handler):
        return
    email = str((body or {}).get("email") or "").strip().lower()
    password = str((body or {}).get("password") or "")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) or len(password) < 6:
        bad(handler, "valid email + password (min 6 chars) required", 400)
        return
    st, res = _supa("POST", "/auth/v1/admin/users",
                    {"email": email, "password": password, "email_confirm": True})
    if st in (400, 422) and "already" in json.dumps(res).lower():
        bad(handler, "email already registered", 409)
        return
    if st not in (200, 201):
        bad(handler, "create failed (%s): %s" % (st, json.dumps(res)[:200]), 502)
        return
    user_id = res.get("id") or (res.get("user") or {}).get("id")
    try:
        client = provision_client(user_id, email)
    except Exception as e:  # noqa: BLE001
        bad(handler, "provisioning failed: %s" % e, 502)
        return
    j(handler, {"ok": True, "client": client})


def saas_admin_user_delete(handler, body):
    if not require_admin(handler):
        return
    uid = str((body or {}).get("id") or "").strip()
    if not uid:
        bad(handler, "id required", 400)
        return
    c = _client_by_id(uid)
    if not c:
        bad(handler, "not found", 404)
        return
    if (c.get("email") or "").lower() in _admin_emails():
        bad(handler, "can't delete an admin account (remove from admin emails first)", 400)
        return
    # 1) delete their GoLogin cloud profile
    pid = c.get("gologin_profile_id") or ""
    if pid:
        try:
            _gologin("DELETE", "/browser/" + pid)
        except Exception as e:  # noqa: BLE001
            logger.warning("gologin delete failed for %s: %s", pid, e)
    # 2) delete the auth user -> clients/media/posts cascade (FK on delete cascade)
    st, _res = _supa("DELETE", "/auth/v1/admin/users/" + urllib.parse.quote(uid))
    if st not in (200, 204):
        # fall back to deleting the clients row directly
        _supa("DELETE", "/rest/v1/clients?id=eq." + urllib.parse.quote(uid))
    j(handler, {"ok": True})


def saas_admin_user_password(handler, body):
    if not require_admin(handler):
        return
    uid = str((body or {}).get("id") or "").strip()
    password = str((body or {}).get("password") or "")
    if not uid or len(password) < 6:
        bad(handler, "id + password (min 6) required", 400)
        return
    st, _res = _supa("PUT", "/auth/v1/admin/users/" + urllib.parse.quote(uid), {"password": password})
    j(handler, {"ok": st in (200, 204)})


# ── Per-client OpenRouter key (Settings tab, only in mode='client') ──────────

def saas_client_keys_get(handler):
    """Both BYO keys (openrouter + peninglab) for the current client's Settings section."""
    info = session_info(handler)
    if not info:
        bad(handler, "not logged in", 401)
        return
    c = _client_by_id(info.get("id") or "") or {}
    out = {}
    for kind, (mode_k, _shared, col) in _CLIENT_KEY_SPECS.items():
        mode = setting(mode_k, "admin")
        key = (c.get(col) or "").strip() if mode == "client" else ""
        out[kind] = {"mode": mode, "has_key": bool(key),
                     "masked": ("*" * 8 + key[-6:]) if len(key) > 10 else ""}
    j(handler, out)


def saas_client_keys_post(handler, body):
    info = session_info(handler)
    if not info:
        bad(handler, "not logged in", 401)
        return
    b = body or {}
    kind = str(b.get("kind") or "openrouter").strip()
    if kind not in _CLIENT_KEY_SPECS:
        bad(handler, "unknown key", 400)
        return
    mode_k, _shared, col = _CLIENT_KEY_SPECS[kind]
    if setting(mode_k, "admin") != "client":
        bad(handler, "this key is managed by the admin", 403)
        return
    key = str(b.get("key") or "").strip()
    if key and not key.startswith("sk-"):
        bad(handler, "that doesn't look like a valid key (starts with sk-)", 400)
        return
    st, _res = _supa("PATCH", "/rest/v1/clients?id=eq." + urllib.parse.quote(info.get("id") or ""),
                     {col: key})
    if st not in (200, 204):
        bad(handler, "save failed (%s)" % st, 502)
        return
    _apply_boot_config()   # rewrite this client's profile config with their key(s)
    j(handler, {"ok": True, "kind": kind, "has_key": bool(key)})


# ── Profiles (each client up to 10 identities) + Social Connect (GoLogin) ────

def _node_bin() -> str:
    for c in ("/opt/node/bin/node", "/usr/local/bin/node", "node"):
        if c == "node" or os.path.exists(c):
            return c
    return "node"


def _client_profiles(client_id: str) -> list:
    st, rows = _supa("GET", "/rest/v1/client_profiles?select=id,gologin_profile_id,name,created_at"
                     "&client_id=eq.%s&order=created_at" % urllib.parse.quote(client_id))
    return rows if (st == 200 and isinstance(rows, list)) else []


def _resolve_profile(handler, gologin_pid: str = ""):
    """Return (info, gologin_pid, profile_row). Validates the pid belongs to the client;
    defaults to their first profile. Legacy fallback to clients.gologin_profile_id."""
    info = session_info(handler)
    if not info:
        return None, "", None
    profs = _client_profiles(info.get("id") or "")
    if not profs:
        return info, (info.get("gologin") or ""), None
    if gologin_pid:
        m = next((p for p in profs if p.get("gologin_profile_id") == gologin_pid), None)
        return (info, gologin_pid, m) if m else (info, "", None)
    return info, profs[0].get("gologin_profile_id") or "", profs[0]


def _status_cache_path(profile: str, pid: str) -> Path:
    return _resolve_profile_home_for_name(profile) / ("social_status_%s.json" % pid)


def _read_status(profile: str, pid: str) -> dict:
    try:
        with open(_status_cache_path(profile, pid), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def saas_profiles_list(handler):
    """All of the client's profiles, each with its cached per-platform login status."""
    info = session_info(handler)
    if not info:
        bad(handler, "not logged in", 401)
        return
    profs = _client_profiles(info.get("id") or "")
    out = []
    for p in profs:
        pid = p.get("gologin_profile_id") or ""
        cached = _read_status(info.get("profile") or "", pid)
        out.append({"id": p.get("id"), "gologin_profile_id": pid, "name": p.get("name") or "Profile",
                    "connected": cached.get("connected") or {}, "checked_at": cached.get("checked_at") or ""})
    j(handler, {"profiles": out, "max": _MAX_PROFILES, "platforms": list(_SOCIAL_PLATFORMS)})


def saas_profiles_add(handler, body):
    """Create a NEW GoLogin profile (own fingerprint + MY proxy) for this client, up to the cap."""
    info = session_info(handler)
    if not info:
        bad(handler, "not logged in", 401)
        return
    profs = _client_profiles(info.get("id") or "")
    if len(profs) >= _MAX_PROFILES:
        bad(handler, "you've reached the max of %d profiles" % _MAX_PROFILES, 409)
        return
    name = str((body or {}).get("name") or "").strip() or ("Profile %d" % (len(profs) + 1))
    try:
        pid = gologin_create_client_profile(info.get("email") or name)
    except Exception as e:  # noqa: BLE001
        bad(handler, "GoLogin profile create failed: %s" % e, 502)
        return
    st, res = _supa("POST", "/rest/v1/client_profiles",
                    {"client_id": info.get("id"), "gologin_profile_id": pid, "name": name},
                    prefer="return=representation")
    if st not in (200, 201):
        bad(handler, "profile save failed (%s)" % st, 502)
        return
    j(handler, {"ok": True, "profile": (res[0] if isinstance(res, list) and res else
                                        {"gologin_profile_id": pid, "name": name})})


def saas_profiles_delete(handler, body):
    info = session_info(handler)
    if not info:
        bad(handler, "not logged in", 401)
        return
    pid = str((body or {}).get("gologin_profile_id") or "").strip()
    profs = _client_profiles(info.get("id") or "")
    if not any(p.get("gologin_profile_id") == pid for p in profs):
        bad(handler, "not found", 404)
        return
    try:
        _gologin("DELETE", "/browser/" + pid)
    except Exception as e:  # noqa: BLE001
        logger.warning("gologin delete failed: %s", e)
    _supa("DELETE", "/rest/v1/client_profiles?client_id=eq.%s&gologin_profile_id=eq.%s"
          % (urllib.parse.quote(info.get("id") or ""), urllib.parse.quote(pid)))
    j(handler, {"ok": True})


# Where each "Connect <platform>" should land the browser (login page).
_PLATFORM_LOGIN = {
    "facebook": "https://www.facebook.com/login",
    "threads": "https://www.threads.net/login",
    "tiktok": "https://www.tiktok.com/login",
    "instagram": "https://www.instagram.com/accounts/login/",
}


def _run_helper_detached(pid: str, args: list, profile: str) -> None:
    """Fire the GoLogin helper without blocking the request (e.g. navigate the live browser)."""
    helper = os.environ.get("HERMES_GOLOGIN_HELPER") or "/apptoo/gologin_helper.js"
    env = dict(os.environ)
    env["GOLOGIN_API_TOKEN"] = _gologin_token()
    env["GOLOGIN_PROFILE_ID"] = pid
    if profile:
        env["HERMES_HOME"] = str(_resolve_profile_home_for_name(profile))
    try:
        subprocess.Popen([_node_bin(), helper] + args, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:  # noqa: BLE001
        logger.warning("helper detached run failed: %s", e)


def saas_social_connect(handler, body):
    """Start a specific profile's cloud browser -> land on the platform login -> return live-view URL."""
    info, pid, _row = _resolve_profile(handler, str((body or {}).get("profileId") or "").strip())
    if not info:
        bad(handler, "not logged in", 401)
        return
    if not pid:
        bad(handler, "unknown profile", 404)
        return
    plat = str((body or {}).get("platform") or "").lower().strip()
    st, res = _gologin("POST", "/browser/%s/web" % pid, {})
    if st not in (200, 201, 202):
        bad(handler, "cloud browser start failed (%s): %s" % (st, json.dumps(res)[:200]), 502)
        return
    url = res.get("remoteOrbitaUrl") or ""
    if not url:
        bad(handler, "no live-view url returned", 502)
        return
    login_url = _PLATFORM_LOGIN.get(plat)
    if login_url:
        _run_helper_detached(pid, ["open-url", login_url], info.get("profile") or "")
    j(handler, {"liveUrl": url, "status": res.get("status") or "", "platform": plat, "gologin_profile_id": pid})


def saas_social_stop(handler, body):
    info, pid, _row = _resolve_profile(handler, str((body or {}).get("profileId") or "").strip())
    if not info or not pid:
        bad(handler, "not logged in / no profile", 401)
        return
    st, _res = _gologin("DELETE", "/browser/%s/web" % pid)
    j(handler, {"ok": st in (200, 202, 204)})


def saas_social_check(handler, body):
    """Verify login for ONE platform of a profile (the one just connected). Merges into the cache."""
    info, pid, _row = _resolve_profile(handler, str((body or {}).get("profileId") or "").strip())
    if not info:
        bad(handler, "not logged in", 401)
        return
    if not pid:
        bad(handler, "unknown profile", 404)
        return
    plat = str((body or {}).get("platform") or "").lower().strip()
    helper = os.environ.get("HERMES_GOLOGIN_HELPER") or "/apptoo/gologin_helper.js"
    env = dict(os.environ)
    env["GOLOGIN_API_TOKEN"] = _gologin_token()
    env["GOLOGIN_PROFILE_ID"] = pid
    env["HERMES_HOME"] = str(_resolve_profile_home_for_name(info["profile"]))
    # Check ONLY the platform being connected (don't touch/navigate the others).
    args = [_node_bin(), helper, "login-status"] + ([plat] if plat in _SOCIAL_PLATFORMS else [])
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=180, env=env)
        out = json.loads((p.stdout or "").strip() or "{}")
    except subprocess.TimeoutExpired:
        bad(handler, "status check timed out", 504)
        return
    except Exception as e:  # noqa: BLE001
        bad(handler, "status check failed: %s" % e, 502)
        return
    if out.get("error"):
        bad(handler, "status check failed: %s" % out["error"], 502)
        return
    checked = out.get("connected") or {}
    # MERGE — keep the other platforms' existing statuses, only update the checked one(s).
    connected = _read_status(info["profile"], pid).get("connected") or {}
    connected.update(checked)
    rec = {"connected": connected, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    try:
        cp = _status_cache_path(info["profile"], pid)
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(rec), encoding="utf-8")
    except Exception:
        pass
    j(handler, {"gologin_profile_id": pid, "just_checked": plat, **rec})


def saas_social_disconnect_platform(handler, body):
    """Mark ONE platform of a profile as disconnected (clears its cached login status)."""
    info, pid, _row = _resolve_profile(handler, str((body or {}).get("profileId") or "").strip())
    if not info or not pid:
        bad(handler, "not logged in / unknown profile", 401)
        return
    plat = str((body or {}).get("platform") or "").lower().strip()
    cache = _read_status(info["profile"], pid)
    connected = cache.get("connected") or {}
    connected.pop(plat, None)
    rec = {"connected": connected, "checked_at": cache.get("checked_at") or ""}
    try:
        cp = _status_cache_path(info["profile"], pid)
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(rec), encoding="utf-8")
    except Exception:
        pass
    j(handler, {"ok": True, **rec})


# ── Reporting (Supabase posts + profile-local jsonl) ─────────────────────────

def log_post_row(client_id: str, rec: dict, name_by_pid: dict | None = None) -> None:
    try:
        gpid = rec.get("gologin_profile_id") or ""
        pname = (name_by_pid or {}).get(gpid, "") if name_by_pid else ""
        _supa("POST", "/rest/v1/posts", {
            "client_id": client_id, "platform": rec.get("platform") or "",
            "agent": rec.get("agent") or "", "caption": rec.get("caption") or "",
            "media": rec.get("media") or [], "link": rec.get("link") or "",
            "status": rec.get("status") or "published",
            "gologin_profile_id": gpid, "profile_name": pname,
        })
    except Exception as e:  # noqa: BLE001
        logger.warning("post log failed: %s", e)


def saas_reports_posts(handler, parsed):
    info = session_info(handler)
    if not info:
        bad(handler, "not logged in", 401)
        return
    q = urllib.parse.parse_qs(parsed.query or "")
    start = (q.get("start") or [""])[0].strip()
    end = (q.get("end") or [""])[0].strip()
    plat = (q.get("platform") or ["all"])[0].strip().lower()
    # map gologin_profile_id -> profile name (for "which identity posted")
    name_by_pid = {p.get("gologin_profile_id"): p.get("name")
                   for p in _client_profiles(info.get("id") or "")}
    posts = []
    # 1) Supabase rows (persist across redeploys)
    try:
        path = "/rest/v1/posts?select=*&client_id=eq.%s&order=created_at.desc&limit=200" % info.get("id")
        if start:
            path += "&created_at=gte." + urllib.parse.quote(start)
        if end:
            path += "&created_at=lte." + urllib.parse.quote(end + "T23:59:59")
        st, rows = _supa("GET", path)
        if st == 200 and isinstance(rows, list):
            for r in rows:
                posts.append({"platform": r.get("platform") or "", "agent": r.get("agent") or "",
                              "content": r.get("caption") or "", "media": r.get("media") or [],
                              "link": r.get("link") or "", "status": r.get("status") or "published",
                              "profile": r.get("profile_name") or name_by_pid.get(r.get("gologin_profile_id"), ""),
                              "date": r.get("created_at") or ""})
    except Exception as e:  # noqa: BLE001
        logger.warning("supabase posts read failed: %s", e)
    # 2) profile-local jsonl (written by gologin_helper) — sync new ones up, then show
    try:
        lp = _resolve_profile_home_for_name(info["profile"]) / "gologin_posts.jsonl"
        seen = {(p.get("link"), p.get("date")) for p in posts}
        if lp.exists():
            for line in lp.read_text(encoding="utf-8").splitlines():
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                key = (rec.get("link"), rec.get("date"))
                if key in seen:
                    continue
                posts.append({"platform": rec.get("platform") or "", "agent": rec.get("agent") or "",
                              "content": rec.get("caption") or "", "media": rec.get("media") or [],
                              "link": rec.get("link") or "", "status": rec.get("status") or "published",
                              "profile": name_by_pid.get(rec.get("gologin_profile_id"), ""),
                              "date": rec.get("date") or ""})
                log_post_row(info.get("id") or "", rec, name_by_pid)  # persist to Supabase
    except Exception as e:  # noqa: BLE001
        logger.warning("local posts read failed: %s", e)
    if plat and plat != "all":
        posts = [p for p in posts if p.get("platform") == plat]
    if start:
        posts = [p for p in posts if not p.get("date") or str(p["date"])[:10] >= start]
    if end:
        posts = [p for p in posts if not p.get("date") or str(p["date"])[:10] <= end]
    posts.sort(key=lambda p: str(p.get("date") or ""), reverse=True)
    j(handler, {"posts": posts[:200]})


# ── Login / Register page (served at /login — replaces the single-password page) ─

_LOGIN_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hermes — Sign in</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#FDFAF4;--card:#FFF;--line:#EAE1D1;--text:#221C14;--muted:#6E6454;--accent:#F26B21}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{display:grid;place-items:center;background:var(--bg);font:15px/1.5 'Inter',sans-serif;color:var(--text);padding:20px}
.card{width:100%;max-width:400px;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:30px 28px;box-shadow:0 10px 40px rgba(34,28,20,.08)}
.logo{width:52px;height:52px;border-radius:15px;background:linear-gradient(135deg,#F8863F,#F26B21);display:grid;place-items:center;color:#fff;font-weight:800;font-size:22px;margin:0 auto 14px}
h1{font-size:20px;text-align:center;margin:0 0 4px;letter-spacing:-.02em}
.sub{color:var(--muted);text-align:center;font-size:13.5px;margin:0 0 20px}
label{display:block;font-size:12px;font-weight:600;color:var(--muted);margin:12px 2px 5px}
input{width:100%;font:inherit;padding:11px 13px;border:1px solid var(--line);border-radius:12px;background:#FAF6EE;outline:none;color:var(--text)}
input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(242,107,33,.15)}
button{width:100%;font:inherit;font-weight:700;margin-top:18px;padding:12px;border:0;border-radius:12px;color:#fff;cursor:pointer;background:linear-gradient(180deg,#F8863F,#F26B21);box-shadow:0 4px 14px rgba(242,107,33,.35)}
button:disabled{opacity:.6;cursor:wait}
.toggle{margin-top:14px;text-align:center;font-size:13px;color:var(--muted)}
.toggle a{color:var(--accent);font-weight:600;cursor:pointer;text-decoration:none}
.err{display:none;margin-top:12px;background:#FDECEC;color:#C0392B;font-size:13px;padding:9px 12px;border-radius:10px}
.note{display:none;margin-top:12px;background:#FFF1E6;color:#C9500E;font-size:13px;padding:9px 12px;border-radius:10px}
</style></head><body>
<form class="card" id="f">
  <div class="logo">H</div>
  <h1 id="title">Welcome back</h1>
  <p class="sub" id="sub">Sign in to your Social Posting Manager</p>
  <label>Email</label><input type="email" id="email" autocomplete="email" required placeholder="you@company.com">
  <label>Password</label><input type="password" id="pw" autocomplete="current-password" required minlength="6" placeholder="••••••••">
  <button id="btn" type="submit">Sign in</button>
  <div class="toggle" id="tg">New here? <a onclick="mode('r')">Create an account</a></div>
  <div class="err" id="err"></div>
  <div class="note" id="note"></div>
</form>
<script>
let M='l';const $=s=>document.querySelector(s);
function mode(m){M=m;$('#title').textContent=m==='l'?'Welcome back':'Create your account';
 $('#sub').textContent=m==='l'?'Sign in to your Social Posting Manager':'We set up your workspace + Malaysia browser automatically';
 $('#btn').textContent=m==='l'?'Sign in':'Create account';
 $('#tg').innerHTML=m==='l'?'New here? <a onclick="mode(\\'r\\')">Create an account</a>':'Have an account? <a onclick="mode(\\'l\\')">Sign in</a>';
 $('#err').style.display='none';}
document.getElementById('f').addEventListener('submit',async(e)=>{e.preventDefault();
 const btn=$('#btn');btn.disabled=true;$('#err').style.display='none';
 if(M==='r'){$('#note').style.display='block';$('#note').textContent='Creating your account + provisioning your Malaysia cloud browser… (~10s)';}
 try{
  const r=await fetch(M==='l'?'/api/saas/login':'/api/saas/register',{method:'POST',
    headers:{'Content-Type':'application/json'},credentials:'same-origin',
    body:JSON.stringify({email:$('#email').value.trim(),password:$('#pw').value})});
  const d=await r.json();
  if(!r.ok||d.error) throw new Error(d.error||('HTTP '+r.status));
  const next=new URLSearchParams(location.search).get('next');
  location.href=(next&&next.startsWith('/')&&!next.startsWith('//'))?next:'/';
 }catch(err){$('#note').style.display='none';$('#err').style.display='block';$('#err').textContent=err.message;btn.disabled=false;}
});
</script></body></html>"""


def saas_login_page(handler) -> None:
    body = _LOGIN_HTML.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


# ── Storage (client image library; agents pull unused images to post) ────────

def _supa_storage_upload(path: str, data: bytes, content_type: str) -> str:
    """Upload bytes to the Supabase 'media' bucket, return the public URL."""
    url, service, _anon = _supa_env()
    req = urllib.request.Request(url + "/storage/v1/object/media/" + path, data=data, method="POST")
    req.add_header("apikey", service)
    req.add_header("Authorization", "Bearer " + service)
    req.add_header("Content-Type", content_type or "application/octet-stream")
    req.add_header("x-upsert", "true")
    with urllib.request.urlopen(req, timeout=60) as resp:
        resp.read()
    return url + "/storage/v1/object/public/media/" + path


def _supa_storage_delete(path: str) -> None:
    url, service, _anon = _supa_env()
    req = urllib.request.Request(url + "/storage/v1/object/media/" + path, method="DELETE")
    req.add_header("apikey", service)
    req.add_header("Authorization", "Bearer " + service)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
    except Exception:
        pass


def saas_storage_list(handler):
    info = session_info(handler)
    if not info:
        bad(handler, "not logged in", 401)
        return
    st, rows = _supa("GET", "/rest/v1/media?select=*&client_id=eq.%s&order=created_at.desc&limit=300"
                     % urllib.parse.quote(info.get("id") or ""))
    j(handler, {"media": rows if isinstance(rows, list) else [],
                "platforms": list(_SOCIAL_PLATFORMS)})


def saas_storage_upload(handler, body):
    import base64
    info = session_info(handler)
    if not info:
        bad(handler, "not logged in", 401)
        return
    b = body or {}
    filename = re.sub(r"[^A-Za-z0-9._-]+", "_", str(b.get("filename") or "image"))[:80] or "image"
    data_url = str(b.get("dataUrl") or "")
    m = re.match(r"^data:([^;]+);base64,(.*)$", data_url, re.S)
    if not m:
        bad(handler, "expected a base64 data URL", 400)
        return
    content_type = m.group(1)
    try:
        raw = base64.b64decode(m.group(2))
    except Exception:
        bad(handler, "bad base64", 400)
        return
    if len(raw) > 15 * 1024 * 1024:
        bad(handler, "image too large (max 15MB)", 400)
        return
    # unique-ish path without Date/random (unavailable): counter via existing count
    stc, cnt = _supa("GET", "/rest/v1/media?select=id&client_id=eq.%s" % urllib.parse.quote(info["id"]),
                     prefer="count=exact")
    seq = (len(cnt) if isinstance(cnt, list) else 0)
    path = "%s/%d_%s" % (info["id"], seq, filename)
    try:
        pub = _supa_storage_upload(path, raw, content_type)
    except Exception as e:  # noqa: BLE001
        bad(handler, "upload failed: %s" % e, 502)
        return
    st, res = _supa("POST", "/rest/v1/media",
                    {"client_id": info["id"], "url": pub, "storage_path": path, "filename": filename},
                    prefer="return=representation")
    if st not in (200, 201):
        bad(handler, "media row insert failed (%s)" % st, 502)
        return
    j(handler, {"ok": True, "media": (res[0] if isinstance(res, list) and res else {"url": pub})})


def saas_storage_delete(handler, body):
    info = session_info(handler)
    if not info:
        bad(handler, "not logged in", 401)
        return
    mid = str((body or {}).get("id") or "").strip()
    if not mid:
        bad(handler, "id required", 400)
        return
    st, rows = _supa("GET", "/rest/v1/media?select=storage_path,client_id&id=eq." + urllib.parse.quote(mid))
    row = rows[0] if isinstance(rows, list) and rows else None
    if not row or row.get("client_id") != info.get("id"):
        bad(handler, "not found", 404)
        return
    _supa_storage_delete(row.get("storage_path") or "")
    _supa("DELETE", "/rest/v1/media?id=eq." + urllib.parse.quote(mid))
    j(handler, {"ok": True})


# ── Dispatch (called from api.routes) ────────────────────────────────────────

def handle_saas_get(handler, parsed) -> bool:
    p = parsed.path
    if p == "/login":
        saas_login_page(handler)
    elif p == "/api/saas/me":
        saas_me(handler)
    elif p == "/api/saas/admin/settings":
        saas_admin_settings_get(handler)
    elif p == "/api/saas/admin/clients":
        saas_admin_clients(handler)
    elif p == "/api/saas/client/keys":
        saas_client_keys_get(handler)
    elif p == "/api/saas/profiles":
        saas_profiles_list(handler)
    elif p == "/api/storage/list":
        saas_storage_list(handler)
    else:
        return False
    return True


def handle_saas_post(handler, parsed, body) -> bool:
    p = parsed.path
    if p == "/api/saas/register":
        saas_register(handler, body)
    elif p == "/api/saas/login":
        saas_login(handler, body)
    elif p == "/api/saas/logout":
        saas_logout(handler)
    elif p == "/api/saas/admin/settings":
        saas_admin_settings_post(handler, body)
    elif p == "/api/saas/admin/user/create":
        saas_admin_user_create(handler, body)
    elif p == "/api/saas/admin/user/delete":
        saas_admin_user_delete(handler, body)
    elif p == "/api/saas/admin/user/password":
        saas_admin_user_password(handler, body)
    elif p == "/api/saas/client/keys":
        saas_client_keys_post(handler, body)
    elif p == "/api/saas/profiles/add":
        saas_profiles_add(handler, body)
    elif p == "/api/saas/profiles/delete":
        saas_profiles_delete(handler, body)
    elif p == "/api/storage/upload":
        saas_storage_upload(handler, body)
    elif p == "/api/storage/delete":
        saas_storage_delete(handler, body)
    elif p == "/api/social/check":
        saas_social_check(handler, body)
    elif p == "/api/social/disconnect-platform":
        saas_social_disconnect_platform(handler, body)
    elif p == "/api/social/stop":
        saas_social_stop(handler, body)
    else:
        return False
    return True

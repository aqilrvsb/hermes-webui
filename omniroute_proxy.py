# Same-origin reverse proxy: browser /omni/* -> OmniRoute on 127.0.0.1:20128/*.
# Lets the in-Hermes "OmniRoute" tab call OmniRoute's management API + /v1 same-origin.
# Reached only AFTER Hermes' own check_auth (see server.py hook), so it's login-gated.
# Stdlib only; never raises — if OmniRoute is down it returns a clean JSON 502 so Hermes
# itself is unaffected.
import urllib.request
import urllib.error

_OMNI = "http://127.0.0.1:20128"
_PREFIX = "/omni"
# headers worth forwarding both ways
_FWD_REQ = ("content-type", "accept", "authorization")


def proxy_omni(handler, parsed=None):
    try:
        path = handler.path[len(_PREFIX):] or "/"   # keeps querystring
        if not path.startswith("/"):
            path = "/" + path
        url = _OMNI + path
        method = handler.command
        try:
            length = int(handler.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            length = 0
        body = handler.rfile.read(length) if length > 0 else None

        req = urllib.request.Request(url, data=body, method=method)
        for hname in _FWD_REQ:
            v = handler.headers.get(hname)
            if v:
                req.add_header(hname, v)
        if body is not None and not handler.headers.get("Content-Type"):
            req.add_header("Content-Type", "application/json")

        try:
            resp = urllib.request.urlopen(req, timeout=180)
            data = resp.read()
            status = getattr(resp, "status", 200) or 200
            ctype = resp.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as e:
            data = e.read()
            status = e.code
            ctype = e.headers.get("Content-Type", "application/json")
        except Exception as e:  # connection refused / OmniRoute not up yet
            data = ('{"error":"OmniRoute not reachable on 127.0.0.1:20128 — it may still be '
                    'starting. (%s)"}' % str(e).replace('"', "'")).encode()
            status = 502
            ctype = "application/json"
    except Exception as e:  # never let the proxy crash the request handler
        data = ('{"error":"omni proxy error: %s"}' % str(e).replace('"', "'")).encode()
        status = 500
        ctype = "application/json"

    try:
        handler.send_response(status)
        handler.send_header("Content-Type", ctype)
        handler.send_header("Content-Length", str(len(data)))
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        handler.wfile.write(data)
    except Exception:
        pass
    return True

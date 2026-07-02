#!/bin/sh
# Internal single-profile tool: DEFAULT profile only.
# (The marketing marketer/developer profiles + the 12-agent cron pipeline were removed — start fresh.)
H="${HERMES_HOME:-$HOME/.hermes}"
mkdir -p "$H/profiles" 2>/dev/null || true

# ── ONE-TIME reset: remove the old marketing profiles and clear every previously-seeded cron.
#    Marker-guarded so it runs exactly once; afterwards the user's own profiles/crons are never touched.
if [ ! -f "$H/.reset_internal_v1" ]; then
  rm -rf "$H/profiles/marketer" "$H/profiles/developer" 2>/dev/null || true
  PYBIN=/app/venv/bin/python; [ -x "$PYBIN" ] || PYBIN="$(command -v python3 2>/dev/null || command -v python 2>/dev/null)"
  if [ -n "$PYBIN" ]; then
    "$PYBIN" - "$H" <<'PY' || true
import json, glob, os, sys
H = sys.argv[1]
for jf in glob.glob(os.path.join(H, "**", "cron", "jobs.json"), recursive=True):
    try:
        d = json.load(open(jf, encoding="utf-8"))
    except Exception:
        d = None
    empty = {"jobs": []} if isinstance(d, dict) else []
    try:
        json.dump(empty, open(jf, "w", encoding="utf-8"), indent=2)
        print("== reset: cleared crons in %s ==" % jf)
    except Exception:
        pass
PY
  fi
  touch "$H/.reset_internal_v1" 2>/dev/null || true
  echo "== reset_internal_v1: removed marketer/developer profiles + cleared all crons =="
fi

chown -R 1024:1024 "$H/profiles" 2>/dev/null || true
echo "== seed_roles: default profile only =="

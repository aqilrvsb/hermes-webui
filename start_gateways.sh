#!/bin/sh
# Launch a Hermes gateway daemon per profile (default + every named profile),
# each auto-restarting. New profiles created after boot get a gateway on next restart.
BASE="${HERMES_HOME:-$HOME/.hermes}"
HB=/app/venv/bin/hermes
launch() { # $1 = profile flag(s), $2 = log label
  ( while true; do $HB $1 gateway >>"/tmp/gw-$2.log" 2>&1; sleep 5; done ) &
}
launch "" default
if [ -d "$BASE/profiles" ]; then
  for d in "$BASE/profiles"/*/; do
    [ -d "$d" ] || continue
    name=$(basename "$d")
    launch "--profile $name" "$name"
  done
fi
echo "== gateways launched: default $( [ -d "$BASE/profiles" ] && ls "$BASE/profiles" 2>/dev/null | tr '\n' ' ' ) =="

# OmniRoute LLM gateway (OpenAI-compatible router, 177 providers, vision, auto-fallback).
# Internal only (127.0.0.1:20128); reached by the browser via Hermes' /omni/* proxy and by
# the agent via http://127.0.0.1:20128/v1. Config persists on the volume. Local-first (no
# JWT_SECRET) so the management API is open behind Hermes' own auth + loopback.
if [ -x /opt/node/bin/omniroute ] || command -v omniroute >/dev/null 2>&1; then
  ( export DATA_DIR="$BASE/omniroute" PORT=20128 DASHBOARD_PORT=20128 HOSTNAME=127.0.0.1 REQUIRE_API_KEY=false
    mkdir -p "$DATA_DIR"
    OMNI=$(command -v omniroute || echo /opt/node/bin/omniroute)
    while true; do "$OMNI" serve >>/tmp/omniroute.log 2>&1 || "$OMNI" >>/tmp/omniroute.log 2>&1; sleep 5; done ) &
  echo "== omniroute launching on 127.0.0.1:20128 (DATA_DIR=$BASE/omniroute) =="
fi

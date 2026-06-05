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

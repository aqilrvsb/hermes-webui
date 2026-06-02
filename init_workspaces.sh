#!/bin/sh
# Make /workspace persistent (volume-backed) and auto-create workspace folders,
# so Spaces can be added without "Path does not exist" and files survive redeploys.
VOL="${HERMES_HOME:-$HOME/.hermes}/workspace"
mkdir -p "$VOL" 2>/dev/null || true
# Repoint /workspace -> volume (preserve anything already there)
if [ ! -L /workspace ]; then
  [ -d /workspace ] && cp -an /workspace/. "$VOL"/ 2>/dev/null || true
  rm -rf /workspace 2>/dev/null || true
  ln -sfn "$VOL" /workspace 2>/dev/null || true
fi
# Auto-create starter folders + any names in HERMES_WORKSPACES (comma or space separated)
for w in FBAds content video scripts scratch $(printf '%s' "${HERMES_WORKSPACES:-}" | tr ',' ' '); do
  mkdir -p "$VOL/$w" 2>/dev/null || true
done
echo "== workspaces ready at /workspace -> $VOL : $(ls "$VOL" 2>/dev/null | tr '\n' ' ') =="

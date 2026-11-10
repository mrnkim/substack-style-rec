#!/usr/bin/env bash
# Re-run Pixeltable setup with a timestamped log under backend/logs/.
#
# Reset levels (least → most destructive) — matches Pixeltable skill / core-api guidance:
#
#   1) ./run_setup_logged.sh
#        Setup only (idempotent creates where supported).
#
#   2) ./run_setup_logged.sh --drop-dir
#        pxt.drop_dir(APP_NAMESPACE) — removes ONLY this app's directory (e.g. substack_rec).
#        Safe for "redo this project" without touching other Pixeltable work.
#
#   3) rm -rf "$PIXELTABLE_HOME/pgdata" OR rm -rf "$PIXELTABLE_HOME"
#        NOT scoped to one project: embedded Postgres + metadata for that entire home are gone.
#        If PIXELTABLE_HOME is ~/.pixeltable, you wipe EVERY Pixeltable project on the machine.
#        Skill reserves full ~/.pixeltable delete for schema corruption (IntegrityError), not routine dev.
#
# Prefer a per-repo home (see backend/.env.example: PIXELTABLE_HOME=./data) so a worst-case rm is
# limited to this checkout.
#
# Examples:
#   ./run_setup_logged.sh --drop-dir
#   ./run_setup_logged.sh --drop-dir --full
#   ./run_setup_logged.sh --full

set -euo pipefail
cd "$(dirname "$0")"

# `pxt` commands run in a daemon that never reads .env files. Export the same settings
# config.py loads (.env overrides .env.local); otherwise the daemon opens ~/.pixeltable
# while drop_dir and load.py use this project's PIXELTABLE_HOME.
set -a
[[ -f .env.local ]] && source .env.local
[[ -f .env ]] && source .env
set +a
if [[ -n "${PIXELTABLE_HOME:-}" && "$PIXELTABLE_HOME" != /* ]]; then
  export PIXELTABLE_HOME="$(pwd)/${PIXELTABLE_HOME#./}"
fi
# A project-specific port keeps this daemon (and its pidfile under PIXELTABLE_HOME)
# apart from daemons that other projects run on the default port, 22089.
export PXT_PORT="${PXT_PORT:-22189}"

mkdir -p logs
STAMP=$(date +%Y%m%d-%H%M%S)
LOG="logs/setup-${STAMP}.log"

log() { echo "$@" | tee -a "$LOG"; }

log "Log file: $(pwd)/$LOG"
log "Started (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"

DROP_DIR=0
LOAD_ARGS=()
for a in "$@"; do
  if [[ "$a" == "--drop-dir" ]]; then
    DROP_DIR=1
  else
    LOAD_ARGS+=("$a")
  fi
done

if [[ "$DROP_DIR" -eq 1 ]]; then
  log "--- pxt.drop_dir (namespace from config) ---"
  uv run python -c "
import config
import pixeltable as pxt
pxt.drop_dir(config.APP_NAMESPACE, force=True)
print('drop_dir OK:', config.APP_NAMESPACE)
" 2>&1 | tee -a "$LOG"
fi

log "--- pxt daemon restart (PIXELTABLE_HOME=${PIXELTABLE_HOME:-~/.pixeltable}, PXT_PORT=$PXT_PORT) ---"
# The daemon reads its environment and imports app.py/functions.py once; restart so it
# sees the variables above and the current code.
uv run pxt daemon restart 2>&1 | tee -a "$LOG"

log "--- pxt schema update (create/update schema) ---"
set +e
uv run pxt schema update app.py substack_rec 2>&1 | tee -a "$LOG"
schema_rc=${PIPESTATUS[0]}
set -e

if [[ "$schema_rc" -ne 0 ]]; then
  log "ERROR: pxt schema update exited with code $schema_rc"
  log "PostgreSQL log (if present): tail -80 \"\${PIXELTABLE_HOME:-\$HOME/.pixeltable}/pgdata/log\"/* 2>/dev/null || true"
  log "Full log: $(pwd)/$LOG"
  exit "$schema_rc"
fi

if [[ ${#LOAD_ARGS[@]} -eq 0 ]]; then
  log "--- load.py ---"
  set +e
  uv run load.py 2>&1 | tee -a "$LOG"
else
  log "--- load.py ${LOAD_ARGS[*]} ---"
  set +e
  uv run load.py "${LOAD_ARGS[@]}" 2>&1 | tee -a "$LOG"
fi
rc=${PIPESTATUS[0]}
set -e

log "Finished (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [[ "$rc" -ne 0 ]]; then
  log "ERROR: load.py exited with code $rc"
  log "PostgreSQL log (if present): tail -80 \"\${PIXELTABLE_HOME:-\$HOME/.pixeltable}/pgdata/log\"/* 2>/dev/null || true"
fi
log "Full log: $(pwd)/$LOG"
exit "$rc"

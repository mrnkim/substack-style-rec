#!/usr/bin/env bash
# Re-run Pixeltable setup with a timestamped log under backend/logs/.
#
# Reset levels (least → most destructive) — matches Pixeltable skill / core-api guidance:
#
#   1) ./run_setup_logged.sh
#        Setup only (idempotent creates where supported).
#
#   2) ./run_setup_logged.sh --drop-dir
#        pxt.drop_dir(APP_NAMESPACE) — removes ONLY this app’s directory (e.g. substack_rec).
#        Safe for “redo this project” without touching other Pixeltable work.
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
mkdir -p logs
STAMP=$(date +%Y%m%d-%H%M%S)
LOG="logs/setup-${STAMP}.log"

log() { echo "$@" | tee -a "$LOG"; }

log "Log file: $(pwd)/$LOG"
log "Started (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"

DROP_DIR=0
SETUP_ARGS=()
for a in "$@"; do
  if [[ "$a" == "--drop-dir" ]]; then
    DROP_DIR=1
  else
    SETUP_ARGS+=("$a")
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

if [[ ${#SETUP_ARGS[@]} -eq 0 ]]; then
  log "--- setup_pixeltable.py ---"
  set +e
  uv run setup_pixeltable.py 2>&1 | tee -a "$LOG"
else
  log "--- setup_pixeltable.py ${SETUP_ARGS[*]} ---"
  set +e
  uv run setup_pixeltable.py "${SETUP_ARGS[@]}" 2>&1 | tee -a "$LOG"
fi
rc=${PIPESTATUS[0]}
set -e

log "Finished (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [[ "$rc" -ne 0 ]]; then
  log "ERROR: setup_pixeltable.py exited with code $rc"
  log "PostgreSQL log (if present): tail -80 \"\${PIXELTABLE_HOME:-\$HOME/.pixeltable}/pgdata/log\"/* 2>/dev/null || true"
fi
log "Full log: $(pwd)/$LOG"
exit "$rc"

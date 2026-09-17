#!/bin/bash
# Odoo initialization orchestrator script
#
# Usage: init-odoo.sh [--seed-only]
#
# SEED_STEPS=admin,users limits which seed steps run (default: all)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/lib"

# shellcheck source=odoo/lib/common.sh
source "${LIB_DIR}/common.sh"
# shellcheck source=odoo/lib/setup-database.sh
source "${LIB_DIR}/setup-database.sh"

SEED_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --seed-only) SEED_ONLY=true ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

echo "======================================="
echo "Odoo Automated Setup"
echo "======================================="

# Step 1: Create the database or install modules added to ODOO_MODULES
if [ "$SEED_ONLY" = "false" ]; then
  setup_database
fi

# Step 2: Seed admin credentials, test users, API keys and sample records.
# Every step is idempotent, so this runs on every start.
log "Seeding steps: ${SEED_STEPS:-all}"
odoo shell -d "$PGDATABASE" --no-http --log-level=warn < "${NOODLE_SEED_DIR}/run.py"

log "Initialization done!"

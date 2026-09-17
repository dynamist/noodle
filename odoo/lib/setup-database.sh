#!/bin/bash
# Database creation and module installation for Odoo

LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=odoo/lib/common.sh
source "${LIB_DIR}/common.sh"

wait_for_db() {
  log "Waiting for database to be ready..."
  # Postgres can start later than Odoo in the cluster, e.g. while its image is pulled
  local timeout=300
  until pg_isready -q -d postgres; do
    timeout=$((timeout - 2))
    if [ "$timeout" -le 0 ]; then
      log "ERROR: database at ${PGHOST}:${PGPORT} is not reachable"
      return 1
    fi
    sleep 2
  done
  log "Database is ready!"
}

# Prints absent, partial or ready
db_state() {
  local exists
  exists=$(psql -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '${PGDATABASE}'")
  if [ "$exists" != "1" ]; then
    echo absent
    return
  fi

  local base_state
  base_state=$(psql -tAc "SELECT state FROM ir_module_module WHERE name = 'base'" 2>/dev/null || true)
  if [ "$base_state" = "installed" ]; then
    echo ready
  else
    echo partial
  fi
}

demo_args() {
  if [ "$ODOO_DEMO_DATA" = "true" ]; then
    echo --with-demo
  fi
}

create_database() {
  if [ "$(db_state)" = "partial" ]; then
    log "Found a partially initialized database (interrupted first run?), recreating it..."
    dropdb --if-exists "$PGDATABASE"
    rm -rf "/var/lib/odoo/filestore/${PGDATABASE}"
  fi

  log "Creating database '${PGDATABASE}' with modules: ${ODOO_MODULES}"
  log "Demo data: ${ODOO_DEMO_DATA}. This takes a few minutes on the first run..."
  # shellcheck disable=SC2046
  odoo -d "$PGDATABASE" -i "$ODOO_MODULES" $(demo_args) --stop-after-init --no-http
  log "Database created!"
}

install_missing_modules() {
  # New modules on disk are not in ir_module_module yet, so compare against
  # the installed ones instead of looking for uninstalled ones
  local installed module missing=()
  installed=$(psql -tAc "SELECT name FROM ir_module_module WHERE state = 'installed'")
  IFS=',' read -ra requested <<< "$ODOO_MODULES"
  for module in "${requested[@]}"; do
    if ! grep -qxF "$module" <<< "$installed"; then
      missing+=("$module")
    fi
  done

  if [ ${#missing[@]} -eq 0 ]; then
    log "All modules already installed, skipping..."
    return
  fi

  local modules
  modules=$(IFS=,; echo "${missing[*]}")
  log "Installing missing modules: ${modules}"
  odoo -d "$PGDATABASE" -i "$modules" --stop-after-init --no-http
}

setup_database() {
  wait_for_db
  case "$(db_state)" in
    absent | partial) create_database ;;
    ready) install_missing_modules ;;
  esac
}

# If script is run directly (not sourced), execute setup
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
  setup_database
fi

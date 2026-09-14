#!/bin/bash
# Common configuration and functions for Odoo initialization scripts

set -euo pipefail

# Configuration - can be overridden via environment variables
export PGHOST="${PGHOST:-db}"
export PGPORT="${PGPORT:-5432}"
export PGUSER="${PGUSER:-odoo}"
export PGPASSWORD="${PGPASSWORD:-supersecr3tpassw0rdfordatabase1}"
export PGDATABASE="${PGDATABASE:-odoo}"
export ODOO_ADMIN_PASSWD="${ODOO_ADMIN_PASSWD:-supersecr3tmasterpassw0rdfordevelop1}"
export ODOO_URL="${ODOO_URL:-http://localhost:8069}"
export ODOO_USER="${ODOO_USER:-admin}"
export ODOO_PASSWORD="${ODOO_PASSWORD:-supersecr3tpassw0rdfordevelop1}"
export ODOO_API_KEY="${ODOO_API_KEY:-odoo-supersecr3tapikeyfordevelop1}"
export ODOO_USERS_PASSWORD="${ODOO_USERS_PASSWORD:-supersecr3tpassw0rdfordevelop1}"
export ODOO_MODULES="${ODOO_MODULES:-contacts,crm,sale_management,account,stock,project,hr}"
export ODOO_DEMO_DATA="${ODOO_DEMO_DATA:-true}"

ODOO_DEV_HOME="${ODOO_DEV_HOME:-/opt/odoo-dev}"
export ODOO_DEV_SEED_DIR="${ODOO_DEV_SEED_DIR:-${ODOO_DEV_HOME}/seed}"

# Suffix of the per-user API keys, the key is "<first name>-<suffix>"
export ODOO_USERS_API_KEY_SUFFIX="${ODOO_USERS_API_KEY_SUFFIX:-supersecr3tapikeyfordevelop1}"

# Test users (login:Full Name:role), roles are mapped to groups in seed/seed_common.py
TEST_USERS=(
  "astrid.lindqvist:Astrid Lindqvist:sales_user"
  "johan.bergman:Johan Bergman:sales_manager"
  "karin.holmberg:Karin Holmberg:inventory_user"
  "nils.ekstrom:Nils Ekström:inventory_manager"
  "elin.sjoberg:Elin Sjöberg:billing"
  "per.lundgren:Per Lundgren:project_manager"
  "lena.hedlund:Lena Hedlund:hr_officer"
  "olof.nystrom:Olof Nyström:portal"
)
ODOO_DEV_TEST_USERS="$(printf '%s\n' "${TEST_USERS[@]}")"
export ODOO_DEV_TEST_USERS

log() {
  echo "[odoo-dev] $*"
}

# API key of a test user, portal users get none
user_api_key() {
  local login=$1
  echo "${login%%.*}-${ODOO_USERS_API_KEY_SUFFIX}"
}

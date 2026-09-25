#!/bin/bash
# Print the credentials summary, with --wait only once Odoo answers

LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=odoo/lib/common.sh
source "${LIB_DIR}/common.sh"

wait_for_http() {
  local timeout=600
  until curl -fs -o /dev/null http://127.0.0.1:8069/web/health; do
    timeout=$((timeout - 2))
    if [ "$timeout" -le 0 ]; then
      log "WARNING: Odoo did not answer on /web/health, printing credentials anyway"
      return
    fi
    sleep 2
  done
}

# Pad to a width in characters, printf pads multibyte names like Nyström by bytes
installed_apps() {
  psql -tAc "SELECT string_agg(name, ', ' ORDER BY name) FROM ir_module_module
    WHERE state = 'installed' AND application" 2>/dev/null || true
}

installed_count() {
  psql -tAc "SELECT count(*) FROM ir_module_module WHERE state = 'installed'" 2>/dev/null || true
}

pad() {
  local LC_ALL=C.UTF-8 text=$1 width=$2
  printf "%s%*s" "$text" $((width - ${#text})) ""
}

print_banner() {
  echo ""
  echo "================================"
  echo "Odoo Dev Setup Complete!"
  echo "================================"
  echo ""
  echo "📦 Odoo: $(python3 -c 'from odoo.release import version; print(version)')"
  echo "👨‍💻 Username: $ODOO_USER"
  echo "🔑 Password: $ODOO_PASSWORD"
  echo "🔐 API Key: $ODOO_API_KEY"
  echo "🗄️ Database: $PGDATABASE"
  echo "🛡️ Master password: $ODOO_ADMIN_PASSWD"
  echo "🧩 Apps: $(installed_apps) ($(installed_count) modules installed)"
  echo ""
  echo "🤖 Test users (password: $ODOO_USERS_PASSWORD):"
  local login name role
  for user_data in "${TEST_USERS[@]}"; do
    IFS=':' read -r login name role <<< "$user_data"
    local key="(no API key)"
    if [ "$role" != "portal" ]; then
      key=$(user_api_key "$login")
    fi
    echo "  - $(pad "$login" 18) $(pad "$name" 18) $(pad "$role" 18) $key"
  done
  if [ "$ODOO_DEMO_DATA" = "true" ]; then
    echo ""
    echo "🧪 Odoo demo users: demo/demo, portal/portal"
  fi
  echo ""
  echo "🌍 Your new Odoo is waiting for you at:"
  echo "   $ODOO_URL"
  echo ""
  echo "💡 TIP: Try the JSON-2 API with the API key:"
  echo "   curl -s ${ODOO_URL}/json/2/res.users/context_get \\"
  echo "     -H 'Authorization: bearer ${ODOO_API_KEY}' \\"
  echo "     -H 'X-Odoo-Database: ${PGDATABASE}' -H 'Content-Type: application/json' -d '{}'"
  echo "================================"
}

# If script is run directly (not sourced), print the banner
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
  if [ "${1:-}" = "--wait" ]; then
    wait_for_http
  fi
  print_banner
fi

#!/bin/bash
# Initialize Odoo, then hand over to the entrypoint of the official image

set -euo pipefail

# Only initialize when starting the server, not for `odoo shell`, bash etc.
if [ $# -eq 0 ] || { [ $# -eq 1 ] && [ "$1" = "odoo" ]; } || [[ "$1" == -* ]]; then
  /opt/noodle/init-odoo.sh
  # Printed in the background once the server answers
  /opt/noodle/lib/banner.sh --wait &
fi

exec /entrypoint.sh "$@"

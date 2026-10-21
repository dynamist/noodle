#!/bin/bash
# Print the PostgreSQL major version to run next to an Odoo image
#
#   (empty)   the default, the postgres tag in k8s/base/postgres.yaml
#   min       the oldest PostgreSQL the Odoo in the image supports
#   16, 17    that major version, if the Odoo in the image supports it

set -euo pipefail

image=${1:?usage: $0 IMAGE [PG]}
pg=${2:-}
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() {
  echo "$*" >&2
}

# Odoo only warns below its minimum, so check it before deploying
read -r series minimum < <(docker run --rm --entrypoint python3 "$image" \
  -c 'from odoo.release import MIN_PG_VERSION, serie; print(serie, MIN_PG_VERSION)')

case "$pg" in
  "")
    # The init container and the server both name the image, they must agree
    pg=$(sed -nE 's/^ *image: postgres:([0-9]+)$/\1/p' "${root}/k8s/base/postgres.yaml" | sort -u)
    [[ -n "$pg" ]] || { log "Error: no postgres:<major> image in k8s/base/postgres.yaml"; exit 1; }
    [[ "$pg" != *$'\n'* ]] || { log "Error: different postgres images in k8s/base/postgres.yaml: ${pg//$'\n'/, }"; exit 1; }
    ;;
  min)
    pg=$minimum
    ;;
  *[!0-9]*)
    log "Error: unknown PG '${pg}', use a major version (e.g. 17) or min"
    exit 1
    ;;
esac

if ((pg < minimum)); then
  log "Error: Odoo ${series} needs PostgreSQL ${minimum} or newer, not ${pg} (PG=min picks ${minimum})"
  exit 1
fi
echo "$pg"

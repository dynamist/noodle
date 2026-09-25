#!/bin/bash
# Print the docker build arguments for an Odoo VERSION (see the Dockerfile stages)
#
#   19, 20         released image from Docker Hub (a release-<major> stage)
#   20-nightly     newest dated nightly deb of the 20.0 series
#   master         the current commit of odoo/odoo master (any branch works)

set -euo pipefail

version=${1:?usage: $0 VERSION}
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() {
  echo "$*" >&2
}

nightly() {
  local series=$1 release
  release=$(curl -fsSL "https://nightly.odoo.com/${series}/nightly/deb/" |
    grep -oE "odoo_${series//./\\.}\.[0-9]{8}_all\.deb" | sort -u | tail -1 |
    sed -E 's/.*\.([0-9]{8})_all\.deb/\1/') || true
  if [ -z "$release" ]; then
    log "Error: no nightly deb of Odoo ${series} found on nightly.odoo.com"
    exit 1
  fi
  log "Odoo ${series} nightly ${release}"
  echo "--build-arg BASE=nightly --build-arg NOODLE_SERIES=${series} --build-arg NOODLE_RELEASE=${release}"
}

git_commit() {
  local branch=$1 commit
  commit=$(git ls-remote https://github.com/odoo/odoo "refs/heads/${branch}" | cut -f1)
  if [ -z "$commit" ]; then
    log "Error: no branch ${branch} in odoo/odoo"
    exit 1
  fi
  log "Odoo ${branch} at ${commit}"
  echo "--build-arg BASE=master --build-arg NOODLE_COMMIT=${commit}"
}

case "$version" in
  [0-9]*-nightly)
    nightly "${version%-nightly}.0"
    ;;
  [0-9] | [0-9][0-9])
    if grep -qE "^FROM .* AS release-${version}\$" "${root}/Dockerfile"; then
      log "Odoo ${version} released image"
      echo "--build-arg BASE=release-${version}"
    else
      log "No released image of Odoo ${version} in the Dockerfile, using the nightly deb"
      nightly "${version}.0"
    fi
    ;;
  master | saas-*)
    git_commit "$version"
    ;;
  *)
    log "Error: unknown VERSION ${version}, use e.g. 19, 20, 20-nightly or master"
    exit 1
    ;;
esac

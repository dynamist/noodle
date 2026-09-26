# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

noodle runs a disposable local Odoo 20 or 19 server, or a nightly or master build (image `dynamist/odoo`), with demo
data, test users and fixed credentials, for developing tools against Odoo. There is no application code, only the
container setup, the init and seed scripts, and custom modules in `addons/`.

## Common Commands

```bash
make up                              # create/reuse the k3d cluster, build, deploy, follow logs
make up VERSION=19                   # 20 (default), 19, 19-nightly, 20-nightly, master (remembered in .k8s/version)
make down                            # stop, keep data
make reset                           # delete the noodle namespace and its data
make destroy                         # delete the shared cluster (FORCE=1 if other apps run)
make logs / make ps
make seed STEPS=users,apikeys        # copy odoo/seed into the pod and re-run seed steps (DATASETS=crm)
make sample DATASETS=crm             # load sample datasets through the API with odooly
make shell / make odoo-shell / make psql / make db-forward
make console                         # odooly as admin (ODOOLY_ENV=<odooly.ini section>)
make validate                        # kubeconform on the rendered overlays
make test-k8s                        # tests/k8s against the deployed odoo

# Test against the local Odoo (safe to run data-altering operations)
curl -s http://odoo.localhost/json/2/res.partner/search_count \
  -H "Authorization: bearer odoo-supersecr3tapikeyfordevelop1" -H "X-Odoo-Database: odoo" \
  -H "Content-Type: application/json" -d '{"domain": []}'
```

## Credentials

This is a disposable test environment. These specific credentials indicate a safe-to-modify development instance.

- URL `http://odoo.localhost`, database `odoo`
- Admin `admin` / `supersecr3tpassw0rdfordevelop1`, API key `odoo-supersecr3tapikeyfordevelop1`
- Test users (`odoo/lib/common.sh`): password `supersecr3tpassw0rdfordevelop1`, API key
  `<first name>-supersecr3tapikeyfordevelop1`
- Master password `supersecr3tmasterpassw0rdfordevelop1`

## Pre-commit Checks

**Always run before committing:**

```bash
pre-commit run --all-files
```

This runs shellcheck, ruff (check and format) for `odoo/seed`, yamllint and taplo.

## Layout

- `k8s/cluster/k3d.yaml` - shared k3d cluster `dynamist-dev` (Traefik on 127.0.0.1:80/443), identical in every repo
  that uses it
- `k8s/base` - namespace `noodle`: `postgres` StatefulSet (postgres:17), `odoo` Deployment, Ingress `odoo.localhost`,
  NetworkPolicies, quota. Settings in `config.env`/`secret.env`. Overlays `local` and `ci`
- `tests/k8s` - smoke, seed data and isolation tests against the deployed instance
- `Dockerfile` - one stage per Odoo source (`release-19`, `nightly`, `master`), picked by the `BASE` build arg, then
  adds `odoo/` and `addons/`
- `scripts/build-args.sh` - maps `VERSION` to the build args, resolving the newest nightly deb or master commit
- `odoo/entrypoint.sh` - runs `init-odoo.sh` and the banner, then the official `/entrypoint.sh`
- `odoo/init-odoo.sh` - orchestrator: database setup, then seeding
- `odoo/lib/` - `common.sh` (defaults, `TEST_USERS`), `setup-database.sh`, `banner.sh`
- `odoo/seed/` - Python piped into `odoo shell`: `run.py` runs `seed_admin`, `seed_users`, `seed_apikeys` and the
  `sample` step. `make seed` copies it into the pod, so it needs no rebuild
- `odoo/seed/datasets/` - sample datasets (`@dataset` from `seed_datasets.py`), run by the `sample` step and by
  `make sample` (`run_odooly.py` piped into odooly)
- `addons/` - custom Dynamist modules, installed when listed in `ODOO_MODULES`
- `mise.toml` / `odooly.ini` - pinned odooly and its connection sections

## Conventions

- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`), default branch `main`
- Init and seed steps must be idempotent (check, then create or update) since they run on every start. Shell modules
  in `odoo/lib/` must also run on their own.
- Sample data goes in a dataset file in `odoo/seed/datasets/`, declaring its Odoo `modules` and the datasets it
  builds on (`after`). Records use `ensure_record()` with `__noodle__.<name>` xmlids and are only created when missing
- Datasets run under both the Odoo ORM and odooly: do not import `odoo`, use the `seed_datasets` helpers, plain ids
  in values and `id_of()` for many2one fields that may be empty
- Keep `k8s/base/*.env`, `odoo/lib/common.sh`, `mise.toml`, `odooly.ini` and the docs in sync when changing credentials
- Apps share the cluster: only namespaced resources (plus the own Namespace), no host ports, every kubectl call
  passes `--context k3d-dynamist-dev`. Change `k8s/cluster/k3d.yaml` in all repos that use it at once

## Odoo Gotchas

- Seed code runs on 19, 20 and master: detect features (`hasattr`) instead of checking versions, and share the
  helpers in `seed_common.py`
- A database only works with the series that created it, `setup-database.sh` refuses others, `make reset` to switch
- Odoo 20: `ir.config_parameter.set_param()` is gone, use typed `set_str()`/`set_bool()`/`set_int()` (see
  `seed_common.set_param()`)
- Odoo 20: bearer API keys must have the route's scope (`rpc`), keys without a scope no longer work there
- `res.users` groups are `group_ids` (not `groups_id`)
- Odoo reads config options from `ODOO_<OPTION>` env vars (e.g. `ODOO_WITH_DEMO`), do not name other variables like that
- `odoo shell` rolls back when the piped script ends, seed code must `env.cr.commit()` (done in `run.py`)
- Demo data is off by default, `--with-demo` loads it
- JSON-2 (`/json/2/<model>/<method>`, bearer API key) is the preferred API, XML-RPC and JSON-RPC are deprecated
- Manifest `license` must be an Odoo license value (e.g. `LGPL-3`), anything else fails module registration

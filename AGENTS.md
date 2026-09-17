# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

oodev runs a disposable local Odoo 19 server (image `dynamist/odoo`) with demo data, test users and fixed
credentials, for developing tools against Odoo. There is no application code, only the container setup, the init and
seed scripts, and custom modules in `addons/`.

## Common Commands

```bash
make up                              # start (postgres detached, odoo in foreground)
make down                            # stop, keep data
make reset                           # stop and delete all data
make logs                            # follow logs
make seed STEPS=users,apikeys        # re-run seed steps in the running container (DATASETS=crm)
make sample DATASETS=crm             # load sample datasets through the API with odooly
make shell / make odoo-shell / make psql
make console                         # odooly as admin (ODOOLY_ENV=<odooly.ini section>)

# Test against the local Odoo (safe to run data-altering operations)
curl -s http://odoo.localhost:8069/json/2/res.partner/search_count \
  -H "Authorization: bearer odoo-supersecr3tapikeyfordevelop1" -H "X-Odoo-Database: odoo" \
  -H "Content-Type: application/json" -d '{"domain": []}'
```

## Credentials

This is a disposable test environment. These specific credentials indicate a safe-to-modify development instance.

- URL `http://odoo.localhost:8069`, database `odoo`
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

- `compose.yml` - `odoo` (built from `Dockerfile`) and `db` (postgres:17) with named volumes
- `Dockerfile` - extends a pinned `odoo:19.0-<date>` image with `odoo/` and `addons/`
- `odoo/entrypoint.sh` - runs `init-odoo.sh` and the banner, then the official `/entrypoint.sh`
- `odoo/init-odoo.sh` - orchestrator: database setup, then seeding
- `odoo/lib/` - `common.sh` (defaults, `TEST_USERS`), `setup-database.sh`, `banner.sh`
- `odoo/seed/` - Python piped into `odoo shell`: `run.py` runs `seed_admin`, `seed_users`, `seed_apikeys` and the
  `sample` step. Mounted into the container, so `make seed` needs no rebuild
- `odoo/seed/datasets/` - sample datasets (`@dataset` from `seed_datasets.py`), run by the `sample` step and by
  `make sample` (`run_odooly.py` piped into odooly)
- `addons/` - custom Dynamist modules, installed when listed in `ODOO_MODULES`
- `mise.toml` / `odooly.ini` - pinned odooly and its connection sections

## Conventions

- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`), default branch `master`
- Init and seed steps must be idempotent (check, then create or update) since they run on every start. Shell modules
  in `odoo/lib/` must also run on their own.
- Sample data goes in a dataset file in `odoo/seed/datasets/`, declaring its Odoo `modules` and the datasets it
  builds on (`after`). Records use `ensure_record()` with `__oodev__.<name>` xmlids and are only created when missing
- Datasets run under both the Odoo ORM and odooly: do not import `odoo`, use the `seed_datasets` helpers, plain ids
  in values and `id_of()` for many2one fields that may be empty
- Keep `compose.yml`, `odoo/lib/common.sh`, `mise.toml`, `odooly.ini` and the docs in sync when changing credentials

## Odoo 19 Gotchas

- `res.users` groups are `group_ids` (not `groups_id`)
- Odoo reads config options from `ODOO_<OPTION>` env vars (e.g. `ODOO_WITH_DEMO`), do not name other variables like that
- `odoo shell` rolls back when the piped script ends, seed code must `env.cr.commit()` (done in `run.py`)
- Demo data is off by default, `--with-demo` loads it
- JSON-2 (`/json/2/<model>/<method>`, bearer API key) is the preferred API, XML-RPC and JSON-RPC are deprecated
- Manifest `license` must be an Odoo license value (e.g. `LGPL-3`), anything else fails module registration

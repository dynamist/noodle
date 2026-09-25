# Local Odoo Setup

This guide covers the local Odoo instance (19, 20, nightly or master, see
[Odoo Versions](#odoo-versions)) for **developing** and **testing**
tools against Odoo.

## Quick Start

**1. Start Odoo:**

```bash
mise trust && make tools   # k3d, kubectl and odooly, pinned in mise.toml
make up
```

`make up` creates the shared k3d cluster `dynamist-dev` (or reuses it), builds
the `dynamist/odoo` image, imports it into the cluster, deploys
`k8s/overlays/local` into the namespace `noodle` and follows the logs until
Odoo is ready. See [Kubernetes Setup](#kubernetes-setup).

The first start creates the database and installs the apps with demo data,
which takes a few minutes. Later starts only check the modules and the seeded
data.

**2. Open Odoo:** <http://odoo.localhost>, log in as `admin` with the password
`supersecr3tpassw0rdfordevelop1`.

**3. Stop Odoo:** `make down` stops Odoo and PostgreSQL and keeps the data,
`make reset` deletes the `noodle` namespace with all its data.

## What Gets Created

### Apps and Demo Data

Contacts, CRM, Sales, Invoicing, Inventory, Project and Employees
(`contacts,crm,sale_management,account,stock,project,hr`) with Odoo's own demo
data: companies, contacts, products, leads, quotations, invoices, projects,
employees and the `demo` / `demo` and `portal` / `portal` users.

### Admin Account

- **Username:** `admin`
- **Password:** `supersecr3tpassw0rdfordevelop1`
- **API key:** `odoo-supersecr3tapikeyfordevelop1` (never expires)

The master password for the database manager is
`supersecr3tmasterpassw0rdfordevelop1`.

### Test Users

Users with different access rights, for testing how tools behave for
non-admin users. They all have the password `supersecr3tpassw0rdfordevelop1`
and an API key `<first name>-supersecr3tapikeyfordevelop1`, except the portal
user which has no API key.

| Login | Name | Role | API key |
|-------|------|------|---------|
| `astrid.lindqvist` | Astrid Lindqvist | Sales: own documents | `astrid-supersecr3tapikeyfordevelop1` |
| `johan.bergman` | Johan Bergman | Sales: administrator | `johan-supersecr3tapikeyfordevelop1` |
| `karin.holmberg` | Karin Holmberg | Inventory: user | `karin-supersecr3tapikeyfordevelop1` |
| `nils.ekstrom` | Nils Ekström | Inventory: administrator | `nils-supersecr3tapikeyfordevelop1` |
| `elin.sjoberg` | Elin Sjöberg | Invoicing: billing | `elin-supersecr3tapikeyfordevelop1` |
| `per.lundgren` | Per Lundgren | Project: administrator | `per-supersecr3tapikeyfordevelop1` |
| `lena.hedlund` | Lena Hedlund | Employees: officer | `lena-supersecr3tapikeyfordevelop1` |
| `olof.nystrom` | Olof Nyström | Portal | none |

Internal test users also get an employee record.

### Sample Records

A few records on top of the demo data, owned by the test users:

- **Exempel AB**, a customer company with Olof Nyström as its contact
- **noodle Consulting Hour**, a service product
- Two opportunities for Exempel AB, one owned by Astrid (sales user) and one by
  Johan (sales administrator), so Astrid sees fewer leads than Johan
- A quotation for Exempel AB, visible to the portal user
- The project **noodle Sandbox** with the columns Backlog, Up next, In progress,
  In review and Done, and three tasks assigned to Per, two in Backlog and one in Up next
- The project **Datacenter migration** for the fictional customer Robot
  Mechanics Inc, with the same columns, a migration underway in them and the RMI
  team as users and assignees (Mikael Wallin as manager, Ove Pettersson, Viola
  Larsson, Daniel Lindgren, Tommy Svensson). They have no password and no API
  key, they are there to be assigned work

Sample records are only created when they are missing, so changes you make
survive restarts. Delete a record to get it back on the next start. The
records come from the datasets in `odoo/seed/datasets/`, see
[Adding Sample Data](#adding-sample-data).

## Configuration

The settings are in `k8s/base/config.env` and, for credentials,
`k8s/base/secret.env`. To override settings locally, put them in the
gitignored `k8s/overlays/local/config.local.env` and run `make up`:

```bash
echo ODOO_MODULES=contacts,sale_management,dynamist_foo >> k8s/overlays/local/config.local.env
make up
```

### Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ODOO_URL` | `http://odoo.localhost` | Base URL (`web.base.url`) |
| `PGDATABASE` | `odoo` | Database name |
| `ODOO_USER` | `admin` | Admin login |
| `ODOO_PASSWORD` | `supersecr3tpassw0rdfordevelop1` | Admin password (secret) |
| `ODOO_API_KEY` | `odoo-supersecr3tapikeyfordevelop1` | Admin API key (secret) |
| `ODOO_USERS_PASSWORD` | `supersecr3tpassw0rdfordevelop1` | Password of the test users (secret) |
| `ODOO_ADMIN_PASSWD` | `supersecr3tmasterpassw0rdfordevelop1` | Master password, database manager (secret) |
| `ODOO_MODULES` | `contacts,crm,sale_management,account,stock,project,hr` | Modules to install |
| `ODOO_DEMO_DATA` | `true` | Load demo data when the database is created |
| `PGUSER` / `POSTGRES_USER` | `odoo` | PostgreSQL user (secret) |
| `PGPASSWORD` / `POSTGRES_PASSWORD` | `supersecr3tpassw0rdfordatabase1` | PostgreSQL password (secret) |

`ODOO_DEMO_DATA` only has an effect when the database is created, run
`make reset` after changing it.

Odoo reads every config file option from an `ODOO_<OPTION>` environment
variable, for example `ODOO_WITH_DEMO` or `ODOO_LIST_DB`. Do not add variables
with such names to the Odoo pod unless you mean to set that option. For the
same reason the pods set `enableServiceLinks: false`, otherwise Kubernetes
would inject `ODOO_PORT` and similar variables for the `odoo` Service.

### Custom Modules

Modules in `addons/` are copied into the `dynamist/odoo` image at
`/mnt/dynamist-addons`, which is on the addons path. Add a module to
`ODOO_MODULES` to install it, modules that are not installed yet are installed
on every start. To update an installed module after changing it:

```bash
make shell
odoo -d odoo -u dynamist_foo --stop-after-init --no-http --db_host postgres
```

Until `addons/` contains a module, Odoo logs a warning that
`/mnt/dynamist-addons` is not a valid addons directory. It is harmless.

### Adding Sample Data

Sample data is split into datasets, one Python file per dataset in
`odoo/seed/datasets/`. Every file there is picked up automatically:

```python
# odoo/seed/datasets/crm.py
from seed_datasets import dataset, ensure_record, ref, user


@dataset(modules=["crm"], after=["partners"])
def crm(env):
    ensure_record(env, "lead_astrid", "crm.lead", {
        "name": "Exempel AB: tooling workshop",
        "type": "opportunity",
        "partner_id": ref(env, "partner_exempel").id,
        "user_id": user(env, "astrid.lindqvist").id,
    })
```

- `@dataset(modules=..., after=...)` registers the function as a dataset with
  its name. It is skipped when one of `modules` is not installed, and so is
  every dataset that builds on it.
- `after` lists the datasets it builds on. They run first, and selecting a
  dataset with `DATASETS=` selects them too.
- `ensure_record(env, name, model, vals)` creates a record with the xmlid
  `__noodle__.<name>` unless it exists, and returns it.
- `ref(env, name)` returns the record of `__noodle__.<name>`, or of a full
  xmlid such as `base.se`.
- `user(env, login)` returns a test user.
- `Command.create/link/clear/set` build x2many values, and `id_of(record.field)`
  reads the id of a many2one that may be empty.

The same datasets run in two ways:

```bash
make seed STEPS=sample DATASETS=crm   # Odoo ORM in the container, as on every start
make sample DATASETS=crm              # odooly over JSON-2 from the host (ODOOLY_ENV=dev)
```

`make seed` copies `odoo/seed` from your checkout into the running pod, so it
uses your edits without a rebuild. Restarts use the copy in the image, run
`make up` to build your edits into it. Seeding in the container runs in one transaction, while
`make sample` commits every call on its own: after a failure, fix it and run
it again.

Datasets must work with both the Odoo ORM and odooly, so do not import `odoo`.
Use the helpers above, `env[model].search/search_read/create`,
`record.write({...})` and ids in values. An empty many2one is `False` in
odooly but an empty recordset in the ORM, which is what `id_of()` handles.

## Using the API Key

Odoo 19 and 20 have three external APIs. The same API key works for all of them.
XML-RPC and JSON-RPC are deprecated and are planned to be removed in Odoo 22.

**JSON-2** (`/json/2/<model>/<method>`), arguments are the method's keyword
arguments:

```bash
curl -s http://odoo.localhost/json/2/res.partner/search_read \
  -H "Authorization: bearer odoo-supersecr3tapikeyfordevelop1" \
  -H "X-Odoo-Database: odoo" \
  -H "Content-Type: application/json" \
  -d '{"domain": [["is_company", "=", true]], "fields": ["name"], "limit": 3}'
```

The API documentation of the instance is at <http://odoo.localhost/doc>
(log in first).

**XML-RPC**, with the API key in place of the password:

```python
from xmlrpc.client import ServerProxy

url, db, key = "http://odoo.localhost", "odoo", "odoo-supersecr3tapikeyfordevelop1"
uid = ServerProxy(f"{url}/xmlrpc/2/common").authenticate(db, "admin", key, {})
models = ServerProxy(f"{url}/xmlrpc/2/object")
print(models.execute_kw(db, uid, key, "res.partner", "search_count", [[]]))
```

**JSON-RPC:**

```bash
curl -s http://odoo.localhost/jsonrpc -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0", "method": "call",
  "params": {"service": "object", "method": "execute_kw",
             "args": ["odoo", 2, "odoo-supersecr3tapikeyfordevelop1", "res.partner", "search_count", [[]]]}}'
```

**odooly**, pinned in `mise.toml` and configured in `odooly.ini`:

```bash
mise trust && make tools
make console                        # admin over JSON-2 with the API key
ODOOLY_ENV=sales make console       # Astrid Lindqvist, sales user
```

```python
>>> env.user.login
'admin'
>>> env['res.partner'].search_count([])
```

| `odooly.ini` section | Logs in as |
|----------------------|------------|
| `dev` | admin, API key over JSON-2 |
| `dev-password` | admin, password |
| `dev-jsonrpc` | admin, API key over JSON-RPC |
| `sales` | astrid.lindqvist, API key |
| `inventory` | karin.holmberg, API key |
| `portal` | olof.nystrom, password |

`mise.toml` also exports `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`
and `ODOO_API_KEY` for tools under development.

## How It Works

The `dynamist/odoo` image extends the official Odoo image of the selected
version (see [Odoo Versions](#odoo-versions)). Its entrypoint (`odoo/entrypoint.sh`) runs `odoo/init-odoo.sh` before starting the
server:

1. **Database:** waits for PostgreSQL, then
   - creates the database with `odoo -i $ODOO_MODULES --with-demo` if it does
     not exist,
   - drops and recreates it if an earlier first start was interrupted,
   - installs modules from `ODOO_MODULES` that are not installed yet.
2. **Seeding:** pipes `odoo/seed/run.py` into `odoo shell`, which runs the
   seed steps `admin`, `users`, `apikeys` and `sample` (the datasets in
   `odoo/seed/datasets/`).
3. **Banner:** prints the credentials once `/web/health` answers.

All steps are idempotent and run on every start. Credentials are only
rewritten when they differ from the configured values, so browser sessions
stay logged in across restarts.

Odoo only generates random API keys, so `odoo/seed/seed_apikeys.py` inserts
the fixed keys into `res_users_apikeys` itself, hashed the same way as Odoo
does it. The failed login cooldown (`base.login_cooldown_after`) is turned off
so tools under development are not locked out.

## Odoo Versions

`make up VERSION=...` builds one of the stages in the `Dockerfile`, chosen by
`scripts/build-args.sh`:

| `VERSION` | Stage | Source |
|-----------|-------|--------|
| `19` (default) | `release-19` | official `odoo:19.0-<date>` image, bumped by Renovate |
| `20` | `release-20` | official `odoo:20.0-<date>` image, falls back to `20-nightly` until the Dockerfile has that stage |
| `19-nightly`, `20-nightly` | `nightly` | newest dated deb from `nightly.odoo.com/<series>/nightly/deb/`, installed over the newest released image |
| `master` | `master` | GitHub tarball of the current `odoo/odoo` master commit, laid out like the deb |

The nightly date and the master commit are resolved at build time and passed
as build arguments, so a rebuild only downloads Odoo again when upstream
moved. `master` is unreleased code and breaks now and then, its Python
dependencies come from its `debian/control` and can be ahead of the base
image.

The last `VERSION` is kept in `.k8s/version` and reused by a plain `make up`.
A database belongs to the Odoo series that created it (`base` module version
`19.0.x`, `20.0.x`, ...). On a mismatch `setup-database.sh` stops with an
error instead of starting Odoo, run `make reset` to switch.

Differences between the versions are handled in the seed code by feature
detection rather than version checks, e.g. `set_param()` in
`seed_common.py`.

CI tests `19` and `20` on every change, and additionally `19-nightly`,
`20-nightly` and `master` weekly and on manual runs (`master` may fail
without failing the workflow).

## Kubernetes Setup

noodle runs in a local [k3d](https://k3d.io) cluster, which is k3s in Docker.
The cluster can be shared with other Dynamist dev apps, and each app keeps to
its own namespace:

- **Cluster:** `k8s/cluster/k3d.yaml`, identical in every repo that uses it.
  It pins the k3s version and publishes the bundled Traefik ingress on
  `127.0.0.1:80` and `:443`. Whichever app starts first creates the cluster,
  the others reuse it.
- **Routing:** each app has a standard `Ingress` with its own hostnames, here
  `odoo.localhost` to the `odoo` Service. Names under `.localhost` resolve to
  loopback, no `/etc/hosts` entry is needed.
- **noodle:** `k8s/base` holds the `noodle` namespace, PostgreSQL (StatefulSet
  `postgres`), Odoo (Deployment `odoo`, `Recreate` so two pods never initialize the
  same database), the Ingress, a ResourceQuota with default limits and
  NetworkPolicies. Only Traefik reaches Odoo and only Odoo reaches PostgreSQL.
  Overlays: `local` (with `config.local.env`) and `ci`.
- **Images:** `make odoo-image` builds `dynamist/odoo`, tags it by content and
  imports it with `k3d image import`, no registry is involved.

Every `make` target passes `--context k3d-dynamist-dev`, so it never acts on
another cluster.

## Useful Commands

```bash
make up                         # create/reuse cluster, build, deploy, follow logs
make down                       # stop odoo and postgres, keep data
make reset                      # delete the noodle namespace and its data
make destroy                    # delete the whole cluster (FORCE=1 if other apps run)
make logs / make ps             # follow odoo logs / show pods, ingress, volumes
make creds                      # print credentials
make seed                       # copy odoo/seed into the pod and re-run all seed steps
make seed STEPS=users,apikeys   # re-run some seed steps
make sample DATASETS=crm        # load sample datasets through the API with odooly
make shell                      # bash in the odoo pod
make odoo-shell                 # Odoo Python shell with env
make psql                       # psql on the odoo database
make db-forward                 # PostgreSQL on 127.0.0.1:5432 until Ctrl+C (POSTGRES_PORT=5433)
make console                    # odooly console
make validate                   # validate the rendered manifests with kubeconform
make test-k8s                   # run tests/k8s against the deployed odoo
```

## Testing

`tests/k8s` runs against the deployed instance and needs no Python project,
`make test-k8s` runs it with `uv run --with`:

- **Smoke:** health, login page, admin API key, WebSocket upgrade through
  Traefik, unknown hosts get a 404.
- **Seed data:** test users with their groups, API keys (none for the portal
  user), sample records, access rules (Astrid sees fewer leads than Johan) and
  that seeding again creates nothing (marked `slow`).
- **Isolation:** pods in other namespaces cannot reach Odoo or PostgreSQL,
  containers have requests and memory limits, the namespace has a quota and
  the manifests create nothing cluster-wide except the namespace.

```bash
make test-k8s PYTEST_ARGS="-m 'not slow'"
```

CI (`.github/workflows/k8s.yml`) validates the manifests, then creates a k3d
cluster on the runner and runs `make ci-deploy` (the `ci` overlay) and
`make ci-test` (`make test-k8s` and `make sample`). A coexistence job deploys the
apps listed in the repository variable `COEXISTENCE_REPOS` (space separated
`owner/name`) into the same cluster and runs every app's tests, which also
checks that the apps cannot reach each other and that all repos pin the same
`k8s/cluster/k3d.yaml`. Each of those repos must provide the make targets
`ci-deploy` and `ci-test`.

## Troubleshooting

**`401 Invalid apikey`:** check the key and the `X-Odoo-Database` header, and
check that the seeding in `make logs` finished. Re-run it with
`make seed STEPS=apikeys`.

**The pod restarts during start:** the init script stops on any error, the
reason is in `make logs` (add `--previous` with `kubectl logs` for the last
attempt). An interrupted first start is detected and the database is
recreated on the next start.

**After bumping the Odoo image** in `Dockerfile`: run `make reset`, or update
all modules with `odoo -d odoo -u all --stop-after-init --no-http --db_host postgres`
from `make shell`.

**Cluster version warning:** `make up` warns when the running cluster uses a
different k3s version than `k8s/cluster/k3d.yaml`. Recreate it with
`make destroy` (this deletes the data of every app in it).

## Data Persistence

The database and the filestore are PersistentVolumeClaims in the `noodle`
namespace, stored by k3s's `local-path` provisioner inside the cluster's
Docker container. `make down` and restarting Docker keep them, `make reset`
deletes them and `make destroy` deletes them along with the cluster.

## Security Note

This setup is for local development only. The credentials are public, list
the database manager and turn off the login cooldown. The ports are bound to
loopback, do not expose them or use this configuration in production.
PostgreSQL is not published at all, use `make db-forward`.

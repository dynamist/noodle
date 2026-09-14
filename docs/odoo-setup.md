# Local Odoo Setup

This guide covers the local Odoo 19 instance for **developing** and **testing**
tools against Odoo.

## Quick Start

**1. Start Odoo:**

```bash
make up
```

The Makefile detects whether you have podman or docker installed (preferring
podman). It starts PostgreSQL in the background and Odoo in the foreground, so
you can see the logs and the credentials summary printed when Odoo is ready.

The first start creates the database and installs the apps with demo data,
which takes a few minutes. Later starts only check the modules and the seeded
data, and are up in about 10 seconds.

**2. Open Odoo:** <http://localhost:8069>, log in as `admin` with the password
`supersecr3tpassw0rdfordevelop1`.

**3. Stop Odoo:** When you are done, press `Ctrl+C`, then run `make down` to
remove the containers. The data is kept, `make reset` deletes it.

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
- **odoo-dev Consulting Hour**, a service product
- Two opportunities for Exempel AB, one owned by Astrid (sales user) and one by
  Johan (sales administrator), so Astrid sees fewer leads than Johan
- A quotation for Exempel AB, visible to the portal user
- The project **odoo-dev Sandbox** with three tasks assigned to Per

Sample records are only created when they are missing, so changes you make
survive restarts. Delete a record to get it back on the next start.

## Configuration

All settings can be customized via environment variables. Defaults are in
`compose.yml` and can be overridden from the command line:

```bash
ODOO_PORT=8070 make up
ODOO_MODULES=contacts,sale_management,dynamist_foo make up
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ODOO_PORT` | `8069` | Port on 127.0.0.1 for Odoo |
| `ODOO_URL` | `http://localhost:8069` | Base URL (`web.base.url`) |
| `ODOO_DB` | `odoo` | Database name |
| `ODOO_USER` | `admin` | Admin login |
| `ODOO_PASSWORD` | `supersecr3tpassw0rdfordevelop1` | Admin password |
| `ODOO_API_KEY` | `odoo-supersecr3tapikeyfordevelop1` | Admin API key |
| `ODOO_USERS_PASSWORD` | `supersecr3tpassw0rdfordevelop1` | Password of the test users |
| `ODOO_MASTER_PASSWORD` | `supersecr3tmasterpassw0rdfordevelop1` | Master password (database manager) |
| `ODOO_MODULES` | `contacts,crm,sale_management,account,stock,project,hr` | Modules to install |
| `ODOO_DEMO_DATA` | `true` | Load demo data when the database is created |
| `POSTGRES_PORT` | `5432` | Port on 127.0.0.1 for PostgreSQL |
| `POSTGRES_USER` | `odoo` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `supersecr3tpassw0rdfordatabase1` | PostgreSQL password |

`ODOO_DEMO_DATA` only has an effect when the database is created, run
`make reset` after changing it.

Odoo 19 reads every config file option from an `ODOO_<OPTION>` environment
variable, for example `ODOO_WITH_DEMO` or `ODOO_LIST_DB`. Do not add variables
with such names to the Odoo container unless you mean to set that option.

### Custom Modules

Modules in `addons/` are copied into the `dynamist/odoo` image at
`/mnt/dynamist-addons`, which is on the addons path. Add a module to
`ODOO_MODULES` to install it, modules that are not installed yet are installed
on every start. To update an installed module after changing it:

```bash
make shell
odoo -d odoo -u dynamist_foo --stop-after-init --no-http
```

Until `addons/` contains a module, Odoo logs a warning that
`/mnt/dynamist-addons` is not a valid addons directory. It is harmless.

## Using the API Key

Odoo 19 has three external APIs. The same API key works for all of them.
XML-RPC and JSON-RPC are deprecated and are planned to be removed in Odoo 22.

**JSON-2** (`/json/2/<model>/<method>`), arguments are the method's keyword
arguments:

```bash
curl -s http://localhost:8069/json/2/res.partner/search_read \
  -H "Authorization: bearer odoo-supersecr3tapikeyfordevelop1" \
  -H "X-Odoo-Database: odoo" \
  -H "Content-Type: application/json" \
  -d '{"domain": [["is_company", "=", true]], "fields": ["name"], "limit": 3}'
```

The API documentation of the instance is at <http://localhost:8069/doc>
(log in first).

**XML-RPC**, with the API key in place of the password:

```python
from xmlrpc.client import ServerProxy

url, db, key = "http://localhost:8069", "odoo", "odoo-supersecr3tapikeyfordevelop1"
uid = ServerProxy(f"{url}/xmlrpc/2/common").authenticate(db, "admin", key, {})
models = ServerProxy(f"{url}/xmlrpc/2/object")
print(models.execute_kw(db, uid, key, "res.partner", "search_count", [[]]))
```

**JSON-RPC:**

```bash
curl -s http://localhost:8069/jsonrpc -H "Content-Type: application/json" -d '{
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

The `dynamist/odoo` image extends the official `odoo:19.0` image. Its
entrypoint (`odoo/entrypoint.sh`) runs `odoo/init-odoo.sh` before starting the
server:

1. **Database:** waits for PostgreSQL, then
   - creates the database with `odoo -i $ODOO_MODULES --with-demo` if it does
     not exist,
   - drops and recreates it if an earlier first start was interrupted,
   - installs modules from `ODOO_MODULES` that are not installed yet.
2. **Seeding:** pipes `odoo/seed/run.py` into `odoo shell`, which runs the
   seed steps `admin`, `users`, `apikeys` and `sample`.
3. **Banner:** prints the credentials once `/web/health` answers.

All steps are idempotent and run on every start. Credentials are only
rewritten when they differ from the configured values, so browser sessions
stay logged in across restarts.

Odoo only generates random API keys, so `odoo/seed/seed_apikeys.py` inserts
the fixed keys into `res_users_apikeys` itself, hashed the same way as Odoo
does it. The failed login cooldown (`base.login_cooldown_after`) is turned off
so tools under development are not locked out.

## Useful Commands

```bash
make up                         # start odoo (postgres detached, odoo in foreground)
make down                       # stop and remove containers, keep data
make reset                      # stop and delete all data
make logs                       # follow logs
make creds                      # print credentials
make seed                       # re-run all seed steps
make seed STEPS=users,apikeys   # re-run some seed steps
make shell                      # bash in the odoo container
make odoo-shell                 # Odoo Python shell with env
make psql                       # psql on the odoo database
make console                    # odooly console
```

## Troubleshooting

**Port already in use:** another service uses 8069 or 5432. Start with
`ODOO_PORT=8070 POSTGRES_PORT=5433 make up`, and set `ODOO_URL` to match.

**`401 Invalid apikey`:** check the key and the `X-Odoo-Database` header, and
check that the seeding in `make logs` finished. Re-run it with
`make seed STEPS=apikeys`.

**The container exits during start:** the init script stops on any error, the
reason is at the end of `make logs`. An interrupted first start is detected
and the database is recreated on the next `make up`.

**After bumping the Odoo image** in `Dockerfile`: run `make reset`, or update
all modules with `odoo -d odoo -u all --stop-after-init --no-http` from
`make shell`.

## Data Persistence

The database and the filestore are in the volumes `odoo-dev_db-data` and
`odoo-dev_odoo-data`. `make down` keeps them, `make reset` deletes them and the
next `make up` starts from scratch.

## Security Note

This setup is for local development only. The credentials are public, list
the database manager and turn off the login cooldown. The ports are bound to
127.0.0.1, do not expose them or use this configuration in production.

# oodev

A disposable local Odoo 19 server with sample data and well-known credentials,
for developing tools against Odoo (JSON-2, XML-RPC and JSON-RPC clients,
odooly scripts, custom Dynamist modules).

## Requirements

- docker or podman (with compose)
- [mise](https://mise.jdx.dev) for the pinned CLI tools (odooly)

## Quick Start

```bash
make up         # start postgres in the background and odoo in the foreground
```

The first start installs the apps with demo data, which takes a few minutes.
Later starts take seconds. Odoo is at <http://localhost:8069>.

Press `Ctrl+C` and run `make down` when you are done. Data is kept in volumes
until `make reset`.

```bash
make tools      # install odooly with mise (run `mise trust` first)
make console    # odooly console logged in as admin with the API key
```

## Credentials

**Local development only**, the ports are bound to 127.0.0.1.

| What | Value |
|------|-------|
| URL / database | `http://localhost:8069` / `odoo` |
| Admin username / password | `admin` / `supersecr3tpassw0rdfordevelop1` |
| Admin API key | `odoo-supersecr3tapikeyfordevelop1` |
| Master password | `supersecr3tmasterpassw0rdfordevelop1` |
| Postgres user / password | `odoo` / `supersecr3tpassw0rdfordatabase1` |
| Test users | password `supersecr3tpassw0rdfordevelop1`, API key `<first name>-supersecr3tapikeyfordevelop1` |
| Odoo demo users | `demo` / `demo`, `portal` / `portal` |

See [docs/odoo-setup.md](docs/odoo-setup.md) for the test users, API
examples and configuration.

```bash
curl -s http://localhost:8069/json/2/res.partner/search_read \
  -H "Authorization: bearer odoo-supersecr3tapikeyfordevelop1" \
  -H "X-Odoo-Database: odoo" -H "Content-Type: application/json" \
  -d '{"domain": [["is_company", "=", true]], "fields": ["name"], "limit": 3}'
```

## Make Targets

| Target | Description |
|--------|-------------|
| `make up` | Start postgres in the background and odoo in the foreground |
| `make down` | Stop and remove the containers, keeping the data |
| `make reset` | Stop and **delete all data volumes** |
| `make logs` / `make ps` | Follow logs / show container status |
| `make creds` | Print the credentials of the running odoo |
| `make seed` | Re-run seeding (`STEPS=users,apikeys` to limit) |
| `make shell` / `make odoo-shell` / `make psql` | bash, Odoo Python shell or psql in the container |
| `make console` | odooly console (`ODOOLY_ENV=sales` for another `odooly.ini` section) |
| `make tools` | Install the tools pinned in `mise.toml` |

## Custom Modules

Put Dynamist modules in [`addons/`](addons/) and add them to `ODOO_MODULES`.
They are built into the `dynamist/odoo` image and installed on the next
`make up`.

## License

Apache License 2.0, see [LICENSE](LICENSE). Copyright (c) 2026 Dynamist AB.

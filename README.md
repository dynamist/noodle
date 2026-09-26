# noodle

A disposable local Odoo 20 or 19 server (or a nightly or master build) with sample data and well-known credentials,
for developing tools against Odoo (JSON-2, XML-RPC and JSON-RPC clients,
odooly scripts, custom Dynamist modules).

The name is a play on *nodool*, but spelled noodle: if Google can misspell
googol, so can we.

## Requirements

- docker, which runs the local [k3d](https://k3d.io) cluster
- [mise](https://mise.jdx.dev) for the pinned CLI tools (k3d, kubectl, odooly)

## Quick Start

```bash
mise trust && make tools   # install k3d, kubectl and odooly
make up                    # create the cluster, build and deploy odoo, follow logs
```

The first start installs the apps with demo data, which takes a few minutes.
Odoo is at <http://odoo.localhost>, behind the cluster's Traefik ingress.

`make down` stops Odoo and keeps the data, `make reset` deletes it.

## Odoo Versions

`VERSION` picks the Odoo to build, one at a time in the same namespace:

| `VERSION` | Odoo |
|-----------|------|
| `20` (default) | the official `odoo:20.0` image, the newest nightly deb until that image is published |
| `19` | the official `odoo:19.0` image, pinned to a dated build |
| `19-nightly`, `20-nightly` | the newest nightly deb of that series from nightly.odoo.com |
| `master` | the current commit of the `odoo/odoo` master branch |

```bash
make reset && make up VERSION=19
```

The last `VERSION` built is kept in `.k8s/version`, a plain `make up` reuses
it. A database only works with the Odoo series that created it: Odoo refuses to
start on another one and asks for `make reset`.

```bash
make console    # odooly console logged in as admin with the API key
make test-k8s   # run the smoke, seed data and isolation tests
```

The k3d cluster `dynamist` can be shared with other Dynamist dev apps.
Each app lives in its own namespace, see
[Kubernetes Setup](docs/odoo-setup.md#kubernetes-setup).

## Credentials

**Local development only**, the ingress is bound to loopback.

| What | Value |
|------|-------|
| URL / database | `http://odoo.localhost` / `odoo` |
| Admin username / password | `admin` / `supersecr3tpassw0rdfordevelop1` |
| Admin API key | `odoo-supersecr3tapikeyfordevelop1` |
| Master password | `supersecr3tmasterpassw0rdfordevelop1` |
| Postgres user / password | `odoo` / `supersecr3tpassw0rdfordatabase1` |
| Test users | password `supersecr3tpassw0rdfordevelop1`, API key `<first name>-supersecr3tapikeyfordevelop1` |
| Odoo demo users | `demo` / `demo`, `portal` / `portal` |

See [docs/odoo-setup.md](docs/odoo-setup.md) for the test users, API
examples and configuration.

```bash
curl -s http://odoo.localhost/json/2/res.partner/search_read \
  -H "Authorization: bearer odoo-supersecr3tapikeyfordevelop1" \
  -H "X-Odoo-Database: odoo" -H "Content-Type: application/json" \
  -d '{"domain": [["is_company", "=", true]], "fields": ["name"], "limit": 3}'
```

## Make Targets

| Target | Description |
|--------|-------------|
| `make up` | Create or reuse the cluster, build and deploy odoo (`VERSION=19` for another version), follow the logs until it is ready |
| `make down` | Stop odoo and postgres, keeping the data |
| `make reset` | **Delete the `noodle` namespace** with all its data |
| `make destroy` | **Delete the whole cluster**, with every app in it (`FORCE=1` if other apps run) |
| `make logs` / `make ps` | Follow odoo logs / show pods, ingress and volumes |
| `make creds` | Print the credentials of the running odoo |
| `make seed` | Copy `odoo/seed` into the pod and re-run seeding (`STEPS=users,apikeys`, `DATASETS=crm` to limit) |
| `make sample` | Load the sample datasets through the API with odooly (`DATASETS=crm` to limit) |
| `make shell` / `make odoo-shell` / `make psql` | bash, Odoo Python shell or psql in the odoo pod |
| `make db-forward` | Forward PostgreSQL to `127.0.0.1:5432` |
| `make console` | odooly console (`ODOOLY_ENV=sales` for another `odooly.ini` section) |
| `make validate` / `make test-k8s` | Validate the manifests / run `tests/k8s` against the deployed odoo |
| `make tools` | Install the tools pinned in `mise.toml` |

## Custom Modules

Put Dynamist modules in [`addons/`](addons/) and add them to `ODOO_MODULES`.
They are built into the `dynamist/odoo` image and installed on the next
`make up`.

## License

Apache License 2.0, see [LICENSE](LICENSE). Copyright (c) 2026 Dynamist AB.

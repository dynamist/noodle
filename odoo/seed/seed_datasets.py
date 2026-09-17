"""Modular sample datasets, one file per dataset in datasets/.

Datasets run with an Odoo ORM env (`odoo shell`, seed step `sample`) or an
odooly env (`make sample`, over JSON-2), so they must not import `odoo` and
only use calls that behave the same in both: the helpers below,
env[model].search/create/search_read, record.write and plain ids in values.
An empty many2one is an empty recordset in the ORM but False in odooly, read
ids of relations with id_of().

    from seed_datasets import Command, dataset, ensure_record, ref, user

    @dataset(modules=["crm"], after=["partners"])
    def crm(env):
        ensure_record(env, "lead_astrid", "crm.lead", {
            "name": "Exempel AB: tooling workshop",
            "partner_id": ref(env, "partner_exempel").id,
            "user_id": user(env, "astrid.lindqvist").id,
        })
"""

import importlib.util
import os
from collections import namedtuple
from pathlib import Path

from seed_common import cfg, find_user, log

XMLID_MODULE = "__noodle__"

Dataset = namedtuple("Dataset", "name func modules after")

DATASETS = {}


def dataset(modules=(), after=()):
    """Register a dataset named after the function.

    modules: Odoo modules that must be installed, the dataset is skipped otherwise
    after: datasets this one builds on, they run first and are selected along with it
    """

    def register(func):
        if func.__name__ in DATASETS:
            raise SystemExit(f"Dataset {func.__name__!r} is defined twice")
        DATASETS[func.__name__] = Dataset(func.__name__, func, tuple(modules), tuple(after))
        return func

    return register


class Command:
    """Odoo x2many commands as plain tuples, accepted by the ORM and odooly."""

    @staticmethod
    def create(values):
        return (0, 0, values)

    @staticmethod
    def link(record_id):
        return (4, record_id, 0)

    @staticmethod
    def clear():
        return (5, 0, 0)

    @staticmethod
    def set(ids):
        return (6, 0, list(ids))


def id_of(value):
    """Id of a many2one value, False when empty (odooly returns False, the ORM an empty recordset)."""
    return value.id if value else False


def _xmlid(name):
    return name.split(".", 1) if "." in name else (XMLID_MODULE, name)


def _lookup(env, name):
    module, xml_name = _xmlid(name)
    return env["ir.model.data"].search_read([("module", "=", module), ("name", "=", xml_name)], ["model", "res_id"])


def _browse_existing(env, model, record_id):
    if env[model].with_context(active_test=False).search([("id", "=", record_id)]):
        return env[model].browse(record_id)
    return None


def ref(env, name):
    """Return the record of an xmlid, __noodle__.<name> unless name has a module."""
    for data in _lookup(env, name):
        record = _browse_existing(env, data["model"], data["res_id"])
        if record:
            return record
    raise SystemExit(f"Record {name!r} not found, is the dataset that creates it listed in `after`?")


def user(env, login):
    users = find_user(env, login)
    if not users:
        raise SystemExit(f"User {login!r} not found, run the users seed step first")
    return env["res.users"].browse(users.ids[0])


def ensure_record(env, name, model, vals, context=None):
    """Create a record tracked by the xmlid __noodle__.<name> unless it exists.

    Existing records are left alone, so changes made while developing survive
    restarts. Delete a record to have it recreated on the next run. context is
    added to the environment of the create call.
    """
    stale = []
    for data in _lookup(env, name):
        record = data["model"] == model and _browse_existing(env, model, data["res_id"])
        if record:
            return record
        stale.append(data["id"])

    if stale:
        env["ir.model.data"].browse(stale).unlink()
    target = env[model].with_context(**context) if context else env[model]
    record = env[model].browse(target.create(vals).ids[0])
    env["ir.model.data"].create(
        {
            "module": XMLID_MODULE,
            "name": name,
            "model": model,
            "res_id": record.id,
            "noupdate": True,
        }
    )
    log(f"Created {model} {record.display_name!r}")
    return record


def load():
    """Import datasets/*.py once, registering their datasets."""
    if DATASETS:
        return
    for path in sorted((Path(cfg("NOODLE_SEED_DIR")) / "datasets").glob("[!_]*.py")):
        spec = importlib.util.spec_from_file_location(f"noodle_dataset_{path.stem}", path)
        spec.loader.exec_module(importlib.util.module_from_spec(spec))


def resolve(names):
    """Return the named datasets and the ones they build on, dependencies first."""
    for ds in DATASETS.values():
        unknown = [dep for dep in ds.after if dep not in DATASETS]
        if unknown:
            raise SystemExit(f"Dataset {ds.name!r} builds on unknown datasets: {', '.join(unknown)}")
    unknown = [name for name in names if name not in DATASETS]
    if unknown:
        raise SystemExit(f"Unknown datasets: {', '.join(unknown)} (available: {', '.join(DATASETS)})")

    order = []

    def visit(name, chain):
        if name in chain:
            raise SystemExit(f"Dataset cycle: {' -> '.join([*chain, name])}")
        if name in order:
            return
        for dep in DATASETS[name].after:
            visit(dep, [*chain, name])
        order.append(name)

    for name in names:
        visit(name, [])
    return [DATASETS[name] for name in order]


def run(env, names=None):
    """Run datasets, all or those in SEED_DATASETS unless names are given."""
    load()
    if names is None:
        names = [name for name in os.environ.get("SEED_DATASETS", "").split(",") if name] or list(DATASETS)

    installed = {mod["name"] for mod in env["ir.module.module"].search_read([("state", "=", "installed")], ["name"])}
    skipped = set()
    for ds in resolve(names):
        missing = [mod for mod in ds.modules if mod not in installed]
        blocked = [dep for dep in ds.after if dep in skipped]
        if missing or blocked:
            skipped.add(ds.name)
            reason = f"modules not installed: {', '.join(missing)}" if missing else f"needs {', '.join(blocked)}"
            log(f"Skipping dataset {ds.name} ({reason})")
            continue
        log(f"Dataset {ds.name}")
        ds.func(env)

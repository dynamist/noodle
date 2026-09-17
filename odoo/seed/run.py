"""Seed the development database.

Piped into `odoo shell`, which provides a superuser `env` and rolls back
when the script ends, so this commits explicitly.

SEED_STEPS=admin,users limits which steps run (default: all).
SEED_DATASETS=crm,sale limits the datasets of the sample step (default: all).
"""

import os
import sys

sys.path.insert(0, os.environ.get("NOODLE_SEED_DIR", "/opt/noodle/seed"))

import seed_admin  # noqa: E402
import seed_apikeys  # noqa: E402
import seed_datasets  # noqa: E402
import seed_users  # noqa: E402

env = globals()["env"]  # injected by `odoo shell`

STEPS = {
    "admin": seed_admin.run,
    "users": seed_users.run,
    "apikeys": seed_apikeys.run,
    "sample": seed_datasets.run,
}

selected = [step for step in os.environ.get("SEED_STEPS", "").split(",") if step] or list(STEPS)
unknown = set(selected) - set(STEPS)
if unknown:
    raise SystemExit(f"Unknown seed steps: {', '.join(sorted(unknown))} (available: {', '.join(STEPS)})")

for name in selected:
    print(f"[noodle] Seeding {name}...", flush=True)
    STEPS[name](env)

env.cr.commit()
print("[noodle] Seeding done!", flush=True)

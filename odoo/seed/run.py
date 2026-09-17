"""Seed the development database.

Piped into `odoo shell`, which provides a superuser `env` and rolls back
when the script ends, so this commits explicitly.

SEED_STEPS=admin,users limits which steps run (default: all).
"""

import os
import sys

sys.path.insert(0, os.environ.get("OODEV_SEED_DIR", "/opt/oodev/seed"))

import seed_admin  # noqa: E402
import seed_apikeys  # noqa: E402
import seed_sample  # noqa: E402
import seed_users  # noqa: E402

env = globals()["env"]  # injected by `odoo shell`

STEPS = {
    "admin": seed_admin.run,
    "users": seed_users.run,
    "apikeys": seed_apikeys.run,
    "sample": seed_sample.run,
}

selected = [step for step in os.environ.get("SEED_STEPS", "").split(",") if step] or list(STEPS)
unknown = set(selected) - set(STEPS)
if unknown:
    raise SystemExit(f"Unknown seed steps: {', '.join(sorted(unknown))} (available: {', '.join(STEPS)})")

for name in selected:
    print(f"[oodev] Seeding {name}...", flush=True)
    STEPS[name](env)

env.cr.commit()
print("[oodev] Seeding done!", flush=True)

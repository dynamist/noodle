"""Load the sample datasets through the API.

Piped into odooly, which provides `env` logged in from odooly.ini (see `make
sample`). Every call commits on its own, re-run after a failure to complete
the data.

SEED_DATASETS=crm,sale limits the datasets (default: all).
"""

import os
import sys

sys.path.insert(0, os.environ["NOODLE_SEED_DIR"])

import seed_datasets  # noqa: E402

env = globals()["env"]  # injected by odooly

print("[noodle] Loading sample datasets...", flush=True)
seed_datasets.run(env)
print("[noodle] Sample datasets done!", flush=True)

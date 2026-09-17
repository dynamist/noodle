"""Tests against noodle deployed in the shared k3d cluster (`make up`, `make test-k8s`).

Run with kubectl on PATH (`mise exec --`), see the `test` target in the Makefile.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "odoo" / "seed"))

import seed_common  # noqa: E402

ODOO_URL = os.environ.get("ODOO_URL", "http://odoo.localhost")
DATABASE = "odoo"
ADMIN_KEY = "odoo-supersecr3tapikeyfordevelop1"
KUBE_CONTEXT = "k3d-dynamist-dev"
NAMESPACE = "noodle"


def kubectl(*args, check=True, namespace=NAMESPACE, **kwargs):
    cmd = ["kubectl", "--context", KUBE_CONTEXT, "-n", namespace, *args]
    return subprocess.run(cmd, check=check, capture_output=True, text=True, **kwargs)


def kubectl_json(*args, **kwargs):
    return json.loads(kubectl(*args, "-o", "json", **kwargs).stdout)


def json2(model, method, key=ADMIN_KEY, **params):
    """Call the JSON-2 API, returning the response for status checks."""
    return requests.post(
        f"{ODOO_URL}/json/2/{model}/{method}",
        headers={"Authorization": f"bearer {key}", "X-Odoo-Database": DATABASE},
        json=params,
        timeout=60,
    )


def json2_ok(model, method, key=ADMIN_KEY, **params):
    response = json2(model, method, key=key, **params)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture(scope="session")
def test_users():
    """(login, name, role) from odoo/lib/common.sh, the same list the seeding uses."""
    script = f"source {ROOT / 'odoo/lib/common.sh'} && printf '%s' \"$NOODLE_TEST_USERS\""
    users = subprocess.run(["bash", "-c", script], check=True, capture_output=True, text=True).stdout
    os.environ["NOODLE_TEST_USERS"] = users
    os.environ.setdefault("ODOO_USERS_API_KEY_SUFFIX", "supersecr3tapikeyfordevelop1")
    return seed_common.test_users()


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: takes minutes, deselect with -m 'not slow'")

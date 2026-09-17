"""Shared configuration and helpers for the seed steps."""

import os

# Groups given to each test user role, on top of base.group_user for internal roles
ROLES = {
    "internal": [],
    "sales_user": ["sales_team.group_sale_salesman"],
    "sales_manager": ["sales_team.group_sale_manager"],
    "inventory_user": ["stock.group_stock_user"],
    "inventory_manager": ["stock.group_stock_manager"],
    "billing": ["account.group_account_invoice"],
    "project_manager": ["project.group_project_manager"],
    "hr_officer": ["hr.group_hr_user"],
    "portal": ["base.group_portal"],
}


def cfg(name):
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Environment variable {name} is not set")
    return value


def log(message):
    print(f"[noodle]   {message}", flush=True)


def test_users():
    """Return (login, name, role) tuples from NOODLE_TEST_USERS (set by lib/common.sh)."""
    users = []
    for line in os.environ.get("NOODLE_TEST_USERS", "").splitlines():
        if line.strip():
            login, name, role = line.split(":")
            users.append((login, name, role))
    return users


def user_api_key(login):
    return f"{login.split('.')[0]}-{cfg('ODOO_USERS_API_KEY_SUFFIX')}"


def find_user(env, login):
    return env["res.users"].with_context(active_test=False).search([("login", "=", login)], limit=1)


def password_matches(user, password):
    """Check a password without changing it, so existing sessions stay valid."""
    user.env.cr.execute("SELECT COALESCE(password, '') FROM res_users WHERE id = %s", [user.id])
    [hashed] = user.env.cr.fetchone()
    return bool(hashed) and user._crypt_context().verify(password, hashed)


def ensure_password(user, password):
    if password_matches(user, password):
        return False
    user.password = password
    return True


def refs(env, xmlids):
    """Resolve xmlids to records, skipping those whose module is not installed."""
    records = []
    for xmlid in xmlids:
        record = env.ref(xmlid, raise_if_not_found=False)
        if record:
            records.append(record)
        else:
            log(f"WARNING: {xmlid} not found, is its module installed?")
    return records

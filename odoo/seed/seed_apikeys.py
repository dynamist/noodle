"""Fixed, well-known API keys.

Odoo only generates random keys, so the key row is inserted directly, hashed
the same way as res.users.apikeys._generate() does it.
"""

from odoo.addons.base.models.res_users import INDEX_SIZE, KEY_CRYPT_CONTEXT, _check_apikey_credentials
from seed_common import cfg, find_user, log, test_users, user_api_key

KEY_NAME = "odoo-dev fixed development key"


def ensure_key(env, user, key):
    if len(key) < INDEX_SIZE:
        raise SystemExit(f"API key for {user.login} must be at least {INDEX_SIZE} characters")

    owner = _check_apikey_credentials(env.cr, scope="rpc", key=key)
    if owner == user.id:
        return
    if owner:
        raise SystemExit(f"API key for {user.login} already belongs to user id {owner}")

    env.cr.execute("DELETE FROM res_users_apikeys WHERE user_id = %s AND name = %s", [user.id, KEY_NAME])
    env.cr.execute(
        """
        INSERT INTO res_users_apikeys (name, user_id, scope, expiration_date, key, index)
        VALUES (%s, %s, NULL, NULL, %s, %s)
        """,
        [KEY_NAME, user.id, KEY_CRYPT_CONTEXT.hash(key), key[:INDEX_SIZE]],
    )
    log(f"API key set for {user.login}")


def run(env):
    ensure_key(env, env.ref("base.user_admin"), cfg("ODOO_API_KEY"))

    for login, _name, role in test_users():
        if role == "portal":
            continue
        user = find_user(env, login)
        if not user:
            log(f"WARNING: user {login} not found, run the users step first")
            continue
        ensure_key(env, user, user_api_key(login))

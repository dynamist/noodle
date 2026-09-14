"""Named test users with different access rights."""

from odoo.fields import Command
from seed_common import ROLES, cfg, ensure_password, find_user, log, refs, test_users


def run(env):
    Users = env["res.users"].with_context(no_reset_password=True)
    password = cfg("ODOO_USERS_PASSWORD")
    has_hr = "create_employee" in Users._fields

    for login, name, role in test_users():
        if role not in ROLES:
            raise SystemExit(f"Unknown role {role!r} for {login}, known roles: {', '.join(ROLES)}")

        if role == "portal":
            groups = refs(env, ROLES[role])
        else:
            groups = refs(env, ["base.group_user", *ROLES[role]])

        vals = {
            "name": name,
            "login": login,
            "email": f"{login}@example.com",
            "tz": "Europe/Stockholm",
            "active": True,
            "group_ids": [Command.set([group.id for group in groups])],
        }

        user = find_user(env, login)
        if user:
            user.with_context(no_reset_password=True).write(vals)
        else:
            if has_hr and role != "portal":
                vals["create_employee"] = True
            user = Users.create(vals)
            log(f"Created user {login} ({role})")

        ensure_password(user, password)

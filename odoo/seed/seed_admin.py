"""Admin login and password plus instance settings for tool development."""

from seed_common import cfg, ensure_password, log


def run(env):
    admin = env.ref("base.user_admin")

    login = cfg("ODOO_USER")
    if admin.login != login:
        admin.login = login
        log(f"Admin login set to {login!r}")

    if ensure_password(admin, cfg("ODOO_PASSWORD")):
        log("Admin password set")

    params = env["ir.config_parameter"]
    params.set_param("web.base.url", cfg("ODOO_URL"))
    params.set_param("web.base.url.freeze", "True")
    # Tools under development fail logins a lot, do not lock accounts out
    params.set_param("base.login_cooldown_after", "0")

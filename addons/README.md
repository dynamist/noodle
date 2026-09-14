# Dynamist modules

Put custom Odoo modules here, one directory per module. They are copied into
the image at `/mnt/dynamist-addons`, which is on the Odoo addons path.

To install a module, add it to `ODOO_MODULES` (in `compose.yml` or the
environment) and restart with `make up`. Modules that are not installed yet
are installed on every start.

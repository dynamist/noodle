# Dynamist modules

Put custom Odoo modules here, one directory per module. They are copied into
the image at `/mnt/dynamist-addons`, which is on the Odoo addons path.

To install a module, add it to `ODOO_MODULES` (in `k8s/base/config.env` and
`odoo/lib/common.sh` for everyone, or in `k8s/overlays/local/config.local.env`
for yourself) and run `make up`. Modules that are not installed yet are
installed on every start.

## Changing a module

```bash
make upgrade    # copy addons/ into the pod, upgrade the modules that changed
```

Odoo only loads the views, data and assets of an installed module again when
the module is upgraded. `make upgrade` copies `addons/` into the running pod and
upgrades the installed modules whose files changed, without a restart, so
changes to XML, SCSS and JS show up after a reload of the page.

Python code is only loaded when Odoo starts, run `make up` after changing it.
`make up` builds `addons/` into the image, and every start upgrades the
modules that changed since the last upgrade.

## noodle_website

The public website at <http://odoo.localhost/>, installed by default:

- `views/homepage.xml` - the homepage content, inherits `website.homepage`
- `views/pages.xml` - further pages, a QWeb template plus a `website.page`
  record with its URL
- `views/contact.xml` - the phone number in the header and footer, which the
  website templates hard-code
- `data/menus.xml` - menu entries under `website.main_menu`, copied to every
  website
- `static/src/scss/website.scss` - styles, in the `web.assets_frontend` bundle

Changes made in the website editor are stored only in the database and are
lost on `make reset`. Use the editor to try things out, then copy the markup
into the module (the editor's HTML/SCSS code view shows it) and `make upgrade`.
A page edited in the editor is a copy that no longer follows the module, see
"Reset" in its page properties, or `make reset`.

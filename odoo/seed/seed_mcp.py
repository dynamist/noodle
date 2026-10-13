"""MCP server of Odoo 20 Enterprise (ai_mcp): a fixed admin key and OAuth client registration.

Does nothing unless ai_mcp is installed, which needs an image built with
ENTERPRISE (see docs/odoo-setup.md). Written without access to the ai_mcp
source, so the names below are assumptions, verify them against ai_mcp:

- the API key scope is a value of res.users.apikeys.description's scope
  selection that contains MCP_SCOPE_HINT (Community only has "rpc")
- "Allow Dynamic Client Registration" is a boolean settings field whose name
  contains one of DCR_FIELD_HINTS, stored in a system parameter
"""

from seed_apikeys import ensure_key
from seed_common import cfg, log, set_param

MODULE = "ai_mcp"
MCP_SCOPE_HINT = "mcp"
DCR_FIELD_HINTS = ("dynamic_client_registration", "dcr")
KEY_NAME = "noodle fixed development MCP key"


def mcp_scope(env):
    scopes = env["res.users.apikeys.description"]._fields["scope"].get_values(env)
    matches = [scope for scope in scopes if MCP_SCOPE_HINT in scope.lower()]
    if len(matches) != 1:
        log(f"WARNING: no single MCP API key scope in {scopes}, update seed_mcp.py")
        return None
    return matches[0]


def dcr_param(env):
    """The system parameter behind the dynamic client registration setting."""
    fields = env["res.config.settings"]._fields.values()
    matches = [
        field
        for field in fields
        if field.type == "boolean"
        and any(hint in field.name for hint in DCR_FIELD_HINTS)
        and getattr(field, "config_parameter", None)
    ]
    if len(matches) != 1:
        log(f"WARNING: no single dynamic client registration setting ({[f.name for f in matches]}), update seed_mcp.py")
        return None
    return matches[0].config_parameter


def is_enabled(env, key):
    params = env["ir.config_parameter"].sudo()
    if hasattr(params, "get_bool"):
        return params.get_bool(key)
    return params.get_param(key) in ("True", "true", "1")


def run(env):
    if not env["ir.module.module"].search_count([("name", "=", MODULE), ("state", "=", "installed")]):
        log(f"{MODULE} not installed (Odoo Enterprise only), skipping")
        return

    scope = mcp_scope(env)
    if scope:
        ensure_key(env, env.ref("base.user_admin"), cfg("ODOO_MCP_KEY"), scope=scope, name=KEY_NAME)

    # MCP clients such as Claude Code register themselves, nothing to pre-register
    param = dcr_param(env)
    if param and not is_enabled(env, param):
        set_param(env, param, True)
        log(f"Dynamic client registration enabled ({param})")

"""MCP server of Odoo 20 Enterprise (ai_mcp), skipped on Community.

Not run against Enterprise yet, see the assumptions in odoo/seed/seed_mcp.py.
"""

import json

import pytest
import requests
from conftest import ADMIN_KEY, ODOO_URL, json2_ok

MCP_KEY = "odoo-supersecr3tmcpkeyfordevelop1"


@pytest.fixture(scope="module", autouse=True)
def ai_mcp_installed():
    if not json2_ok("ir.module.module", "search_count", domain=[["name", "=", "ai_mcp"], ["state", "=", "installed"]]):
        pytest.skip("ai_mcp is not installed (Odoo Enterprise only, make up ENTERPRISE=<dir>)")


def mcp(method, key=MCP_KEY, session=None, params=None):
    """Send one JSON-RPC request over streamable HTTP, returning the response."""
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    return requests.post(f"{ODOO_URL}/mcp", headers=headers, json=body, timeout=60)


def result(response):
    assert response.status_code == 200, response.text
    if response.headers.get("Content-Type", "").startswith("text/event-stream"):
        data = [line[5:] for line in response.text.splitlines() if line.startswith("data:")]
        message = json.loads(data[-1])
    else:
        message = response.json()
    assert "error" not in message, message
    return message["result"]


def initialize(key=MCP_KEY):
    response = mcp(
        "initialize",
        key=key,
        params={
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "noodle-tests", "version": "1"},
        },
    )
    return response, response.headers.get("Mcp-Session-Id")


def test_oauth_metadata():
    response = requests.get(f"{ODOO_URL}/.well-known/oauth-authorization-server", timeout=30)
    assert response.status_code == 200
    metadata = response.json()
    assert metadata["issuer"].startswith(ODOO_URL)
    # Claude Code registers itself, the seed enables dynamic client registration
    assert metadata.get("registration_endpoint")


def test_tools_with_mcp_key():
    response, session = initialize()
    assert result(response)["serverInfo"]
    tools = result(mcp("tools/list", session=session))["tools"]
    assert tools, "no tools available in MCP"


def test_rpc_key_is_rejected():
    response, _session = initialize(key=ADMIN_KEY)
    assert response.status_code == 401

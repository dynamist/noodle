"""Odoo answers through the shared Traefik ingress."""

import http.client
from urllib.parse import urlparse

import requests
from conftest import ADMIN_KEY, ODOO_URL, json2, json2_ok


def test_health():
    response = requests.get(f"{ODOO_URL}/web/health", timeout=30)
    assert response.status_code == 200
    assert response.json()["status"] == "pass"


def test_login_page():
    assert requests.get(f"{ODOO_URL}/web/login", timeout=30).status_code == 200


def test_unknown_host_is_not_routed():
    host = urlparse(ODOO_URL).hostname
    response = requests.get(ODOO_URL.replace(host, "127.0.0.1"), headers={"Host": "nope.localhost"}, timeout=30)
    assert response.status_code == 404


def test_admin_api_key():
    [admin] = json2_ok("res.users", "search_read", domain=[["login", "=", "admin"]], fields=["login"])
    assert admin["login"] == "admin"


def test_wrong_api_key_is_rejected():
    assert json2("res.users", "context_get", key=ADMIN_KEY + "x").status_code == 401


def test_websocket_upgrade():
    """Odoo 19 serves its bus on /websocket, Traefik must pass the upgrade through."""
    url = urlparse(ODOO_URL)
    conn = http.client.HTTPConnection(url.hostname, url.port or 80, timeout=30)
    conn.request(
        "GET",
        "/websocket",
        headers={
            "Connection": "Upgrade",
            "Upgrade": "websocket",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            "Origin": ODOO_URL,
        },
    )
    assert conn.getresponse().status == 101

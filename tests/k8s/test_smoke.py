"""Odoo answers through the shared Traefik ingress."""

import http.client
import os
import re
from urllib.parse import urlparse

import pytest
import requests
from conftest import ADMIN_KEY, ODOO_URL, json2, json2_ok


def test_health():
    response = requests.get(f"{ODOO_URL}/web/health", timeout=30)
    assert response.status_code == 200
    assert response.json()["status"] == "pass"


def test_login_page():
    assert requests.get(f"{ODOO_URL}/web/login", timeout=30).status_code == 200


def test_website_homepage():
    """The public website serves the homepage of addons/noodle_website."""
    response = requests.get(f"{ODOO_URL}/", timeout=30)
    assert response.status_code == 200
    assert "o_noodle_hero" in response.text


def test_website_contact_details():
    """The header and footer show the Dynamist phone number and email address instead of the placeholders."""
    text = requests.get(f"{ODOO_URL}/", timeout=30).text
    assert "+46 (0)8-DYNAMI" in text
    assert 'href="tel:+468396264"' in text
    assert "555-555-5556" not in text
    assert 'href="mailto:hello@dynamist.se"' in text
    assert "yourcompany" not in text


def test_website_about_page():
    response = requests.get(f"{ODOO_URL}/about", timeout=30)
    assert response.status_code == 200
    assert 'href="/about"' in requests.get(f"{ODOO_URL}/", timeout=30).text


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
    """Odoo serves its bus on /websocket, Traefik must pass the upgrade through."""
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


def test_odoo_series():
    """The deployed Odoo is the series of the VERSION it was built from (make passes NOODLE_VERSION)."""
    match = re.fullmatch(r"(\d+)(-nightly)?", os.environ.get("NOODLE_VERSION", ""))
    if not match:
        pytest.skip("no NOODLE_VERSION with a series, e.g. master")
    response = requests.post(f"{ODOO_URL}/web/webclient/version_info", json={}, timeout=30)
    assert response.json()["result"]["server_serie"] == f"{match[1]}.0"

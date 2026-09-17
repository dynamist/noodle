"""The seeding created what the docs promise, and does not create it twice."""

import pytest
import seed_common
from conftest import ODOO_URL, json2, json2_ok, kubectl

# Sample records of odoo/seed/datasets/, by xmlid name under __noodle__
SAMPLE_XMLIDS = {
    "partner_exempel",
    "product_consulting_hour",
    "lead_astrid",
    "lead_johan",
    "sale_order_exempel",
    "project_sandbox",
    "project_sandbox_task_1",
    "project_sandbox_task_2",
    "project_sandbox_task_3",
}


def test_base_url_is_the_ingress_url():
    [param] = json2_ok("ir.config_parameter", "search_read", domain=[["key", "=", "web.base.url"]], fields=["value"])
    assert param["value"] == ODOO_URL


def test_users_have_their_role_groups(test_users):
    for login, name, role in test_users:
        [user] = json2_ok(
            "res.users",
            "search_read",
            domain=[["login", "=", login]],
            fields=["name", "active"],
            context={"active_test": False},
        )
        assert user["name"] == name and user["active"], login
        expected = seed_common.ROLES[role] if role == "portal" else ["base.group_user", *seed_common.ROLES[role]]
        for group in expected:
            assert json2_ok("res.users", "has_group", ids=[user["id"]], group_ext_id=group), f"{login} not in {group}"


def test_user_api_keys(test_users):
    for login, _name, role in test_users:
        key = seed_common.user_api_key(login)
        response = json2("res.users", "search_read", key=key, domain=[["login", "=", login]], fields=["login"])
        if role == "portal":
            assert response.status_code == 401, f"portal user {login} must not have an API key"
        else:
            assert response.status_code == 200, f"API key of {login}: {response.text}"


def test_sample_records_exist():
    records = json2_ok("ir.model.data", "search_read", domain=[["module", "=", "__noodle__"]], fields=["name"])
    assert SAMPLE_XMLIDS <= {record["name"] for record in records}


def test_sales_user_sees_fewer_leads_than_sales_manager():
    astrid = json2_ok("crm.lead", "search_count", key=seed_common.user_api_key("astrid.lindqvist"), domain=[])
    johan = json2_ok("crm.lead", "search_count", key=seed_common.user_api_key("johan.bergman"), domain=[])
    assert 0 < astrid < johan


@pytest.mark.slow
def test_seeding_again_creates_nothing():
    result = kubectl("exec", "deploy/odoo", "--", "/opt/noodle/init-odoo.sh", "--seed-only", timeout=600)
    assert "Seeding done!" in result.stdout
    assert "Created" not in result.stdout, result.stdout

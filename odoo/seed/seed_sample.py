"""A few records owned by the test users, for testing access rules.

Odoo's demo data provides the bulk of the sample data.
"""

from odoo.fields import Command
from seed_common import ensure_record, find_user


def run(env):
    customer = ensure_record(
        env,
        "partner_exempel",
        "res.partner",
        {
            "name": "Exempel AB",
            "is_company": True,
            "email": "info@exempel.example.com",
            "city": "Stockholm",
            "country_id": env.ref("base.se").id,
        },
    )

    # The portal user is a contact of the customer, so it sees the customer's orders
    portal_user = find_user(env, "olof.nystrom")
    if portal_user and portal_user.partner_id.parent_id != customer:
        portal_user.partner_id.parent_id = customer

    salesperson = find_user(env, "astrid.lindqvist")
    sales_manager = find_user(env, "johan.bergman")
    project_manager = find_user(env, "per.lundgren")

    if "product.product" in env:
        product = ensure_record(
            env,
            "product_consulting_hour",
            "product.product",
            {"name": "odoo-dev Consulting Hour", "type": "service", "list_price": 1200.0},
        )

    if "crm.lead" in env:
        ensure_record(
            env,
            "lead_astrid",
            "crm.lead",
            {
                "name": "Exempel AB: tooling workshop",
                "type": "opportunity",
                "partner_id": customer.id,
                "user_id": salesperson.id,
                "expected_revenue": 24000.0,
            },
        )
        ensure_record(
            env,
            "lead_johan",
            "crm.lead",
            {
                "name": "Exempel AB: support contract",
                "type": "opportunity",
                "partner_id": customer.id,
                "user_id": sales_manager.id,
                "expected_revenue": 96000.0,
            },
        )

    if "sale.order" in env:
        ensure_record(
            env,
            "sale_order_exempel",
            "sale.order",
            {
                "partner_id": customer.id,
                "user_id": salesperson.id,
                "order_line": [Command.create({"product_id": product.id, "product_uom_qty": 20})],
            },
        )

    if "project.project" in env:
        project = ensure_record(
            env,
            "project_sandbox",
            "project.project",
            {"name": "odoo-dev Sandbox", "user_id": project_manager.id, "partner_id": customer.id},
        )
        for number, task_name in enumerate(["Set up API access", "Write import script", "Review access rules"], 1):
            ensure_record(
                env,
                f"project_sandbox_task_{number}",
                "project.task",
                {"name": task_name, "project_id": project.id, "user_ids": [Command.set([project_manager.id])]},
            )

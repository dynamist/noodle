"""A quotation for the customer, visible to the portal user."""

from seed_datasets import Command, dataset, ensure_record, ref, user


@dataset(modules=["sale"], after=["partners", "products"])
def sale(env):
    ensure_record(
        env,
        "sale_order_exempel",
        "sale.order",
        {
            "partner_id": ref(env, "partner_exempel").id,
            "user_id": user(env, "astrid.lindqvist").id,
            "order_line": [
                Command.create({"product_id": ref(env, "product_consulting_hour").id, "product_uom_qty": 20}),
            ],
        },
    )

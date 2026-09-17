"""Opportunities owned by a sales user and a sales administrator, so Astrid sees fewer leads than Johan."""

from seed_datasets import dataset, ensure_record, ref, user


@dataset(modules=["crm"], after=["partners"])
def crm(env):
    leads = [
        ("lead_astrid", "Exempel AB: tooling workshop", "astrid.lindqvist", 24000.0),
        ("lead_johan", "Exempel AB: support contract", "johan.bergman", 96000.0),
    ]
    for name, title, login, revenue in leads:
        ensure_record(
            env,
            name,
            "crm.lead",
            {
                "name": title,
                "type": "opportunity",
                "partner_id": ref(env, "partner_exempel").id,
                "user_id": user(env, login).id,
                "expected_revenue": revenue,
            },
        )

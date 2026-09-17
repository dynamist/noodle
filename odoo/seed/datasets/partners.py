"""Customer company, with the portal test user as its contact."""

from seed_datasets import dataset, ensure_record, id_of, ref, user


@dataset()
def partners(env):
    customer = ensure_record(
        env,
        "partner_exempel",
        "res.partner",
        {
            "name": "Exempel AB",
            "is_company": True,
            "email": "info@exempel.example.com",
            "city": "Stockholm",
            "country_id": ref(env, "base.se").id,
        },
    )

    # The portal user is a contact of the customer, so it sees the customer's orders
    contact = user(env, "olof.nystrom").partner_id
    if id_of(contact.parent_id) != customer.id:
        contact.write({"parent_id": customer.id})

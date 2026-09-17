"""Products used by the other datasets."""

from seed_datasets import dataset, ensure_record


@dataset(modules=["product"])
def products(env):
    ensure_record(
        env,
        "product_consulting_hour",
        "product.product",
        {"name": "noodle Consulting Hour", "type": "service", "list_price": 1200.0},
    )

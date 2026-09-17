"""A project for the customer with tasks assigned to the project manager."""

from seed_datasets import Command, dataset, ensure_record, ref, user


@dataset(modules=["project"], after=["partners"])
def project(env):
    manager = user(env, "per.lundgren")
    sandbox = ensure_record(
        env,
        "project_sandbox",
        "project.project",
        {"name": "oodev Sandbox", "user_id": manager.id, "partner_id": ref(env, "partner_exempel").id},
    )
    for number, task_name in enumerate(["Set up API access", "Write import script", "Review access rules"], 1):
        ensure_record(
            env,
            f"project_sandbox_task_{number}",
            "project.task",
            {"name": task_name, "project_id": sandbox.id, "user_ids": [Command.set([manager.id])]},
        )

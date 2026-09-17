"""A project for the customer with kanban stages and tasks assigned to the project manager."""

from seed_datasets import Command, dataset, ensure_record, ref, user

STAGES = [
    ("backlog", "Backlog"),
    ("up_next", "Up next"),
    ("in_progress", "In progress"),
    ("in_review", "In review"),
    ("done", "Done"),
]


@dataset(modules=["project"], after=["partners"])
def project(env):
    manager = user(env, "per.lundgren")
    sandbox = ensure_record(
        env,
        "project_sandbox",
        "project.project",
        {"name": "noodle Sandbox", "user_id": manager.id, "partner_id": ref(env, "partner_exempel").id},
    )
    stages = {
        key: ensure_record(
            env,
            f"project_sandbox_stage_{key}",
            "project.task.type",
            {"name": name, "sequence": number * 10, "project_ids": [Command.link(sandbox.id)]},
        )
        for number, (key, name) in enumerate(STAGES, 1)
    }
    tasks = [("Set up API access", "backlog"), ("Write import script", "backlog"), ("Review access rules", "up_next")]
    for number, (task_name, stage) in enumerate(tasks, 1):
        task = ensure_record(
            env,
            f"project_sandbox_task_{number}",
            "project.task",
            {
                "name": task_name,
                "project_id": sandbox.id,
                "stage_id": stages[stage].id,
                "user_ids": [Command.set([manager.id])],
            },
        )
        # Tasks created before the project had stages are outside any column
        if not task.stage_id:
            task.write({"stage_id": stages[stage].id})

"""A datacenter migration in progress, with the team of the fictional customer Robot Mechanics Inc.

The people and their roles are the ones in the RMI GUNNAR design specification.
"""

from seed_datasets import Command, dataset, ensure_record, ref

STAGES = [
    ("backlog", "Backlog"),
    ("up_next", "Up next"),
    ("in_progress", "In progress"),
    ("in_review", "In review"),
    ("done", "Done"),
]

# login, name, job title, project role
TEAM = [
    ("mikael.wallin", "Mikael Wallin", "Team Lead", "manager"),
    ("ove.pettersson", "Ove Pettersson", "System Architect", "user"),
    ("viola.larsson", "Viola Larsson", "System Administrator", "user"),
    ("daniel.lindgren", "Daniel Lindgren", "DevOps Engineer", "user"),
    ("tommy.svensson", "Tommy Svensson", "QA Engineer", "user"),
]

GROUPS = {
    "manager": ["base.group_user", "project.group_project_manager"],
    "user": ["base.group_user", "project.group_project_user"],
}

# name, stage, assignees, state
TASKS = [
    ("Replace the UPS units in the rack room", "done", ["viola.larsson"], "1_done"),
    ("Physical network: structured cabling and patch panels", "in_review", ["viola.larsson"], "03_approved"),
    ("Layer 2 networking: VLANs and switch configuration", "in_progress", ["daniel.lindgren"], "01_in_progress"),
    ("Routing: OSPF between the old and the new site", "up_next", ["ove.pettersson", "daniel.lindgren"], None),
    ("VPN: site-to-site tunnel for the migration window", "backlog", ["daniel.lindgren"], None),
    ("Acceptance test of the migrated racks", "backlog", ["tommy.svensson"], None),
]


@dataset(modules=["project"])
def datacenter(env):
    team = {}
    for login, name, job_title, role in TEAM:
        team[login] = ensure_record(
            env,
            f"user_{login.replace('.', '_')}",
            "res.users",
            {
                "name": name,
                "login": login,
                "email": f"{login}@air.rmi.se",
                "tz": "Europe/Stockholm",
                "group_ids": [Command.set([ref(env, group).id for group in GROUPS[role]])],
            },
            # Creating a user mails an invitation, this instance has no mail server
            context={"no_reset_password": True},
        )
    customer = ensure_record(
        env,
        "partner_rmi",
        "res.partner",
        {"name": "Robot Mechanics Inc", "is_company": True, "email": "info@air.rmi.se"},
    )
    migration = ensure_record(
        env,
        "project_datacenter",
        "project.project",
        {
            "name": "Datacenter migration",
            "user_id": team["mikael.wallin"].id,
            "partner_id": customer.id,
        },
    )
    stages = {
        key: ensure_record(
            env,
            f"project_datacenter_stage_{key}",
            "project.task.type",
            {"name": name, "sequence": number * 10, "project_ids": [Command.link(migration.id)]},
        )
        for number, (key, name) in enumerate(STAGES, 1)
    }
    for number, (task_name, stage, assignees, state) in enumerate(TASKS, 1):
        vals = {
            "name": task_name,
            "project_id": migration.id,
            "stage_id": stages[stage].id,
            "user_ids": [Command.set([team[login].id for login in assignees])],
        }
        if state:
            vals["state"] = state
        ensure_record(env, f"project_datacenter_task_{number}", "project.task", vals)

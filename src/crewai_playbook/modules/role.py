from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from crewai_playbook.models.playbook import Role, Task
from crewai_playbook.utils.errors import RoleError


def load_role_tasks(
    role_name: str,
    roles_path: str | Path = "roles",
    role_vars: Optional[Dict[str, Any]] = None,
) -> tuple[List[Task], Dict[str, Any]]:
    """Load a role's tasks and merged variables.

    Returns ``(tasks, merged_vars)`` where merged_vars is
    ``{**defaults, **role_vars}``.
    """
    role_dir = Path(roles_path) / role_name
    if not role_dir.exists():
        raise RoleError(f"role '{role_name}' not found at {role_dir}")

    defaults: Dict[str, Any] = {}
    defaults_file = role_dir / "defaults" / "main.yml"
    if defaults_file.exists():
        with open(defaults_file) as f:
            raw = yaml.safe_load(f)
            if isinstance(raw, dict):
                defaults = raw

    tasks_file = role_dir / "tasks" / "main.yml"
    if not tasks_file.exists():
        raise RoleError(
            f"role '{role_name}' has no tasks/main.yml at {tasks_file}"
        )

    with open(tasks_file) as f:
        raw_tasks = yaml.safe_load(f)
    if not isinstance(raw_tasks, list):
        raise RoleError(
            f"role '{role_name}' tasks/main.yml must be a list"
        )

    from crewai_playbook.core.parser import _parse_task
    tasks: List[Task] = []
    for i, item in enumerate(raw_tasks):
        if not isinstance(item, dict):
            raise RoleError(
                f"role '{role_name}' task #{i + 1} must be a mapping"
            )
        tasks.append(_parse_task(item, f"role:{role_name}", i + 1))

    merged_vars = {**defaults, **(role_vars or {})}
    return tasks, merged_vars


def resolve_role_tasks(
    roles: List[Role],
    roles_path: str | Path = "roles",
) -> List[tuple[Task, Dict[str, Any]]]:
    """Resolve a list of role references into their task lists.

    Returns a list of ``(task, merged_vars)`` tuples in execution order.
    """
    result: List[tuple[Task, Dict[str, Any]]] = []
    for role_ref in roles:
        tasks, merged_vars = load_role_tasks(
            role_ref.role, roles_path, role_ref.vars
        )
        for task in tasks:
            result.append((task, merged_vars))
    return result

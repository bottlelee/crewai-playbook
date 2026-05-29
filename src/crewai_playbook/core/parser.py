from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from crewai_playbook.models.playbook import (
    Block,
    Handler,
    Play,
    Playbook,
    Task,
    Role,
)
from crewai_playbook.utils.errors import ParseError
from crewai_playbook.utils.vars import collect_variable_refs


def parse_playbook(path: str | Path) -> Playbook:
    """Read and validate a YAML playbook file.

    Returns a :class:`Playbook` instance on success.
    """
    p = Path(path)
    if not p.exists():
        raise ParseError(f"playbook not found: {p}")
    if not p.suffix.lower() in (".yml", ".yaml"):
        raise ParseError(f"playbook must have a .yml or .yaml extension")

    with open(p) as f:
        try:
            raw = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ParseError(f"YAML parse error in {p}: {exc}") from exc

    if not isinstance(raw, list):
        raise ParseError(f"playbook must be a list of plays (YAML sequence)")

    plays: List[Play] = []
    for i, play_raw in enumerate(raw):
        if not isinstance(play_raw, dict):
            raise ParseError(f"play #{i + 1} must be a mapping")
        plays.append(_parse_play(play_raw, i + 1))

    return Playbook(plays=plays)


def _parse_play(raw: Dict[str, Any], index: int) -> Play:
    missing = _require_keys(raw, {"name", "agents"})
    if missing:
        raise ParseError(f"play #{index} missing required key(s): {missing}")

    if not isinstance(raw.get("agents"), list):
        raise ParseError(f"play #{index} 'agents' must be a list")

    tasks: Optional[List[Task | Block]] = None
    if "tasks" in raw:
        tasks = _parse_task_list(raw["tasks"], index)

    roles: Optional[List[Role]] = None
    if "roles" in raw:
        roles = _parse_role_list(raw["roles"], index)

    handlers: Optional[List[Handler]] = None
    if "handlers" in raw:
        handlers = _parse_handler_list(raw["handlers"], index)

    raw_process = raw.get("process", "sequential")
    if raw_process not in ("sequential", "hierarchical"):
        raise ParseError(
            f"play #{index} 'process' must be 'sequential' or 'hierarchical'"
        )

    return Play(
        name=raw["name"],
        agents=raw["agents"],
        vars=raw.get("vars"),
        tasks=tasks,
        roles=roles,
        handlers=handlers,
        become=raw.get("become", False),
        gather_facts=raw.get("gather_facts", True),
        tags=raw.get("tags"),
        process=raw_process,
    )


def _parse_task_list(raw_tasks: list, play_index: int) -> List[Task | Block]:
    tasks: List[Task | Block] = []
    for i, item in enumerate(raw_tasks):
        if not isinstance(item, dict):
            raise ParseError(
                f"play #{play_index} task #{i + 1} must be a mapping"
            )
        if "block" in item:
            tasks.append(_parse_block(item, play_index, i + 1))
        else:
            tasks.append(_parse_task(item, play_index, i + 1))
    return tasks


def _parse_task(raw: Dict[str, Any], play_index: int, task_index: int) -> Task:
    missing = _require_keys(raw, {"name", "task", "agents"})
    if missing:
        raise ParseError(
            f"play #{play_index} task #{task_index} missing: {missing}"
        )
    register_raw = raw.get("register")
    return Task(
        name=raw["name"],
        agents=raw["agents"],
        task=raw["task"],
        src=raw.get("src"),
        dest=raw.get("dest"),
        register_var=register_raw,
        when=raw.get("when"),
        notify=_ensure_list(raw.get("notify")),
        until=raw.get("until"),
        retries=raw.get("retries"),
        delay=raw.get("delay"),
        tags=_ensure_list(raw.get("tags")),
        vars=raw.get("vars"),
    )


def _parse_block(raw: Dict[str, Any], play_index: int, index: int) -> Block:
    if not isinstance(raw.get("block"), list):
        raise ParseError(
            f"play #{play_index} block #{index} 'block' must be a list"
        )
    block_tasks = [_parse_task(t, play_index, f"{index}.block")
                   for t in raw["block"]]
    rescue_tasks = None
    if "rescue" in raw:
        if not isinstance(raw["rescue"], list):
            raise ParseError(
                f"play #{play_index} block #{index} 'rescue' must be a list"
            )
        rescue_tasks = [_parse_task(t, play_index, f"{index}.rescue")
                        for t in raw["rescue"]]
    always_tasks = None
    if "always" in raw:
        if not isinstance(raw["always"], list):
            raise ParseError(
                f"play #{play_index} block #{index} 'always' must be a list"
            )
        always_tasks = [_parse_task(t, play_index, f"{index}.always")
                        for t in raw["always"]]
    return Block(
        block=block_tasks,
        rescue=rescue_tasks,
        always=always_tasks,
        when=raw.get("when"),
        tags=_ensure_list(raw.get("tags")),
    )


def _parse_role_list(raw_roles: list, play_index: int) -> List[Role]:
    roles: List[Role] = []
    for i, item in enumerate(raw_roles):
        if isinstance(item, str):
            roles.append(Role(role=item))
        elif isinstance(item, dict):
            roles.append(Role(
                role=item.get("role", ""),
                vars=item.get("vars"),
                tags=_ensure_list(item.get("tags")),
                when=item.get("when"),
            ))
        else:
            raise ParseError(
                f"play #{play_index} role #{i + 1} must be a string or mapping"
            )
    return roles


def _parse_handler_list(raw: list, play_index: int) -> List[Handler]:
    handlers: List[Handler] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict) or "name" not in item:
            raise ParseError(
                f"play #{play_index} handler #{i + 1} must have a 'name'"
            )
        handlers.append(Handler(
            name=item["name"],
            tasks=_parse_task_list(item.get("tasks", []), play_index),
        ))
    return handlers


def _require_keys(d: Dict[str, Any], keys: set[str]) -> set[str]:
    return keys - set(d.keys())


def _ensure_list(val: Any) -> Optional[list]:
    if val is None:
        return None
    if isinstance(val, list):
        return val
    return [val]


def syntax_check(path: str | Path) -> List[str]:
    """Validate a playbook's syntax without executing it.

    Returns a list of error messages (empty if valid).
    """
    errors: List[str] = []
    try:
        playbook = parse_playbook(path)
    except ParseError as exc:
        return [str(exc)]

    known_vars = {
        "facts", "hostvars", "groups", "inventory_hostname",
        "ansible_play_name", "ansible_play_hosts",
    }

    for play_idx, play in enumerate(playbook.plays):
        if not play.name.strip():
            errors.append(f"play #{play_idx + 1}: 'name' must not be empty")
        if not play.agents:
            errors.append(
                f"play #{play_idx + 1} '{play.name}': 'agents' must not be empty"
            )

        play_known = set(known_vars)
        if play.vars:
            play_known.update(play.vars.keys())

        registered_vars: set[str] = set()
        for task_list in (play.tasks or []):
            if isinstance(task_list, Block):
                _check_block_refs(task_list, play, play_known | registered_vars, errors)
                for bt in task_list.block:
                    if bt.register_var:
                        registered_vars.add(bt.register_var)
                for rt in (task_list.rescue or []):
                    if rt.register_var:
                        registered_vars.add(rt.register_var)
            else:
                _check_task_refs(task_list, play, play_known | registered_vars, errors)
                if task_list.register_var:
                    registered_vars.add(task_list.register_var)
    return errors


def _check_task_refs(task: Task, play: Play, known: set[str],
                     errors: List[str]) -> None:
    for val in (task.when, task.until, task.task):
        if val:
            refs = collect_variable_refs(val)
            unknown = refs - known
            if unknown:
                errors.append(
                    f"play '{play.name}' task '{task.name}': "
                    f"undefined variable(s): {unknown}"
                )
    for cond in ("when", "until"):
        val = getattr(task, cond, None)
        if val and "{{" not in str(val) and "}}" not in str(val):
            pass


def _check_block_refs(block: Block, play: Play, known: set[str],
                      errors: List[str]) -> None:
    for task in block.block:
        _check_task_refs(task, play, known, errors)
    if block.rescue:
        for task in block.rescue:
            _check_task_refs(task, play, known, errors)
    if block.always:
        for task in block.always:
            _check_task_refs(task, play, known, errors)

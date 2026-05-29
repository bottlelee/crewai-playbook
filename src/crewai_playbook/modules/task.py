from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from crewai_playbook.core.runner import run_single_task
from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.models.playbook import Task as PlaybookTask
from crewai_playbook.utils.errors import ExecutionError
from crewai_playbook.utils.vars import resolve_vars


def _read_src(path_str: str) -> str:
    """Read the content of a ``src`` file.

    Returns empty string if the file does not exist.
    """
    p = Path(path_str)
    if not p.exists():
        return ""
    return p.read_text()


def _write_dest(path_str: str, content: str) -> None:
    """Write *content* to a ``dest`` file path.

    Creates parent directories as needed.
    """
    p = Path(path_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def execute_task(
    task: PlaybookTask,
    inventory: Dict[str, AgentDefinition],
    variable_context: Dict[str, Any],
    verbose: bool = False,
) -> str:
    """Execute a single playbook task, with retry/until/delay support,
    optional ``src`` file input, and ``dest`` file output.

    *   If ``task.src`` is set, the file content is prepended to the task
        description as additional context.
    *   If ``task.dest`` is set, the task output is written to that file
        after successful execution.

    Returns the task output string.
    """
    resolved_description = resolve_vars(task.task, variable_context)
    resolved_when = resolve_vars(task.when, variable_context) if task.when else None

    if resolved_when is not None:
        if isinstance(resolved_when, str) and resolved_when.strip():
            if not _evaluate_when(resolved_when, variable_context):
                return ""

    resolved_src = resolve_vars(task.src, variable_context) if task.src else None
    resolved_dest = resolve_vars(task.dest, variable_context) if task.dest else None

    if resolved_src:
        src_content = _read_src(resolved_src)
        if src_content:
            resolved_description = (
                f"Context from {resolved_src}:\n{src_content}\n\n"
                f"Task:\n{resolved_description}"
            )

    last_error: Optional[Exception] = None
    result_text = ""

    retries = task.retries or 1
    delay = task.delay or 0

    for attempt in range(1, retries + 1):
        try:
            result_text = run_single_task(
                task_description=resolved_description,
                agent_names=task.agents,
                inventory=inventory,
                verbose=verbose,
            )

            if task.until:
                resolved_until = resolve_vars(task.until, {
                    **variable_context,
                    "result": result_text,
                })
                if not _evaluate_condition(resolved_until, result_text):
                    raise ExecutionError(
                        f"until condition not met: {task.until}"
                    )

            if resolved_dest and result_text:
                _write_dest(resolved_dest, result_text)

            if task.register_var:
                variable_context[task.register_var] = result_text
                variable_context[f"{task.register_var}_is_defined"] = True
                variable_context[f"{task.register_var}_succeeded"] = True

            return result_text

        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(delay)

    raise ExecutionError(
        f"task '{task.name}' failed after {retries} retries: {last_error}"
    ) from last_error


def _evaluate_when(condition: str, context: Dict[str, Any]) -> bool:
    """Evaluate a simple ``when`` condition.

    Supports basic checks like ``result is defined``,
    ``result_var is succeeded``, and truthy string checks.
    """
    cond = condition.strip().lower()
    if "is defined" in cond:
        var_name = cond.split("is defined")[0].strip()
        return var_name in context or f"{var_name}_is_defined" in context
    if "is succeeded" in cond:
        var_name = cond.split("is succeeded")[0].strip()
        return context.get(f"{var_name}_succeeded", False)
    if "is not defined" in cond:
        var_name = cond.split("is not defined")[0].strip()
        return var_name not in context and f"{var_name}_is_defined" not in context
    if cond in ("true", "yes", "1"):
        return True
    if cond in ("false", "no", "0"):
        return False
    return bool(cond) if cond else True


def _evaluate_condition(condition: str, result_text: str) -> bool:
    """Evaluate an ``until`` condition against the task result."""
    cond_lower = condition.strip().lower()
    if cond_lower == "result is succeeded":
        return True
    if cond_lower == "result is not succeeded":
        return False
    if cond_lower.startswith("result contains "):
        prefix_len = len("result contains ")
        raw_needle = condition.strip()[prefix_len:].strip().strip("\"'")
        return raw_needle in result_text
    return bool(result_text)

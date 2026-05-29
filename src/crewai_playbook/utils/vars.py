from __future__ import annotations

import re
from typing import Any, Dict

from crewai_playbook.utils.errors import VariableError

_VAR_PATTERN = re.compile(r"\{\{\s*(\w+(?:\.\w+)*)\s*\}\}")


def resolve_vars(value: Any, context: Dict[str, Any]) -> Any:
    """Resolve ``{{ var }}`` patterns in a value using the context dict.

    Supports simple dotted paths inside the braces, e.g. ``{{ facts.os }}``.
    """
    if isinstance(value, str):
        def _replace(match: re.Match) -> str:
            path = match.group(1)
            parts = path.split(".")
            cur: Any = context
            for part in parts:
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    raise VariableError(f"undefined variable '{path}'")
            return str(cur)
        return _VAR_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: resolve_vars(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_vars(item, context) for item in value]
    return value


def collect_variable_refs(value: Any) -> set[str]:
    """Return the set of variable names referenced in *value* (or its
    children) without resolving them."""
    refs: set[str] = set()
    if isinstance(value, str):
        for match in _VAR_PATTERN.finditer(value):
            refs.add(match.group(1))
    elif isinstance(value, dict):
        for v in value.values():
            refs.update(collect_variable_refs(v))
    elif isinstance(value, list):
        for item in value:
            refs.update(collect_variable_refs(item))
    return refs

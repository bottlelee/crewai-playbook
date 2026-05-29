from __future__ import annotations

from typing import Any, Dict


def debug(
    msg: str,
    var: str = "",
    variable_context: Dict[str, Any] = None,
    verbose: bool = False,
) -> str:
    """Print a debug message and optional variable value.

    Analogous to Ansible's ``debug`` module.
    Returns the formatted message string.
    """
    output_parts: list[str] = []

    if msg:
        output_parts.append(f"msg: {msg}")

    if var and variable_context is not None and var in variable_context:
        value = variable_context[var]
        output_parts.append(f"{var}: {value!r}")
    elif var:
        output_parts.append(f"{var}: UNDEFINED")

    output = "\n".join(output_parts)
    return output

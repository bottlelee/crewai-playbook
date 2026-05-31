from __future__ import annotations

import getpass
from typing import Any, Dict, List, Optional

from crewai_playbook.models.playbook import VarPrompt
from crewai_playbook.utils.errors import ExecutionError


def prompt_vars(
    prompts: List[VarPrompt],
    already_defined: Optional[Dict[str, Any]] = None,
    console: Any = None,
) -> Dict[str, Any]:
    """Interactively prompt the user for variable values.

    Variables whose names already exist in *already_defined* are skipped
    (this is how ``-e`` overrides ``vars_prompt``).

    Parameters
    ----------
    prompts:
        The ``vars_prompt`` entries from the play.
    already_defined:
        Variables already set (e.g. from ``-e`` / extra-vars).
        Any prompt whose ``name`` is a key in this dict is silently skipped.
    console:
        An optional ``rich.console.Console`` instance for pretty output.
        When *None* a plain ``input()`` / ``getpass`` call is used.

    Returns
    -------
    dict
        A mapping of variable names to the values entered by the user.
    """
    already_defined = already_defined or {}
    result: Dict[str, Any] = {}

    for vp in prompts:
        # Skip if already provided via extra-vars
        if vp.name in already_defined:
            continue

        value = _prompt_single(vp, console)
        result[vp.name] = value

    return result


def _prompt_single(vp: VarPrompt, console: Any = None) -> str:
    """Prompt for a single variable and return the user's answer."""
    # Build the prompt text
    if vp.prompt:
        label = vp.prompt
    else:
        label = f"Enter value for {vp.name}"

    # Append default hint
    if vp.default is not None:
        label = f"{label} [{vp.default}]"

    # Append choices hint
    if vp.choices:
        label = f"{label} ({'/'.join(vp.choices)})"

    label = f"{label}: "

    while True:
        try:
            if vp.private:
                value = getpass.getpass(label)
            else:
                if console is not None:
                    console.print(f"[bold cyan]?[/bold cyan] {vp.prompt or vp.name}", end="")
                    if vp.default is not None:
                        console.print(f" [dim]\\[{vp.default}][/dim]", end="")
                    if vp.choices:
                        console.print(f" [dim]({'/'.join(vp.choices)})[/dim]", end="")
                    console.print(": ", end="")
                    value = input()
                else:
                    value = input(label)
        except (EOFError, KeyboardInterrupt):
            # Non-interactive environment — fall back to default or empty
            return vp.default or ""

        # Apply default if empty
        if not value and vp.default is not None:
            return vp.default

        # Validate choices
        if vp.choices and value not in vp.choices:
            msg = f"Invalid choice '{value}'. Must be one of: {', '.join(vp.choices)}"
            if console is not None:
                console.print(f"[red]ERROR:[/red] {msg}")
            else:
                print(f"ERROR: {msg}")
            continue

        return value

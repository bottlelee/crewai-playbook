from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import typer
from rich.console import Console
from typer.core import TyperGroup

from crewai_playbook import __version__
from crewai_playbook.cli import flags
from crewai_playbook.core.executor import PlaybookExecutor
from crewai_playbook.core.inventory import load_inventory, resolve_agents
from crewai_playbook.core.parser import parse_playbook, syntax_check
from crewai_playbook.utils.config import default_inventory_path, load_project_config
from crewai_playbook.utils.errors import (
    CrewAIBookError,
    ParseError,
)


class _DefaultGroup(TyperGroup):
    """Typer Group that falls back to the ``run`` command when the first
    positional argument does not match any registered subcommand."""

    default_cmd_name = "run"

    def resolve_command(self, ctx, args):
        if args and not args[0].startswith("-"):
            cmd_name = click.utils.make_str(args[0])
            if cmd_name not in self.commands:
                cmd = self.get_command(ctx, self.default_cmd_name)
                if cmd is not None:
                    return self.default_cmd_name, cmd, list(args)
        return super().resolve_command(ctx, args)


app = typer.Typer(
    name="crewai-playbook",
    cls=_DefaultGroup,
    help="Ansible-compatible YAML playbook orchestrator for crewAI agents.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"crewai-playbook v{__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit.",
        callback=_version_callback, is_eager=True,
    ),
) -> None:
    pass


@app.command()
def run(
    playbook: str = typer.Argument(
        ..., help="Path to the playbook YAML file."
    ),
    check: bool = typer.Option(False, "--check", help=flags.CHECK_HELP),
    diff: bool = typer.Option(False, "--diff", help=flags.DIFF_HELP),
    syntax_check_flag: bool = typer.Option(
        False, "--syntax-check", help=flags.SYNTAX_HELP
    ),
    tags: Optional[List[str]] = typer.Option(
        None, "--tags", help=flags.TAGS_HELP
    ),
    skip_tags: Optional[List[str]] = typer.Option(
        None, "--skip-tags", help=flags.SKIP_TAGS_HELP
    ),
    list_tasks: bool = typer.Option(
        False, "--list-tasks", help=flags.LIST_TASKS_HELP
    ),
    list_tags: bool = typer.Option(
        False, "--list-tags", help=flags.LIST_TAGS_HELP
    ),
    limit: Optional[List[str]] = typer.Option(
        None, "--limit", help=flags.LIMIT_HELP
    ),
    extra_vars: Optional[List[str]] = typer.Option(
        None, "-e", "--extra-vars", help=flags.EXTRA_VARS_HELP
    ),
    verbose: int = typer.Option(
        0, "-v", "--verbose", count=True, help=flags.VERBOSE_HELP
    ),
    inventory: Optional[str] = typer.Option(
        None, "--inventory", "-i", help=flags.INVENTORY_HELP
    ),
) -> None:
    """Execute a playbook against the agent inventory."""
    try:
        _validate_not_empty(playbook, "playbook path")

        inv_path = inventory or default_inventory_path()
        inv = load_inventory(inv_path)
        proj_config = load_project_config()

        pb_path = Path(playbook)

        if syntax_check_flag:
            errors = syntax_check(pb_path)
            if errors:
                for err in errors:
                    console.print(f"[red]SYNTAX ERROR:[/red] {err}")
                raise typer.Exit(code=1)
            console.print("[green]Syntax check passed.[/green]")
            raise typer.Exit()

        pb = parse_playbook(pb_path)

        if list_tasks:
            _list_tasks(pb)
            raise typer.Exit()

        if list_tags:
            _list_tags(pb)
            raise typer.Exit()

        if check:
            console.print("[yellow]CHECK MODE:[/yellow] playbook parsed, "
                          "no agents will be executed.")
            _print_check_plan(pb, diff)
            raise typer.Exit()

        console.print(f"[green]Running playbook:[/green] {pb_path}")
        console.print(f"[dim]Inventory: {inv_path}[/dim]")
        if verbose > 0:
            console.print(f"[dim]Verbosity level: {verbose}[/dim]")

        extra_vars_dict = _parse_extra_vars(extra_vars) if extra_vars else {}

        executor = PlaybookExecutor(
            playbook=pb,
            inventory=inv,
            verbose=verbose > 0,
            check_mode=check,
            tags=tags,
            skip_tags=skip_tags,
            limit=limit,
            extra_vars=extra_vars_dict,
            playbook_path=str(pb_path),
            inventory_path=str(inv_path),
        )

        results = executor.run()

        _print_results(results)

        if results.get("failed"):
            raise typer.Exit(code=1)

    except CrewAIBookError as exc:
        console.print(f"[red]ERROR:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def init(
    path: str = typer.Argument(
        ".", help="Directory to scaffold the project into."
    ),
) -> None:
    """Scaffold a new crewai-playbook project with the standard directory layout."""
    from crewai_playbook.resources import scaffold
    dest = Path(path)
    scaffold.create_project(dest)
    console.print(f"[green]Project scaffolded at:[/green] {dest.resolve()}")


@app.command()
def lint(
    playbook: str = typer.Argument(
        ..., help="Path to the playbook YAML file."
    ),
    inventory: Optional[str] = typer.Option(
        None, "--inventory", "-i", help=flags.INVENTORY_HELP
    ),
) -> None:
    """Lint a playbook for common issues."""
    try:
        _validate_not_empty(playbook, "playbook path")
        inv_path = inventory or default_inventory_path()
        inv = load_inventory(inv_path)
        pb = parse_playbook(playbook)
        errors: list[str] = []

        for play_idx, play in enumerate(pb.plays):
            if not play.name.strip():
                errors.append(
                    f"play #{play_idx + 1}: 'name' must not be empty"
                )
            if not play.agents:
                errors.append(
                    f"play #{play_idx + 1}: 'agents' must not be empty"
                )
            for agent_name in play.agents:
                raw_name = agent_name.lstrip("@")
                if agent_name.startswith("@"):
                    from crewai_playbook.core.inventory import resolve_agents
                    resolved = resolve_agents([agent_name], inv)
                    if not resolved:
                        errors.append(
                            f"play #{play_idx + 1}: group '{agent_name}' "
                            f"resolves to zero agents"
                        )
                elif agent_name not in inv:
                    errors.append(
                        f"play #{play_idx + 1}: agent '{agent_name}' "
                        f"not found in inventory"
                    )
            if play.roles:
                seen_roles: set[str] = set()
                for role_ref in play.roles:
                    if role_ref.role in seen_roles:
                        errors.append(
                            f"play #{play_idx + 1}: role '{role_ref.role}' "
                            f"referenced more than once"
                        )
                    seen_roles.add(role_ref.role)

        if errors:
            for err in errors:
                console.print(f"[red]LINT:[/red] {err}")
            raise typer.Exit(code=1)
        console.print("[green]Lint passed: no issues found.[/green]")
    except CrewAIBookError as exc:
        console.print(f"[red]ERROR:[/red] {exc}")
        raise typer.Exit(code=1)


def _validate_not_empty(val: str, label: str) -> None:
    if not val or not val.strip():
        raise ParseError(f"{label} must not be empty")


def _list_tasks(pb) -> None:
    for play_idx, play in enumerate(pb.plays):
        console.print(f"\n[bold]play #{play_idx + 1}: {play.name}[/bold]")
        if play.tasks:
            for task_idx, task_entry in enumerate(play.tasks):
                if hasattr(task_entry, "block"):
                    console.print(f"  block #{task_idx + 1}")
                    for bt in task_entry.block:
                        console.print(f"    {bt.name}")
                    if task_entry.rescue:
                        console.print(f"    rescue:")
                        for rt in task_entry.rescue:
                            console.print(f"      {rt.name}")
                    if task_entry.always:
                        console.print(f"    always:")
                        for at in task_entry.always:
                            console.print(f"      {at.name}")
                else:
                    console.print(f"  {task_entry.name}")


def _list_tags(pb) -> None:
    all_tags: set[str] = set()
    for play in pb.plays:
        if play.tags:
            all_tags.update(play.tags)
        if play.tasks:
            for task_entry in play.tasks:
                if hasattr(task_entry, "block"):
                    if task_entry.tags:
                        all_tags.update(task_entry.tags)
                    for bt in task_entry.block:
                        if bt.tags:
                            all_tags.update(bt.tags)
                else:
                    if task_entry.tags:
                        all_tags.update(task_entry.tags)
    for tag in sorted(all_tags):
        console.print(tag)


def _parse_extra_vars(raw: List[str]) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for item in raw:
        if item.startswith("{"):
            import json
            parsed.update(json.loads(item))
        elif "=" in item:
            key, _, val = item.partition("=")
            parsed[key.strip()] = val.strip()
    return parsed


def _print_results(results: Dict[str, Any]) -> None:
    for play_result in results.get("plays", []):
        name = play_result.get("name", "unnamed")
        status = "[red]FAILED[/red]" if play_result.get("failed") else "[green]OK[/green]"
        console.print(f"  play '{name}': {status}")
        for task in play_result.get("tasks", []):
            tname = task.get("name", "?")
            if isinstance(task, dict) and task.get("type") in ("block",):
                console.print(f"    [dim]block[/dim]")
                continue
            if task.get("failed"):
                console.print(f"    [red]✗ {tname}[/red]: {task.get('error', '')}")
            else:
                output = task.get("output", "")
                preview = output[:80] + "..." if len(output) > 80 else output
                console.print(f"    [green]✓ {tname}[/green]")
                if preview:
                    console.print(f"      [dim]{preview}[/dim]")
        if play_result.get("handlers"):
            for hname, houtput in play_result["handlers"].items():
                console.print(f"    [blue]handler {hname}[/blue]")


def _print_check_plan(pb, diff: bool) -> None:
    for play_idx, play in enumerate(pb.plays):
        console.print(f"\n[bold]play #{play_idx + 1}: {play.name}[/bold]")
        console.print(f"  agents: {', '.join(play.agents)}")
        console.print(f"  gather_facts: {play.gather_facts}")
        if play.tasks:
            for task_entry in play.tasks:
                if hasattr(task_entry, "block"):
                    console.print(f"  block:")
                    for bt in task_entry.block:
                        console.print(f"    [yellow]task:[/yellow] {bt.name}")
                        if bt.dest and diff:
                            console.print(f"      [dim]dest: {bt.dest}[/dim]")
                    if task_entry.rescue:
                        console.print(f"    rescue:")
                        for rt in task_entry.rescue:
                            console.print(f"      [yellow]task:[/yellow] {rt.name}")
                    if task_entry.always:
                        console.print(f"    always:")
                        for at in task_entry.always:
                            console.print(f"      [yellow]task:[/yellow] {at.name}")
                else:
                    console.print(f"  [yellow]task:[/yellow] {task_entry.name}")
                    if task_entry.dest and diff:
                        console.print(f"    [dim]dest: {task_entry.dest}[/dim]")

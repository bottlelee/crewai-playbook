from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Dict, List

import yaml

from crewai_playbook.models.agent import AgentDefinition, AgentInventory
from crewai_playbook.utils.errors import InventoryError


def load_inventory(path: str | Path) -> Dict[str, AgentDefinition]:
    """Load agent definitions from a YAML inventory file.

    Expected format (``config/agents.yaml``):

    .. code-block:: yaml

        agents:
          researcher:
            role: "Research Specialist"
            goal: "Find relevant information"
            backstory: "Expert researcher"
            groups: ["developers", "qa"]
          coder:
            role: "Software Engineer"
            goal: "Write clean code"
            backstory: "Senior developer"
            groups: ["developers"]
    """
    p = Path(path)
    if not p.exists():
        raise InventoryError(f"inventory file not found: {p}")

    with open(p) as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict) or "agents" not in raw:
        raise InventoryError(f"inventory file must contain an 'agents' mapping")

    try:
        inventory = AgentInventory(**raw)
    except Exception as exc:
        raise InventoryError(f"invalid agent definition in {p}: {exc}") from exc

    return inventory.agents


def resolve_agents(
    names: List[str], inventory: Dict[str, AgentDefinition]
) -> Dict[str, AgentDefinition]:
    """Resolve a list of agent names into a flat dict of agent definitions.

    Supported entry formats:

    *   Exact name: ``tang_sanzang``
    *   Group reference: ``@wukong`` (all agents in the ``wukong`` group)
    *   Glob pattern: ``wukong_*``, ``*_backend``, ``?`` (Unix-style wildcards)

    Glob patterns use Python's ``fnmatch`` module:

    *   ``*`` matches everything
    *   ``?`` matches any single character
    *   ``[seq]`` matches any character in *seq*
    *   ``[!seq]`` matches any character not in *seq*
    """
    resolved: Dict[str, AgentDefinition] = {}
    for entry in names:
        if entry.startswith("@"):
            group = entry[1:]
            found = False
            for name, defn in inventory.items():
                if defn.groups and group in defn.groups:
                    resolved[name] = defn
                    found = True
            if not found:
                raise InventoryError(f"no agents found in group '@{group}'")
        elif any(c in entry for c in "*?["):
            matched = False
            for name, defn in inventory.items():
                if fnmatch.fnmatch(name, entry):
                    resolved[name] = defn
                    matched = True
            if not matched:
                raise InventoryError(
                    f"no agents matched pattern '{entry}'"
                )
        else:
            if entry not in inventory:
                raise InventoryError(
                    f"agent '{entry}' not found in inventory"
                )
            resolved[entry] = inventory[entry]
    return resolved

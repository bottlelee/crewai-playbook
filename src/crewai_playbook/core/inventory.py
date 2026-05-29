from __future__ import annotations

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
    """Resolve a list of agent names (which may include ``@group`` entries)
    into a flat dict of agent definitions."""
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
        else:
            if entry not in inventory:
                raise InventoryError(
                    f"agent '{entry}' not found in inventory"
                )
            resolved[entry] = inventory[entry]
    return resolved

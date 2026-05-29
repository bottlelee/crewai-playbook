from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from crewai_playbook.utils.errors import ConfigError

DEFAULT_PROJECT_CONFIG = "crewai-playbook.yml"


def load_project_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the project-level ``crewai-playbook.yml`` configuration.

    Searches in order:
    1. Explicit ``path`` argument
    2. ``CREWAI_PLAYBOOK_CONFIG`` environment variable
    3. ``crewai-playbook.yml`` in the current working directory
    """
    search_paths: list[Path] = []
    if path:
        search_paths.append(Path(path))
    env = os.environ.get("CREWAI_PLAYBOOK_CONFIG")
    if env:
        search_paths.append(Path(env))
    search_paths.append(Path.cwd() / DEFAULT_PROJECT_CONFIG)

    for p in search_paths:
        if p.exists():
            with open(p) as f:
                raw = yaml.safe_load(f)
                if not isinstance(raw, dict):
                    raise ConfigError(f"{p} must be a YAML mapping")
                return raw
    return {}


def default_inventory_path() -> str:
    """Return the default path to the agent inventory file."""
    return os.environ.get("CREWAI_PLAYBOOK_INVENTORY", "config/agents.yaml")

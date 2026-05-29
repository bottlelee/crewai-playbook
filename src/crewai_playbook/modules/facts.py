from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict, List


def gather_facts() -> Dict[str, Any]:
    """Gather environment facts about the control node.

    Returns a dict that is injected as ``{{ facts }}`` into playbooks.
    Mirrors Ansible's ``gather_facts`` module.
    """
    facts: Dict[str, Any] = {}

    facts["os"] = {
        "name": os.name,
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
    }

    facts["python"] = {
        "version": sys.version,
        "executable": sys.executable,
        "implementation": platform.python_implementation(),
    }

    facts["cwd"] = os.getcwd()

    facts["environment"] = {
        "home": os.environ.get("HOME", ""),
        "user": os.environ.get("USER", ""),
        "path": os.environ.get("PATH", ""),
    }

    facts["tools"] = _detect_tools()

    return facts


def _detect_tools() -> Dict[str, bool]:
    """Detect available CLI tools on the system."""
    tools = [
        "git", "make", "gcc", "g++", "python3", "node", "npm",
        "docker", "kubectl", "aws", "gcloud", "curl", "wget",
        "jq", "yq", "rg", "fd", "fzf", "tmux", "vim", "nvim",
    ]
    result: Dict[str, bool] = {}
    for tool in tools:
        result[tool] = shutil.which(tool) is not None
    return result

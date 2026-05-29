from __future__ import annotations

from pathlib import Path

from crewai_playbook.utils.errors import CrewAIBookError

_DIRS = (
    "config",
    "playbooks",
    "roles",
    "group_vars",
    "inventory",
)

_FILES: dict[str, str] = {}


def create_project(dest: Path) -> None:
    """Create the standard crewai-playbook project scaffold at *dest*."""
    if dest.exists() and any(dest.iterdir()):
        raise CrewAIBookError(
            f"target directory '{dest}' exists and is not empty"
        )
    dest.mkdir(parents=True, exist_ok=True)
    for d in _DIRS:
        (dest / d).mkdir(parents=True, exist_ok=True)

    agents_yaml = dest / "config" / "agents.yaml"
    if not agents_yaml.exists():
        agents_yaml.write_text(_AGENTS_YAML)

    example_playbook = dest / "playbooks" / "example.yml"
    if not example_playbook.exists():
        example_playbook.write_text(_EXAMPLE_PLAYBOOK)

    gitignore = dest / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(_GITIGNORE)

    crewai_config = dest / "crewai-playbook.yml"
    if not crewai_config.exists():
        crewai_config.write_text(_CREWAI_CONFIG)


_AGENTS_YAML = """\
agents:
  manager:
    role: "Project Manager"
    goal: "Coordinate agents, assign tasks, and synthesize results"
    backstory: "Experienced team lead who orchestrates multi-agent workflows."
    tools: []
    allow_delegation: true
    verbose: true
    leader: true
    groups: ["default"]
    llm: "ollama/gemma4:latest"

  researcher:
    role: "Research Specialist"
    goal: "Find and synthesize relevant information on given topics"
    backstory: "You are an expert researcher with deep knowledge of information gathering and synthesis."
    tools: []
    allow_delegation: false
    verbose: true
    groups: ["default"]
    llm: "ollama/gemma4:latest"

  writer:
    role: "Content Writer"
    goal: "Transform research into well-structured, clear content"
    backstory: "You are a skilled writer who produces clear, engaging content from research material."
    tools: []
    allow_delegation: false
    verbose: true
    groups: ["default"]
    llm: "ollama/gemma4:latest"
"""

_EXAMPLE_PLAYBOOK = """\
- name: "Research and Write"
  agents:
    - researcher
    - writer
  gather_facts: true
  process: sequential
  tasks:
    - name: "Conduct research"
      agents:
        - researcher
      task: "Research the topic: {{ topic | default('artificial intelligence trends') }}"
      register: research_output

    - name: "Write content"
      agents:
        - writer
      task: "Based on the research, write a concise summary"
      when: research_output is defined
"""

_GITIGNORE = """\
__pycache__/
*.pyc
.env
*.egg-info/
dist/
"""

_CREWAI_CONFIG = """\
# crewai-playbook project configuration
inventory: config/agents.yaml
default_verbosity: 0
"""

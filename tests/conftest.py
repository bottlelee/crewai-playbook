from pathlib import Path
from typing import Dict

import pytest
import yaml

from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.models.playbook import Playbook

FIXTURES = Path(__file__).parent / "fixtures"
ROLES_PATH = FIXTURES / "roles"


@pytest.fixture
def sample_inventory() -> Dict[str, AgentDefinition]:
    return {
        "researcher": AgentDefinition(
            role="Research Specialist",
            goal="Find relevant information",
            backstory="Expert researcher",
            groups=["default", "research"],
        ),
        "writer": AgentDefinition(
            role="Content Writer",
            goal="Write clear content",
            backstory="Professional writer",
            groups=["default", "writing"],
        ),
        "reviewer": AgentDefinition(
            role="Quality Reviewer",
            goal="Review content",
            backstory="Senior editor",
            groups=["default", "qa"],
        ),
    }


@pytest.fixture
def simple_playbook_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "simple.yml"
    data = [
        {
            "name": "Test Play",
            "agents": ["researcher"],
            "gather_facts": False,
            "tasks": [
                {
                    "name": "Research task",
                    "agents": ["researcher"],
                    "task": "Find information about AI",
                }
            ],
        }
    ]
    p.write_text(yaml.safe_dump(data))
    return p


@pytest.fixture
def block_playbook_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "block.yml"
    data = [
        {
            "name": "Block Test Play",
            "agents": ["researcher"],
            "gather_facts": False,
            "tasks": [
                {
                    "block": [
                        {
                            "name": "Main task",
                            "agents": ["researcher"],
                            "task": "Do main work",
                        }
                    ],
                    "rescue": [
                        {
                            "name": "Fallback",
                            "agents": ["writer"],
                            "task": "Handle failure",
                        }
                    ],
                    "always": [
                        {
                            "name": "Cleanup",
                            "agents": ["reviewer"],
                            "task": "Always run cleanup",
                        }
                    ],
                }
            ],
        }
    ]
    p.write_text(yaml.safe_dump(data))
    return p


@pytest.fixture
def role_playbook_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "roles_playbook.yml"
    data = [
        {
            "name": "Role Test Play",
            "agents": ["researcher"],
            "roles": [
                {"role": "research", "vars": {"topic": "AI"}},
                "write",
            ],
        }
    ]
    p.write_text(yaml.safe_dump(data))
    return p


@pytest.fixture
def handler_playbook_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "handlers.yml"
    data = [
        {
            "name": "Handler Test Play",
            "agents": ["researcher"],
            "tasks": [
                {
                    "name": "Generate report",
                    "agents": ["researcher"],
                    "task": "Write a research report",
                    "notify": ["Summarize"],
                }
            ],
            "handlers": [
                {
                    "name": "Summarize",
                    "tasks": [
                        {
                            "name": "Create summary",
                            "agents": ["writer"],
                            "task": "Summarize the report",
                        }
                    ],
                }
            ],
        }
    ]
    p.write_text(yaml.safe_dump(data))
    return p


@pytest.fixture
def inventory_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "agents.yaml"
    data = {
        "agents": {
            "researcher": {
                "role": "Research Specialist",
                "goal": "Find relevant information",
                "backstory": "Expert researcher",
                "groups": ["default"],
            },
            "writer": {
                "role": "Content Writer",
                "goal": "Write clear content",
                "backstory": "Professional writer",
                "groups": ["default"],
            },
        }
    }
    p.write_text(yaml.safe_dump(data))
    return p


@pytest.fixture
def tagged_playbook_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "tagged.yml"
    data = [
        {
            "name": "Tagged Play",
            "agents": ["researcher"],
            "tasks": [
                {
                    "name": "Research phase",
                    "agents": ["researcher"],
                    "task": "Do research",
                    "tags": ["research"],
                },
                {
                    "name": "Coding phase",
                    "agents": ["writer"],
                    "task": "Write code",
                    "tags": ["coding"],
                },
                {
                    "name": "Summary",
                    "agents": ["reviewer"],
                    "task": "Summarize",
                    "tags": ["summary"],
                },
            ],
        }
    ]
    p.write_text(yaml.safe_dump(data))
    return p

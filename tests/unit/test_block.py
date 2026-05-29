from unittest.mock import patch

import pytest

from crewai_playbook.models.playbook import Block, Task
from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.modules.block import execute_block


@pytest.fixture
def inventory():
    return {
        "researcher": AgentDefinition(
            role="Research Specialist", goal="Find info", backstory="Expert",
        ),
        "writer": AgentDefinition(
            role="Writer", goal="Write content", backstory="Pro",
        ),
        "reviewer": AgentDefinition(
            role="Reviewer", goal="Review", backstory="Editor",
        ),
    }


class TestExecuteBlock:
    def test_block_tasks_execute(self, inventory):
        block = Block(
            block=[
                Task(name="Main", agents=["researcher"], task="Main work"),
            ],
        )
        with patch("crewai_playbook.modules.block.execute_task") as mock:
            mock.return_value = "main output"
            outputs = execute_block(block, inventory, {})
            assert outputs == ["main output"]

    def test_rescue_runs_on_failure(self, inventory):
        block = Block(
            block=[
                Task(name="Main", agents=["researcher"], task="Main work"),
            ],
            rescue=[
                Task(name="Fallback", agents=["writer"], task="Recover"),
            ],
        )
        with patch("crewai_playbook.modules.block.execute_task") as mock:
            mock.side_effect = [Exception("fail"), "rescue output"]
            outputs = execute_block(block, inventory, {})
            assert "rescue output" in outputs

    def test_always_runs_regardless(self, inventory):
        block = Block(
            block=[
                Task(name="Main", agents=["researcher"], task="Main work"),
            ],
            always=[
                Task(name="Cleanup", agents=["reviewer"], task="Clean up"),
            ],
        )
        with patch("crewai_playbook.modules.block.execute_task") as mock:
            mock.return_value = "output"
            outputs = execute_block(block, inventory, {})
            assert len(outputs) == 2

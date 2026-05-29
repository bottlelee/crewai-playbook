from unittest.mock import patch

import pytest

from crewai_playbook.models.playbook import Handler, Task
from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.modules.handler import HandlerManager


@pytest.fixture
def inventory():
    return {
        "writer": AgentDefinition(
            role="Writer", goal="Write content", backstory="Pro",
        ),
    }


class TestHandlerManager:
    def test_notify_triggers_handler(self, inventory):
        handlers = [
            Handler(
                name="Summarize",
                tasks=[
                    Task(name="Summary", agents=["writer"], task="Summarize")
                ],
            )
        ]
        mgr = HandlerManager(handlers)
        mgr.notify("Summarize")
        with patch("crewai_playbook.modules.handler.execute_task") as mock:
            mock.return_value = "summary output"
            outputs = mgr.execute(inventory, {})
            assert "Summarize/Summary" in outputs

    def test_no_notify_no_execution(self, inventory):
        handlers = [
            Handler(
                name="Summarize",
                tasks=[
                    Task(name="Summary", agents=["writer"], task="Summarize")
                ],
            )
        ]
        mgr = HandlerManager(handlers)
        with patch("crewai_playbook.modules.handler.execute_task") as mock:
            outputs = mgr.execute(inventory, {})
            assert outputs == {}
            mock.assert_not_called()

    def test_process_notifications_only_with_output(self, inventory):
        handlers = [
            Handler(
                name="Summarize",
                tasks=[
                    Task(name="Summary", agents=["writer"], task="Summarize")
                ],
            )
        ]
        mgr = HandlerManager(handlers)
        task = Task(
            name="Research",
            agents=["writer"],
            task="Do research",
            notify=["Summarize"],
        )
        mgr.process_notifications(task, "")
        assert "Summarize" not in mgr._notified

        mgr.process_notifications(task, "some output")
        assert "Summarize" in mgr._notified

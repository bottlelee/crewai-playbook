from __future__ import annotations

from typing import Any, Dict, List, Set

from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.models.playbook import Handler, Task
from crewai_playbook.modules.task import execute_task


class HandlerManager:
    """Manages handler notifications and deferred execution.

    Mirrors Ansible's handler pattern: tasks ``notify`` handlers, and
    handlers execute once at the end of a play.
    """

    def __init__(self, handlers: List[Handler]) -> None:
        self._handlers = {h.name: h for h in handlers}
        self._notified: Set[str] = set()

    def notify(self, handler_name: str) -> None:
        if handler_name in self._handlers:
            self._notified.add(handler_name)

    def process_notifications(self, task: Task, output: str) -> None:
        """Process ``notify`` from a completed task.

        Only notifies if the task produced output (non-empty).
        """
        if not output:
            return
        if task.notify:
            for name in task.notify:
                self.notify(name)

    def execute(
        self,
        inventory: Dict[str, AgentDefinition],
        variable_context: Dict[str, Any],
        verbose: bool = False,
    ) -> Dict[str, str]:
        """Execute all notified handlers and return their outputs."""
        outputs: Dict[str, str] = {}
        for name in sorted(self._notified):
            handler = self._handlers[name]
            for task in handler.tasks:
                output = execute_task(task, inventory, variable_context, verbose)
                outputs[f"{name}/{task.name}"] = output
        return outputs

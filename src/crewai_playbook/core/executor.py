from __future__ import annotations

from typing import Any, Dict, List, Optional

from crewai_playbook.core.inventory import resolve_agents
from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.models.playbook import Block, Play, Playbook, Task
from crewai_playbook.modules.block import execute_block
from crewai_playbook.modules.facts import gather_facts
from crewai_playbook.modules.handler import HandlerManager
from crewai_playbook.modules.task import execute_task
from crewai_playbook.core.runner import run_crew_for_play
from crewai_playbook.modules.role import resolve_role_tasks
from crewai_playbook.utils.errors import ExecutionError
from crewai_playbook.utils.vars import resolve_vars as resolve_vars_fn


class PlaybookExecutor:
    """Orchestrate playbook execution.

    Iterates through plays, resolves agents, gathers facts, executes
    tasks/blocks, and fires handlers.
    """

    def __init__(
        self,
        playbook: Playbook,
        inventory: Dict[str, AgentDefinition],
        verbose: bool = False,
        check_mode: bool = False,
        tags: Optional[List[str]] = None,
        skip_tags: Optional[List[str]] = None,
        limit: Optional[List[str]] = None,
        extra_vars: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.playbook = playbook
        self.inventory = inventory
        self.verbose = verbose
        self.check_mode = check_mode
        self.tags = tags
        self.skip_tags = skip_tags
        self.limit = limit
        self.extra_vars = extra_vars or {}

    def run(self) -> Dict[str, Any]:
        """Execute the full playbook and return results."""
        results: Dict[str, Any] = {
            "plays": [],
            "failed": False,
        }

        for play in self.playbook.plays:
            play_result = self._execute_play(play)
            results["plays"].append(play_result)
            if play_result.get("failed"):
                results["failed"] = True
                break

        return results

    @staticmethod
    def _find_leader(agents: Dict[str, AgentDefinition]) -> Optional[str]:
        for name, defn in agents.items():
            if defn.leader:
                return name
        return None

    def _execute_play(self, play: Play) -> Dict[str, Any]:
        """Execute a single play."""
        play_result: Dict[str, Any] = {
            "name": play.name,
            "agents": play.agents,
            "tasks": [],
            "handlers": {},
            "failed": False,
        }

        resolved = resolve_agents(play.agents, self.inventory)

        if self.limit:
            filtered = {}
            for lim in self.limit:
                if lim.startswith("@"):
                    from crewai_playbook.core.inventory import resolve_agents as ra
                    limited = ra([lim], self.inventory)
                    filtered.update(limited)
                elif lim in resolved:
                    filtered[lim] = resolved[lim]
            resolved = filtered

        leader_name = self._find_leader(resolved)

        variable_context: Dict[str, Any] = {}
        variable_context["play_name"] = play.name
        variable_context["play_agents"] = play.agents

        if play.vars:
            variable_context.update(play.vars)

        variable_context.update(self.extra_vars)

        if play.gather_facts:
            facts = gather_facts()
            variable_context["facts"] = facts

        if self.check_mode:
            play_result["tasks"] = self._describe_tasks(
                play, variable_context, roles=play.roles
            )
            return play_result

        all_tasks = []
        if play.roles:
            resolved_role_tasks = resolve_role_tasks(play.roles)
            for role_task, role_vars in resolved_role_tasks:
                with_role_vars = {**variable_context, **role_vars}
                all_tasks.append((role_task, with_role_vars))
        if play.tasks:
            for task_entry in play.tasks:
                all_tasks.append((task_entry, variable_context))

        handler_mgr: Optional[HandlerManager] = None
        if play.handlers:
            handler_mgr = HandlerManager(play.handlers)

        use_hierarchical = leader_name and play.process == "hierarchical"
        use_hierarchical = use_hierarchical and not any(
            isinstance(t, Block) for t, _ in all_tasks
        )

        if use_hierarchical and all_tasks:
            self._execute_play_hierarchical(
                play, all_tasks, resolved, leader_name, variable_context,
                play_result, handler_mgr,
            )
        elif all_tasks:
            for task_entry, task_vars in all_tasks:
                if self._should_skip_by_tags(task_entry):
                    continue

                variable_context.update(task_vars)

                if isinstance(task_entry, Block):
                    task_result = self._execute_block(
                        task_entry, resolved, variable_context, handler_mgr
                    )
                else:
                    task_result = self._execute_single_task(
                        task_entry, resolved, variable_context, handler_mgr
                    )
                play_result["tasks"].append(task_result)
                if task_result.get("failed"):
                    play_result["failed"] = True
                    break

        if handler_mgr:
            handler_outputs = handler_mgr.execute(
                resolved, variable_context, self.verbose
            )
            play_result["handlers"] = handler_outputs

        return play_result

    def _execute_single_task(
        self,
        task: Task,
        resolved: Dict[str, AgentDefinition],
        variable_context: Dict[str, Any],
        handler_mgr: Optional[HandlerManager],
    ) -> Dict[str, Any]:
        task_result: Dict[str, Any] = {
            "name": task.name,
            "agents": task.agents,
            "output": "",
            "failed": False,
        }
        try:
            output = execute_task(
                task, resolved, variable_context, self.verbose
            )
            task_result["output"] = output
            variable_context[task.name] = output
            if handler_mgr:
                handler_mgr.process_notifications(task, output)
        except Exception as exc:
            task_result["failed"] = True
            task_result["error"] = str(exc)
        return task_result

    def _execute_block(
        self,
        block: Block,
        resolved: Dict[str, AgentDefinition],
        variable_context: Dict[str, Any],
        handler_mgr: Optional[HandlerManager],
    ) -> Dict[str, Any]:
        block_result: Dict[str, Any] = {
            "type": "block",
            "block": [],
            "rescue": [],
            "always": [],
            "failed": False,
        }
        try:
            for i, task in enumerate(block.block):
                task_result = self._execute_single_task(
                    task, resolved, variable_context, handler_mgr
                )
                block_result["block"].append(task_result)
                if task_result.get("failed"):
                    break
        except Exception:
            if block.rescue:
                for task in block.rescue:
                    task_result = self._execute_single_task(
                        task, resolved, variable_context, handler_mgr
                    )
                    block_result["rescue"].append(task_result)
            block_result["failed"] = True
        finally:
            if block.always:
                for task in block.always:
                    task_result = self._execute_single_task(
                        task, resolved, variable_context, handler_mgr
                    )
                    block_result["always"].append(task_result)
        return block_result

    def _execute_play_hierarchical(
        self,
        play: Play,
        all_tasks: list,
        resolved: Dict[str, AgentDefinition],
        leader_name: Optional[str],
        variable_context: Dict[str, Any],
        play_result: Dict[str, Any],
        handler_mgr: Optional[HandlerManager],
    ) -> None:
        tasks_data = []
        for task_entry, task_vars in all_tasks:
            if self._should_skip_by_tags(task_entry):
                continue
            if isinstance(task_entry, Task):
                variable_context.update(task_vars)
                resolved_desc = resolve_vars_fn(task_entry.task, variable_context)
                tasks_data.append({
                    "name": task_entry.name,
                    "agent_names": task_entry.agents,
                    "description": resolved_desc,
                })

        if not tasks_data:
            return

        try:
            results = run_crew_for_play(
                tasks_data=tasks_data,
                agent_definitions=resolved,
                verbose=self.verbose,
                leader_name=leader_name,
                process="hierarchical",
            )
            for td in tasks_data:
                output = results.get(td["name"], "")
                task_result = {
                    "name": td["name"],
                    "agents": td["agent_names"],
                    "output": output,
                    "failed": False,
                }
                variable_context[td["name"]] = output
                play_result["tasks"].append(task_result)
        except Exception as exc:
            play_result["failed"] = True
            play_result["tasks"].append({
                "name": "hierarchical_execution",
                "error": str(exc),
                "failed": True,
            })

    def _should_skip_by_tags(
        self, task_entry: Task | Block
    ) -> bool:
        if not self.tags and not self.skip_tags:
            return False

        entry_tags = set()
        if isinstance(task_entry, Task):
            if task_entry.tags:
                entry_tags = set(task_entry.tags)
        elif isinstance(task_entry, Block):
            if task_entry.tags:
                entry_tags = set(task_entry.tags)

        if self.tags:
            if not entry_tags:
                return True
            if not entry_tags.intersection(self.tags):
                return True

        if self.skip_tags:
            if entry_tags.intersection(self.skip_tags):
                return True

        return False

    def _describe_tasks(
        self, play: Play, variable_context: Dict[str, Any],
        roles: Optional[List] = None,
    ) -> List[Dict[str, Any]]:
        descriptions: List[Dict[str, Any]] = []
        if roles:
            resolved = resolve_role_tasks(roles)
            for role_task, role_vars in resolved:
                descriptions.append({
                    "type": "role_task",
                    "name": role_task.name,
                    "agents": role_task.agents,
                    "action": role_task.task,
                    "role_vars": role_vars,
                })
        if play.tasks:
            for task_entry in play.tasks:
                if isinstance(task_entry, Block):
                    descriptions.append({
                        "type": "block",
                        "block": [
                            {"name": t.name, "agents": t.agents, "action": t.task}
                            for t in task_entry.block
                        ],
                        "rescue": [
                            {"name": t.name, "agents": t.agents}
                            for t in (task_entry.rescue or [])
                        ],
                        "always": [
                            {"name": t.name, "agents": t.agents}
                            for t in (task_entry.always or [])
                        ],
                    })
                else:
                    descriptions.append({
                        "name": task_entry.name,
                        "agents": task_entry.agents,
                        "action": task_entry.task,
                    })
        return descriptions

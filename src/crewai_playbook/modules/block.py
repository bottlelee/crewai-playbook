from __future__ import annotations

from typing import Any, Dict, List, Optional

from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.models.playbook import Block as BlockModel, Task
from crewai_playbook.modules.task import execute_task
from crewai_playbook.utils.errors import ExecutionError


def execute_block(
    block: BlockModel,
    inventory: Dict[str, AgentDefinition],
    variable_context: Dict[str, Any],
    verbose: bool = False,
) -> List[str]:
    """Execute a block/rescue/always task group.

    Returns a list of output strings from executed tasks.
    """
    outputs: List[str] = []
    try:
        for task in block.block:
            output = execute_task(task, inventory, variable_context, verbose)
            outputs.append(output)
    except Exception:
        if block.rescue:
            for task in block.rescue:
                output = execute_task(task, inventory, variable_context, verbose)
                outputs.append(output)
    finally:
        if block.always:
            for task in block.always:
                output = execute_task(task, inventory, variable_context, verbose)
                outputs.append(output)

    return outputs

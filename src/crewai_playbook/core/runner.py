from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

# Allow OpenTelemetry tracer provider to be overridden (crewAI's Telemetry
# sets a global provider that conflicts with subsequent runs).
os.environ.setdefault("OTEL_PYTHON_TRACER_PROVIDER", "override")

from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.modules.tools import resolve_tools
from crewai_playbook.utils.errors import ExecutionError


OLLAMA_BASE_URL = os.environ.get(
    "OLLAMA_BASE_URL", "http://localhost:11434/v1"
)


def _resolve_llm(llm_spec: str) -> Any:
    """Resolve an LLM string spec to a LangChain chat model instance.

    Supported formats:

    * ``"ollama/<model>"`` — uses Ollama's OpenAI-compatible endpoint.
    * ``"gpt-4"`` / ``"gpt-4o"`` — passed to crewAI as-is (it creates an
      internal ChatOpenAI).
    """
    if llm_spec.startswith("ollama/"):
        model = llm_spec[len("ollama/"):]
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            from langchain_community.chat_models import ChatOpenAI
        return ChatOpenAI(
            model=model,
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",
        )
    return llm_spec


def create_crew_agent(
    name: str, definition: AgentDefinition
) -> Any:
    """Create a single crewAI Agent from an inventory definition."""
    try:
        from crewai import Agent as CrewAgent
    except ImportError as exc:
        raise ExecutionError(
            "crewai is not installed. Run: pip install crewai"
        ) from exc

    allow_delegation = definition.allow_delegation or definition.leader
    kwargs: Dict[str, Any] = {
        "role": definition.role,
        "goal": definition.goal,
        "backstory": definition.backstory,
        "allow_delegation": allow_delegation,
        "verbose": definition.verbose,
    }
    if definition.llm:
        kwargs["llm"] = _resolve_llm(definition.llm)
    if definition.tools:
        resolved = resolve_tools(definition.tools)
        if resolved:
            kwargs["tools"] = resolved
    return CrewAgent(**kwargs)


def run_single_task(
    task_description: str,
    agent_names: List[str],
    inventory: Dict[str, AgentDefinition],
    context: Optional[str] = None,
    verbose: bool = False,
) -> str:
    """Execute a single task description through crewAI.

    Creates a temporary crew with the specified agents and runs the task.
    Returns the task output as a string.
    """
    try:
        from crewai import Task as CrewTask, Crew, Process
    except ImportError as exc:
        raise ExecutionError(
            "crewai is not installed. Run: pip install crewai"
        ) from exc

    crew_agents = [
        create_crew_agent(name, inventory[name])
        for name in agent_names
        if name in inventory
    ]

    if not crew_agents:
        raise ExecutionError(
            f"no valid agents found for task (requested: {agent_names})"
        )

    crew_task = CrewTask(
        description=task_description,
        agent=crew_agents[0],
        expected_output="A detailed response addressing the task requirements",
    )

    crew = Crew(
        agents=crew_agents,
        tasks=[crew_task],
        process=Process.sequential,
        verbose=verbose,
    )

    result = crew.kickoff()
    return str(result)


def run_hierarchical_task(
    task_description: str,
    agent_names: List[str],
    agent_definitions: Dict[str, AgentDefinition],
    leader_name: str,
    verbose: bool = False,
) -> str:
    """Execute a single task in hierarchical mode.

    Creates a crew with the leader (manager) and the task-specific agents.
    The manager delegates the task to the appropriate agent.
    Returns the task output as a string.
    """
    try:
        from crewai import Task as CrewTask, Crew, Process
    except ImportError as exc:
        raise ExecutionError(
            "crewai is not installed. Run: pip install crewai"
        ) from exc

    all_names = [leader_name] + [n for n in agent_names if n != leader_name]
    crew_agents = [
        create_crew_agent(name, agent_definitions[name])
        for name in all_names if name in agent_definitions
    ]
    if not crew_agents:
        raise ExecutionError(
            f"no valid agents found for task (requested: {agent_names})"
        )

    task_agent = crew_agents[1] if len(crew_agents) > 1 else crew_agents[0]
    crew_task = CrewTask(
        description=task_description,
        agent=task_agent,
        expected_output="A detailed response addressing the task requirements",
    )

    leader_def = agent_definitions[leader_name]
    crew = Crew(
        agents=crew_agents,
        tasks=[crew_task],
        process=Process.hierarchical,
        manager_llm=_resolve_llm(leader_def.llm) if leader_def.llm else None,
        verbose=verbose,
    )
    return str(crew.kickoff())


def run_crew_for_play(
    tasks_data: List[Dict[str, Any]],
    agent_definitions: Dict[str, AgentDefinition],
    verbose: bool = False,
    leader_name: Optional[str] = None,
    process: str = "sequential",
) -> Dict[str, str]:
    """Execute a sequence of tasks as a crew, optionally with a leader.

    Each task dict must have at least ``description``, ``agent_names``.
    When *leader_name* is set and *process* is ``"hierarchical"``, the
    leader agent is used as the manager in hierarchical mode.

    Returns a dict mapping task names to output strings.
    """
    try:
        from crewai import Task as CrewTask, Crew, Process
    except ImportError as exc:
        raise ExecutionError(
            "crewai is not installed. Run: pip install crewai"
        ) from exc

    all_agent_names: set[str] = set()
    for td in tasks_data:
        all_agent_names.update(td.get("agent_names", []))

    crew_agents_map = {
        name: create_crew_agent(name, agent_definitions[name])
        for name in all_agent_names if name in agent_definitions
    }

    crew_tasks = []
    for td in tasks_data:
        agent = crew_agents_map.get(td["agent_names"][0])
        if not agent:
            raise ExecutionError(
                f"agent '{td['agent_names'][0]}' not found for task '{td['name']}'"
            )
        crew_tasks.append(
            CrewTask(
                description=td["description"],
                agent=agent,
                expected_output=(
                    td.get("expected_output")
                    or "A detailed response addressing the task requirements"
                ),
            )
        )

    crew_kwargs: Dict[str, Any] = {
        "agents": list(crew_agents_map.values()),
        "tasks": crew_tasks,
        "verbose": verbose,
    }

    if leader_name and process == "hierarchical":
        crew_kwargs["process"] = Process.hierarchical
        if leader_name in agent_definitions:
            leader_def = agent_definitions[leader_name]
            if leader_def.llm:
                crew_kwargs["manager_llm"] = _resolve_llm(leader_def.llm)
    else:
        crew_kwargs["process"] = Process.sequential

    crew = Crew(**crew_kwargs)

    full_output = str(crew.kickoff())
    output: Dict[str, str] = {}
    for td in tasks_data:
        output[td["name"]] = full_output
    return output

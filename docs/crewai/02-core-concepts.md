# Core Concepts

> Source: https://docs.crewai.com/en/concepts/agents, https://docs.crewai.com/en/concepts/tasks, https://docs.crewai.com/en/concepts/flows, https://docs.crewai.com/en/concepts/crews

## Agents

An `Agent` is an autonomous unit that performs tasks, makes decisions, uses tools, and collaborates with other agents.

### Key Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| `role` | `str` | Agent's function and expertise |
| `goal` | `str` | Individual objective guiding decisions |
| `backstory` | `str` | Context and personality |
| `llm` | `Union[str, LLM, Any]` | Language model (default: OPENAI_MODEL_NAME or "gpt-4") |
| `tools` | `List[BaseTool]` | Capabilities available to agent |
| `max_iter` | `int` | Max iterations before best answer (default: 20) |
| `allow_delegation` | `bool` | Allow task delegation (default: False) |
| `respect_context_window` | `bool` | Auto-summarize when context exceeded (default: True) |
| `reasoning` | `bool` | Enable planning before execution (default: False) |
| `multimodal` | `bool` | Support image/visual input (default: False) |
| `memory` | `bool` | Maintain conversation history |
| `function_calling_llm` | `Optional[Any]` | Separate LLM for tool calling |

### Creation Methods
1. **YAML Configuration (recommended)** - Define in `config/agents.yaml`, use `@CrewBase` + `@agent` decorators
2. **Direct Code** - Instantiate `Agent(...)` directly

### Best Practices (80/20 Rule)
- 80% effort on task design, 20% on agent design
- Use specialists over generalists
- Be specific: "Technical Documentation Specialist" > "Writer"
- Keep backstory to 2-4 sentences
- Set `allow_delegation=False` by default; enable only when needed

## Tasks

A `Task` is a specific assignment completed by an Agent.

### Key Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| `description` | `str` | Clear statement of what to do |
| `expected_output` | `str` | Detailed description of completion criteria |
| `agent` | `Optional[BaseAgent]` | Responsible agent |
| `tools` | `List[BaseTool]` | Tool overrides for this task |
| `context` | `Optional[List[Task]]` | Tasks whose outputs are used as context |
| `output_pydantic` | `Optional[Type[BaseModel]]` | Pydantic model for structured output |
| `output_json` | `Optional[Type[BaseModel]]` | JSON schema for output |
| `guardrail` / `guardrails` | `Callable` or `List[Callable]` | Validate/transform task output |
| `async_execution` | `bool` | Execute asynchronously (default: False) |
| `human_input` | `bool` | Human review required (default: False) |
| `output_file` | `Optional[str]` | File path to save output |
| `callback` | `Optional[Any]` | Function executed after completion |

### Guardrails
Two types:
1. **Function-based**: Python function `(TaskOutput) -> Tuple[bool, Any]`
2. **LLM-based**: String description evaluated by agent's LLM

### Task Dependencies
Use `context=[other_task]` to make a task wait for others' outputs. Supports async execution.

## Flows

Flows create structured, event-driven workflows with state management.

### Decorators
- `@start()` - Entry point (can be multiple)
- `@listen(method)` - Triggered when target method completes
- `@router(method)` - Conditional routing based on return value
- `@persist` - Persist state to SQLite/PostgreSQL
- `@human_feedback` - Pause for human input

### State Management
- **Unstructured**: `self.state['key'] = value` (flexible)
- **Structured**: `Flow[MyPydanticModel]` with typed state (recommended)

### Control Flow
- `or_(method1, method2)` - Trigger when ANY completes
- `and_(method1, method2)` - Trigger when ALL complete
- `@router` with string labels for conditional branching

### State Persistence
```python
@persist  # Class-level: auto-persist all methods
class MyFlow(Flow[MyState]):
    ...

# Resume: kickoff(inputs={"id": <uuid>})
# Fork:   kickoff(restore_from_state_id=<uuid>)
```

## Processes

### Sequential (Default)
- Tasks execute in defined order
- Each task's output is context for next
- Deterministic, easy to debug
- Cheaper (no manager LLM)

### Hierarchical
- Manager agent coordinates task delegation
- Requires `manager_llm` or `manager_agent`
- Runtime branching based on intermediate results
- More expensive, higher latency
- Use only when workflow genuinely needs runtime branching

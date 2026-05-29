# Production Architecture

> Sources: https://docs.crewai.com/en/concepts/production-architecture, community guides

## Flow-First Architecture

```
┌─────────────┐
│    Start    │
└──────┬──────┘
       ▼
┌─────────────────────────────────┐
│       Flow Orchestrator         │
│  - State management (Pydantic)  │
│  - Event-driven execution       │
│  - @start / @listen / @router   │
└────────────────┬────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│       State Management          │
│  - @persist (SQLite/PostgreSQL) │
│  - Crash recovery               │
│  - Fork/resume support          │
└────────────────┬────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│     Step: Data Gathering        │
│  ┌─────────────────────────┐    │
│  │    Research Crew         │    │
│  │  - Researcher Agent      │    │
│  │  - Analyst Agent         │    │
│  │  - Tools (search, DB)    │    │
│  └─────────────────────────┘    │
└────────────────┬────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│     Condition Check             │
│  (router: success / failed)     │
└──────┬──────────────────┬───────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│  Execution   │   │     End      │
│  Crew        │   │              │
└──────┬───────┘   └──────────────┘
       │
       ▼
┌──────────────┐
│     End      │
└──────────────┘
```

## Deployment Patterns

### 1. Isolated Execution
Every run gets its own environment. Use containers (Docker/Kubernetes) for:
- No interference between runs
- Auto-scaling (scale to zero when idle)
- Version pinning per deployment

### 2. Queue-Based Architecture
For production, use a message broker:
```
API → Queue (Redis/RabbitMQ/SQS) → Workers → Result Store
```
Benefits: retry policies, dead letter queues, concurrency limits, monitoring.

### 3. Async Execution
```python
# Don't block the API
async_result = await crew.kickoff_async()

# Or for multiple items concurrently
tasks = [crew.kickoff_async(inputs={"item": item}) for item in items]
results = await asyncio.gather(*tasks)
```

### 4. Persistence for Long-Running Flows
```python
@persist
class ProductionFlow(Flow[AppState]):
    ...

# Resume from crash
flow.kickoff(inputs={"id": "previous-run-uuid"})

# Fork into new lineage
flow.kickoff(restore_from_state_id="previous-state-uuid")
```

## Control Primitives

### Task Guardrails
```python
def validate_output(result: TaskOutput) -> Tuple[bool, Any]:
    if len(result.raw) < 100:
        return (False, "Content too short")
    return (True, result.raw)
```

### Structured Outputs
```python
class ResearchResult(BaseModel):
    summary: str
    sources: List[str]
    key_findings: List[str]

task = Task(
    ...,
    output_pydantic=ResearchResult  # Type-safe data passing
)
```

### LLM Hooks
```python
@before_llm_call
def log_request(context):
    print(f"Agent {context.agent.role} is calling the LLM...")

@after_llm_call
def sanitize_response(context):
    # Filter sensitive data from LLM response
    pass
```

## Monitoring & Observability

### Metrics to Track
| Metric | What | Why |
|--------|------|-----|
| Runtime per execution | Duration | Identify slow steps |
| Cost per execution | Token usage | Budget control |
| Success/retry rate | Completion rate | Reliability |
| Output acceptance rate | Guardrail pass rate | Quality |

### Observability Integrations (15+)
- Built-in tracing (`crewai login`)
- OpenTelemetry exporters
- Datadog, Langfuse, MLflow, Weave, Arize Phoenix, etc.

## Cost Management

### Tiered Model Strategy
```python
# Cheap model for routine tasks
research_llm = LLM(model="gpt-4o-mini")

# Expensive model for critical decisions
decision_llm = LLM(model="gpt-4o")

analyst = Agent(
    role="Research Analyst",
    llm=research_llm,
    function_calling_llm="gpt-4o-mini"  # Cheaper model for tool calls
)
```

### Other Cost Controls
- Enable caching (`cache=True`)
- Set `max_rpm` for rate limiting
- Use `max_iter` limits (default 20 is too high; set to 3-5)
- Implement token budgeting

## CrewAI Enterprise (AMP)
- One-command deploy: `crewai deploy create`
- Version management: rollback with a click
- RBAC, SSO, secrets management
- Webhook streaming and triggers (Gmail, Slack, Salesforce, etc.)
- Visual agent/task builder (Crew Studio)

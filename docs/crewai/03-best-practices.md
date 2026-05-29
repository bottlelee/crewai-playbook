# Best Practices

> Sources: Official docs, community guides, production deployment experience (2026)

## Architecture

### Flow-First Mindset
Always start with a Flow, even for simple projects. Flows provide:
- State management across steps
- Precise execution paths (loops, conditionals, branching)
- Observability and debugging structure
- Persistence for crash recovery

### Use Pydantic for State
```python
# DO: Structured state with type safety
class AppState(BaseModel):
    user_input: str = ""
    research_results: str = ""

class MyFlow(Flow[AppState]):
    ...

# DON'T: Unstructured dicts
class MyFlow(Flow):
    @start()
    def begin(self):
        self.state['key'] = 'value'  # Prone to typos, hard to debug
```

### Crews as Units of Work
- Each Crew should be focused on a single goal
- Pass state explicitly from Flow to Crew inputs
- Don't over-engineer Crews; keep them simple

## Agent Design

### The 80/20 Rule
- 80% effort on **task design** (description + expected_output)
- 20% effort on **agent design** (role, goal, backstory)

### Role-Goal-Backstory Framework
- **Role**: Specific and specialized (e.g., "Technical Documentation Specialist")
- **Goal**: Clear, outcome-focused with quality standards
- **Backstory**: 2-4 sentences; delete sentences that don't change behavior

### Specialists Over Generalists
```yaml
# DON'T:
role: "Writer"

# DO:
role: "Technical Blog Writer specializing in explaining complex AI concepts"
```

### Critical Agent Settings
- `allow_delegation=False` (default); enable only for specific agents
- `max_iter=3-5` unless you have a specific reason for more
- `respect_context_window=True` for production
- Keep tool surfaces narrow per agent

## Task Design

### expected_output is the Most Important Field
The single highest-leverage thing in any CrewAI system is `expected_output`.

```yaml
# DON'T:
expected_output: "A report on AI trends"

# DO:
expected_output: >
  A comprehensive markdown report with:
  - Executive summary (5 bullet points)
  - 5-7 major trends with supporting evidence
  - For each trend: definition, examples, business implications
  - References to authoritative sources
```

### Task Design Rules
1. **Single purpose, single output** per task
2. **Be explicit** about inputs and outputs
3. **Use structured outputs** (`output_pydantic`) for passing data between tasks
4. **Use guardrails** to validate critical outputs

### Guardrails
```python
def validate_content(result: TaskOutput) -> Tuple[bool, Any]:
    if len(result.raw) < 100:
        return (False, "Content too short. Please expand.")
    return (True, result.raw)

task = Task(
    ...,
    guardrail=validate_content,
    guardrail_max_retries=3
)
```

## Production

### 5 Must-Do Items Before Production
1. **Version and freeze workflow**: Agent, task, and prompt must be traceable
2. **Set quality gates**: Validate results before writing to storage
3. **Plan cost budgets**: Define token guardrails per run
4. **Add monitoring and logs**: Know which step is slow or fails often
5. **Design fallback paths**: Handle model failure with graceful degradation

### Gradual Autonomy Pattern
- Start at 100% human review
- Track accuracy rate per output type
- Remove human review from specific branches as accuracy reaches thresholds
- Never flip from 0% to 100% autonomous overnight

### Deployment
```python
# Async execution for long-running tasks
result = await crew.kickoff_async()

# or in Flow
@listen(some_method)
async def run_async_crew(self):
    result = await some_crew.kickoff_async(inputs={...})
```

### Monitoring & Observability
- Run `crewai login` for free tracing
- Use OpenTelemetry exporters for production
- Track: runtime per execution, cost per execution, success/retry rate, output acceptance rate
- Use `step_callback` for real-time agent monitoring

## Cost Optimization
- Use cheaper models (e.g., `gpt-4o-mini`) for routine tasks
- Reserve expensive models (e.g., `gpt-4o`) for critical decisions
- Enable caching to avoid redundant API calls
- Set `max_rpm` to control rate limits
- Use `function_calling_llm` with a cheaper model for tool calls

## Process Selection
- **Start sequential**; move to hierarchical ONLY when routing genuinely varies by run
- Sequential is cheaper, more predictable, easier to debug
- Hierarchical adds latency and cost from manager LLM calls

## Security
- Keep API keys in environment variables, never hardcoded
- Filter sensitive information before external output
- Log critical operation trails for audits
- Use E2B or Modal for secure code execution (not deprecated built-in interpreter)

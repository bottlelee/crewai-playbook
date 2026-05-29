# Common Issues, Bugs & Fixes

> Sources: GitHub Issues, StackOverflow, community discussions (2026)

## 1. OpenAI API Key 401 Error Inside CrewAI

**Issue**: #5622 - API key works locally but fails inside CrewAI with `401 invalid_api_key`.

**Root Cause**: CrewAI may override `base_url` or pass extra headers. Virtual environment mismatch can also cause env var isolation.

**Fix**:
```python
from crewai import LLM
llm = LLM(model='gpt-4')
print(llm.client.base_url)    # Check endpoint
print(llm.client.api_key[:8])  # Verify key passed correctly
```

**Check**: `OPENAI_API_BASE` env var may be overriding the endpoint. Ensure your `.env` is correctly loaded.

---

## 2. `output_pydantic` Leaks Into Tool-Calling Loop

**Issue**: #5472 - Since v1.9.0, `output_pydantic` mapped to `response_model` causes non-OpenAI LLMs (vLLM, Gemini, Bedrock) to skip tool calls.

**Root Cause**: Both `tools` and `response_format` passed simultaneously in every iteration.

**Fix**: Update to a version containing the fix (PR #5821 scopes `output_pydantic` to post-processing only). Or workaround: avoid `output_pydantic` on tasks that need tools; use post-processing instead.

---

## 3. Checkpointing + Guardrail Retry Incompatible with Pydantic

**Issue**: #5544 - Flow with Pydantic state + guardrails + `output_pydantic` fails with serialization errors.

**Symptoms**:
- `PydanticSerializationError: Unable to serialize unknown type: <class 'pydantic._internal._model_construction.ModelMetaclass'>`
- Guardrail retry: `ValidationError for TaskOutput raw - Input should be a valid string`

**Fix**: PR #5557 and #5559. Use version with the fix, or manually control schema parsing:
```python
result = MyModel.model_validate_json(task.output.raw)
```

---

## 4. `crew.kickoff()` Truncates LLM Output

**Issue**: #4603 - `crew.kickoff()` truncates output (7-227 chars) while `task.execute_sync()` works correctly (2500-5700 chars).

**Root Cause**: Crew orchestration layer issue (not provider-specific; affects OpenAI and Bedrock).

**Workaround**: Use `task.execute_sync(agent=agent)` instead of `crew.kickoff()` for critical outputs. Fixed in PR #4669.

---

## 5. Flows Don't Work with `kickoff_for_each`

**Issue**: #4555 - Using `kickoff_for_each` in a Flow causes `parent_flow` validation error.

**Error**:
```
Input should be an instance of Flow.__class_getitem__.<locals>._FlowGeneric
```

**Fix**: PR #4668 and #4716 - fixed `crew.copy()` to exclude `parent_flow`. Update to version containing the fix.

---

## 6. Multimodal Input Files Ignored Without `Crew.agents`

**Issue**: #5534 - `Task.input_files` silently ignored when `agents=[]` not explicitly passed to `Crew`.

**Workaround**: Always include `agents=[agent]` in `Crew()` constructor when using `input_files`.

---

## 7. Text Files Rejected on Non-Multimodal Models

**Issue**: #5137 - Text files via `input_files` parameter are rejected with "Model does not support multimodal input" on text-only models like Claude Sonnet.

**Root Cause**: v1.10+ treats all `input_files` as multimodal, even text files.

**Workaround**: Either use multimodal-capable models, attach files directly to Task, or interpolate file content into prompt manually.

---

## 8. `result_as_answer=True` Ignores Tool Failure

**Issue**: #5156 - When `result_as_answer=True`, tool error output becomes the final answer, bypassing agent reflection.

**Fix**: Set `result_as_answer=True` only when the tool is guaranteed to succeed. For fallible tools, leave it as default.

---

## 9. ChatWithCrewFlow Blocks at Module Import

**Issue**: #5510 - `ChatWithCrewFlow.__init__` makes synchronous LLM calls during module import, crashing containers on LLM failure.

**Impact**: Deployments fail health checks if LLM is slow or down.

**Fix**: PR #3974 in CopilotKit. Defer initialization to first request. Add timeouts and fallbacks.

---

## 10. Gemini `get_llm_response()` Doesn't Pass Tools

**Issue**: #4238 - Gemini hierarchical process fails because `get_llm_response()` in `agent_utils.py` doesn't pass tools to `llm.call()`.

**Error**: `ValueError: Invalid response from LLM call - None or empty`

**Fix**: PR #4239. Update to version containing the fix.

---

## 11. Agent Not Finding Co-Worker (Delegation Loop)

**Source**: StackOverflow

**Error**: "Co-worker mentioned not found, it must be one of the following options"

**Fix**: Set `allow_delegation=False` on agents that shouldn't delegate. The issue is the researcher with `allow_delegation=True` trying to delegate to agents it can't reach.

---

## 12. `@CrewBase` Class Not Registering Agents

**Source**: StackOverflow

**Error**: `'mechanical_assistant'` key error when using `@CrewBase` decorator.

**Fix**: The class needs proper type annotations:
```python
from typing import List
from crewai.agents.agent_builder.base_agent import BaseAgent

@CrewBase
class MyCrew():
    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
```

---

## 13. Hierarchical Process: `manager_agent` Input Error

**Source**: StackOverflow

**Error**: `Input should be a valid dictionary or instance of BaseAgent`

**Fix**: The manager agent should NOT be annotated with `@agent`. Reference it directly:
```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,  # Auto-collected (excludes manager)
        tasks=self.tasks,
        process=Process.hierarchical,
        manager_agent=self.manager(),  # Call method, not @agent-decorated
    )
```
Also, the manager should not have its own task.

---

## 14. Dependency Conflicts

**Issue**: #4262 - OpenAI SDK version conflicts between crewai, litellm, and instructor.

**Fix**: Use `litellm==1.73` which resolves dependency conflicts. Or use `uv` which handles dependency resolution better than pip.

---

## Debugging Framework

From ActiveWizards' guide on debugging multi-agent workflows:

### Three Failure Layers
1. **Agent failures** (isolated): Wrong output from one agent
   - Fix: Tighter `expected_output`, better tools, right model
2. **Orchestration failures** (systemic): Delegation logic misfired
   - Fix: Track delegation depth, set hard limits, inspect chain
3. **Tool failures** (boundary): Tool returned error/wrong type
   - Fix: Log tool call args and responses, propagate tools explicitly

### Diagnostic Rule
- Same agent fails consistently with different input → tool or role boundary problem
- Same input fails inconsistently → orchestration problem

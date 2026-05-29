# CrewAI vs Ansible — Conceptual Parallels

Both are **orchestration frameworks** for different domains:
- **Ansible**: orchestrates **computers** (SSH/WinRM), modules as atomic actions
- **crewAI**: orchestrates **AI agents** (LLM calls), tools as atomic actions

| Concept | Ansible | crewAI |
|---------|---------|--------|
| **Workflow definition** | Playbook (YAML) | Flow (`@start`/`@listen`/`@router`) |
| **Unit of work** | Task (module invocation) | Task (`description` + `expected_output`) |
| **Reusable component** | Role (tasks + handlers + vars + templates) | Agent (role + goal + backstory + tools) |
| **Team / scope** | Inventory / Group (`webservers`, `databases`) | Crew (composed of specialized agents) |
| **Execution order** | Sequential (linear) or free strategy | `Process.sequential` or `Process.hierarchical` |
| **Event-driven reaction** | Handler (triggered on `notify` → state change) | `@listen(method)` (triggered on method completion) |
| **Conditional routing** | `when:` or `block/rescue` | `@router()` with string labels |
| **Pluggable capabilities** | Module (built-in / custom / collection) | Tool (`@tool` decorator / MCP server) |
| **State / Variables** | Variable precedence (20+ levels), `group_vars` | `Flow[PydanticModel]` state with type safety |
| **Safety validation** | `--check --diff` (dry-run) | `guardrail` / `@human_feedback` decorator |
| **Secrets management** | `ansible-vault` | Environment variables, LLM hooks |
| **Idempotency guarantee** | Modules designed declaratively (desired state) | Guardrails + structured outputs (`output_pydantic`) |
| **Ecosystem** | Galaxy (collections + roles) | 40+ tools, 15+ observability integrations |
| **Testing** | Molecule, ansible-lint | Testing docs, step callbacks |
| **Scale** | `serial`, `forks`, `max_fail_percentage` | `kickoff_for_each`, `@persist`, `kickoff_async` |

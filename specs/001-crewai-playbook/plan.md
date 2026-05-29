# Implementation Plan: crewai-playbook

**Branch**: `001-crewai-playbook` | **Date**: 2026-05-29 | **Spec**: `specs/001-crewai-playbook/spec.md`
**Input**: Feature specification from `/specs/001-crewai-playbook/spec.md`

## Summary

Build a `crewai-playbook` CLI tool that mirrors `ansible-playbook` to orchestrate
crewAI agents via YAML playbooks. Users write playbooks with `agents:`, `tasks:`,
`roles:`, `handlers:`, and optional `block`/`rescue`/`always` — the tool parses
them, resolves agent definitions from `config/agents.yaml`, and executes them
through crewAI's Python API.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: crewai, PyYAML, typer (CLI), rich (output), pydantic (validation)  
**Storage**: YAML files on filesystem (playbooks, inventory, roles)  
**Testing**: pytest with pytest-mock for LLM-free unit tests  
**Target Platform**: Linux / macOS CLI  
**Project Type**: CLI tool (Python package, installable via `pip`)  
**Performance Goals**: Parse + validate 100-line playbook <2s; `--check` makes zero LLM calls  
**Constraints**: Must wrap crewAI SDK — no replacing crewAI internals. No LLM calls in `--check` or `--syntax-check`.  
**Scale/Scope**: v1 targets single-playbook execution; no concurrency or distributed mode.

## Constitution Check

*GATE: Passes — all 5 principles satisfied:*
1. **YAML-Driven Configuration** (P-I): The entire tool is YAML-driven playbooks + inventory.
2. **Ansible-Compatible CLI** (P-II): Flags mirror `ansible-playbook` (`--check`, `--tags`, `--syntax-check`, `--limit`, `-e`, `-v`).
3. **Separation of Concerns** (P-III): Playbooks (orchestration), agents.yaml (definitions), roles/ (reusable logic) are separate.
4. **Idempotency & Guardrails** (P-IV): `--check` prevents unwanted execution; `--syntax-check` catches errors early.
5. **Convention over Configuration** (P-V): Sensible defaults (`gather_facts: true`, `become: false`, `config/agents.yaml`).

## Project Structure

### Documentation (this feature)

```text
specs/001-crewai-playbook/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: Architecture research & decisions
└── tasks.md             # Phase 2: Concrete implementation tasks
```

### Source Code (repository root)

```text
src/crewai_playbook/
├── __init__.py
├── __main__.py          # python -m entry point
├── cli/
│   ├── __init__.py
│   ├── app.py           # typer app + command definitions
│   └── flags.py         # shared CLI flag definitions
├── core/
│   ├── __init__.py
│   ├── executor.py      # playbook execution engine
│   ├── parser.py        # YAML playbook parser + validator
│   ├── inventory.py     # agents.yaml loader + agent resolution
│   └── runner.py        # crewAI crew runner wrapper
├── modules/
│   ├── __init__.py
│   ├── task.py          # task execution logic
│   ├── block.py         # block/rescue/always handler
│   ├── role.py          # role loader
│   ├── handler.py       # handler notifier/executor
│   ├── facts.py         # gather_facts implementation
│   └── debug.py         # debug module
├── models/
│   ├── __init__.py
│   ├── playbook.py      # Playbook, Play, Task, Block data models
│   ├── agent.py         # AgentDefinition model
│   └── role.py          # Role model
├── utils/
│   ├── __init__.py
│   ├── vars.py          # variable templating (Jinja2-like)
│   ├── config.py        # crewai-playbook.yml config loader
│   └── errors.py        # custom error types
└── resources/
    └── scaffold/        # init command templates
        ├── playbooks/
        ├── config/agents.yaml
        ├── roles/
        └── group_vars/

tests/
├── unit/
│   ├── test_parser.py
│   ├── test_inventory.py
│   ├── test_executor.py
│   ├── test_vars.py
│   ├── test_block.py
│   ├── test_handler.py
│   ├── test_facts.py
│   └── test_cli.py
├── fixtures/
│   ├── playbooks/       # sample playbooks for tests
│   ├── agents.yaml
│   └── roles/
└── conftest.py

config/
├── agents.yaml          # default agent inventory (for testing/dev)

docs/
├── crewai/              # existing research
├── ansible/             # existing research
└── crewai-vs-ansible.md # existing comparison

pyproject.toml           # package config + dependencies
```

## Phases

### Phase 0: Foundation & Architecture Research

- Decide on CLI framework: **typer** (built on click, type-safe, auto-help).
- Decide on validation: **pydantic** for YAML schema models.
- Decide on output: **rich** for colored terminal output, progress bars, diffs.
- Decide on variable templating: lightweight `string.Template` or regex-based (no full Jinja2 to keep deps minimal; upgrade to Jinja2 later if needed).
- Confirm crewAI API surface for programmatic crew creation (Crew, Agent, Task, Process).
- Outcome: `research.md` documenting architecture decisions.

### Phase 1: Data Models & Parsing

- Define pydantic models: `Playbook` (list of `Play`), `Play` (agents, vars, tasks, roles, handlers, gather_facts, become), `Task` (name, agents, task, src, dest, register, when, notify, until, retries, delay), `Block` (block/rescue/always tasks), `Handler` (name, tasks), `Role` (name, vars).
- Implement `parser.py` — load YAML, validate against pydantic schemas, resolve `{{ variable }}` references.
- Implement `inventory.py` — load `agents.yaml`, parse agent definitions (role, goal, backstory, tools, llm), resolve `@group` expansion.
- Implement `--syntax-check` — standalone validation command.
- Outcome: Playbooks parse correctly; syntax-check passes/fails as expected.

### Phase 1.5: CLI Shell

- Implement `app.py` with typer: `run`, `init`, `--syntax-check`, `--check`, `--tags`, `--skip-tags`, `--diff`, `--list-tasks`, `--list-tags`, `--limit`, `-e`, `-v`.
- Wire basic command routing (parse playbook, then hand to executor).
- Outcome: All CLI flags accepted; error messages for missing required args.

### Phase 2: Task & Play Execution

- Implement `runner.py` — wrap crewAI's `Crew`, `Agent`, `Task`, `Process` to create and run crews programmatically.
- Implement `executor.py` — orchestration loop: for each play, resolve agents, gather facts (if enabled), execute tasks sequentially, handle block/rescue/always, fire handlers.
- Implement `task.py` — single task execution through crewAI, handle `register` to capture output, `until`/`retries`/`delay` for retry logic.
- Implement `block.py` — block/rescue/always execution with try/except semantics.
- Implement `handler.py` — notify tracking + deferred handler execution at play end.
- Implement `facts.py` — gather system info (OS, Python version, tools available) into `{{ facts }}` dict.
- Implement `vars.py` — variable substitution across playbook fields.
- Outcome: A simple playbook with 1 play, 2 agents, 1 task runs end-to-end.

### Phase 3: Roles & Advanced Features

- Implement `role.py` — load role from `roles/<name>/tasks/main.yml`, resolve defaults from `defaults/main.yml`, apply role vars from playbook.
- Implement `--check` mode — trace execution path without calling crewAI.
- Implement `--diff` — compare `dest` file content before/after.
- Implement `debug` module — print variable values to stdout.
- Implement `crewai-playbook run --limit` — filter agents by name or group.
- Outcome: Role-based playbooks, check mode, diff, debug all functional.

### Phase 4: Init Scaffold & Polish

- Implement `crewai-playbook init` — create directory scaffold with example files.
- Implement `crewai-playbook lint` — extended validation (undefined vars, missing agents, circular roles).
- Implement `crewai-playbook.yml` project config support.
- Add rich output formatting, error handling, and verbosity levels.
- Outcome: `init` scaffolds a new project; `lint` catches common mistakes.

### Phase 5: Testing & Hardening

- Write unit tests for parser, inventory, vars, executor (mocked crewAI).
- Write integration tests with fixture playbooks.
- Test edge cases: missing agents.yaml, circular role deps, failed block rescue, handler not-triggered, `--check` with nonexitent dest.
- Test `--syntax-check` on invalid YAML, missing fields, bad variable refs.
- Outcome: >=80% coverage; all acceptance scenarios verified.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| block/rescue/always | Must match Ansible's error-handling pattern | Simple task-only would lose Ansible parity |
| Role system | Reuse across playbooks | Copy-paste tasks would violate DRY |
| Handler system | Change-triggered actions per Ansible spec | Running all tasks unconditionally wastes LLM calls |

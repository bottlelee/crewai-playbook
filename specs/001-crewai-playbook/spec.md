# Feature Specification: crewai-playbook

**Feature Branch**: `001-crewai-playbook`
**Created**: 2026-05-29
**Status**: Draft
**Input**: Base on the researched documents in `docs/`, create a `crewai-playbook` tool similar to `ansible-playbook`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run a Simple Playbook (Priority: P1)

As a user familiar with Ansible, I want to write a YAML playbook with agents and
tasks and run it with `crewai-playbook run playbook.yml`, so that I can
orchestrate AI agents without writing Python code.

**Why this priority**: This is the core value proposition — YAML-driven agent
orchestration. Without it, there is no product.

**Independent Test**: Create a minimal playbook with one task and one agent, run
`crewai-playbook run test.yml --syntax-check`, then `crewai-playbook run
test.yml`, verify agents executed and output was produced.

**Acceptance Scenarios**:

1. **Given** a valid playbook with `name`, `agents`, and `tasks`, **When**
   running `crewai-playbook run playbook.yml`, **Then** all agents execute their
   tasks and output is printed to stdout.
2. **Given** a playbook with a syntax error, **When** running
   `crewai-playbook --syntax-check playbook.yml`, **Then** a non-zero exit code
   and descriptive error message are returned.
3. **Given** a playbook with an undefined variable reference, **When** running
   `crewai-playbook run playbook.yml`, **Then** the tool fails with a clear
   reference error before any agent executes.

---

### User Story 2 - Dry-Run with --check (Priority: P1)

As a user managing production agent workflows, I want to run
`crewai-playbook --check playbook.yml` to preview what agents would do without
actually executing them, so that I can validate changes safely.

**Why this priority**: Safety is a first-class concern, mirroring Ansible's
`--check` mode. Without it, users cannot trust the tool in production.

**Independent Test**: Run `crewai-playbook --check --diff test.yml` on a
playbook, verify it parses the playbook and reports expected actions without
making any LLM calls.

**Acceptance Scenarios**:

1. **Given** any playbook, **When** running with `--check`, **Then** no agents
   are invoked and the tool prints what it WOULD do.
2. **Given** a playbook with `dest` paths, **When** running with `--check
   --diff`, **Then** expected file output diffs are displayed.
3. **Given** a playbook with conditional tasks (`when:`), **When** running with
   `--check`, **Then** conditions are evaluated and skipped tasks are reported.

---

### User Story 3 - Playbook with Block/Rescue/Always (Priority: P2)

As a user writing robust automation, I want to use `block`/`rescue`/`always`
sections in playbook tasks, so that I can handle agent failures gracefully with
fallback agents and always-run cleanup.

**Why this priority**: Error handling is essential for production use, but the
core execution (US1) and safety (US2) come first.

**Independent Test**: Write a playbook where the `block` task is configured to
fail, verify the `rescue` section executes with alternative agents, and the
`always` section runs regardless.

**Acceptance Scenarios**:

1. **Given** a `block` with `rescue` and `always`, **When** the block task
   fails, **Then** the rescue task runs with its specified agents and the always
   task runs afterward.
2. **Given** a `block` with `rescue` and `always`, **When** the block task
   succeeds, **Then** the rescue task is skipped and the always task still runs.
3. **Given** a `block` without a `rescue`, **When** the block task fails, **Then**
   the error propagates to the playbook level.

---

### User Story 4 - Role-Based Playbook Execution (Priority: P2)

As a user building complex agent workflows, I want to define reusable `roles`
in a roles/ directory and reference them in playbooks, so that I can compose
and reuse complex agent task groups.

**Why this priority**: Roles enable reuse at scale. Without them, playbooks
become unmanageable beyond a handful of tasks.

**Independent Test**: Create a role with default vars and tasks, reference it
in a playbook with role vars, verify role tasks execute with the provided vars.

**Acceptance Scenarios**:

1. **Given** a role defined in `roles/myrole/` with `defaults/main.yml` and
   `tasks/main.yml`, **When** a playbook references `roles: - role: myrole`,
   **Then** the role's tasks execute with default variables.
2. **Given** a playbook referencing a role with `vars:`, **When** executed,
   **Then** the provided vars override role defaults.
3. **Given** a playbook referencing a nonexistent role, **When** executed,
   **Then** a clear error is raised referencing the missing role path.

---

### User Story 5 - Tags for Targeted Execution (Priority: P3)

As a user with a large playbook, I want to tag tasks and run only a subset with
`--tags` / `--skip-tags`, so that I can iterate quickly on specific parts of a
workflow.

**Why this priority**: A productivity boost but not required for the core loop.

**Independent Test**: Write a playbook with 3 tasks tagged `research`,
`coding`, `summary`. Run with `--tags coding`, verify only the coding task
executes.

**Acceptance Scenarios**:

1. **Given** a playbook with tagged tasks, **When** running with
   `--tags research`, **Then** only tasks with the `research` tag execute.
2. **Given** a playbook with tagged tasks, **When** running with
   `--skip-tags summary`, **Then** tasks tagged `summary` are skipped.
3. **Given** a playbook with `--list-tags`, **Then** all available tags are
   printed without executing anything.

---

### User Story 6 - Handlers for Change-Driven Actions (Priority: P3)

As a user, I want `notify`/`handlers` so that follow-up actions (e.g.,
summarization, logging) only run when a preceding task actually produced a
result.

**Why this priority**: Mirrors Ansible's handler pattern; nice-to-have for
production but not MVP-blocking.

**Independent Test**: Write a playbook with a task that `notify`s a handler.
Verify the handler runs only when the notifying task produces output.

**Acceptance Scenarios**:

1. **Given** a task with `notify: Summary`, **When** the task completes with
   output, **Then** the `Summary` handler executes.
2. **Given** a task with `notify: Summary`, **When** the task produces no
   output (e.g., skipped by `when:`), **Then** the handler does NOT execute.

---

### User Story 7 - Gather Facts for Context Awareness (Priority: P3)

As a user, I want `gather_facts: true` to automatically collect development
environment info (tools, system, hardware, middleware) before tasks run, so
that agents can be context-aware without manual data collection tasks.

**Why this priority**: Enhances agent context but is supplemental to core
execution.

**Independent Test**: Run a playbook with `gather_facts: true`, verify fact
variables are populated and accessible in task templates.

**Acceptance Scenarios**:

1. **Given** a playbook with `gather_facts: true`, **When** executed, **Then**
   facts are gathered before any task runs and stored in `{{ facts }}`.
2. **Given** a playbook with `gather_facts: false`, **When** executed, **Then**
   no facts are gathered and the playbook starts tasks immediately.
3. **Given** facts are gathered, **When** a task references `{{ facts.os }}`,
   **Then** the OS information is available.

---

### Edge Cases

- What happens when an agent specified in `agents:` is not defined in
  `agents.yaml`? → clear error with available agent names.
- What happens when a playbook has circular role dependencies? →
  `--syntax-check` detects and reports the cycle.
- What happens when LLM API returns an error or rate-limit? → `retries`/`delay`
  handle transient failures; `until: result is succeeded` blocks for success.
- What happens when `dest` points to a path the user doesn't have write
  permission for? → error with clear message and path.
- What happens when `--check` mode encounters a task that cannot be
  dry-run? → report as "UNSUPPORTED CHECK MODE" and continue.
- What happens when multiple playbook files are passed? → run each in sequence,
  fail-fast on first error unless `--force-handlers`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST support `crewai-playbook run <playbook.yml>` as the
  primary execution command.
- **FR-002**: The tool MUST parse YAML playbooks conforming to the crewai-
  playbook schema (agents, tasks, block/rescue/always, roles, handlers).
- **FR-003**: The tool MUST support `--check` for dry-run mode that parses the
  playbook and reports expected actions without invoking any agents.
- **FR-004**: The tool MUST support `--diff` in conjunction with `--check` to
  show expected output diffs.
- **FR-005**: The tool MUST support `--tags` and `--skip-tags` for selective
  task execution.
- **FR-006**: The tool MUST support `--syntax-check` to validate playbook YAML
  and variable references without executing.
- **FR-007**: The tool MUST support `--list-tasks` and `--list-tags` for
  playbook introspection.
- **FR-008**: The tool MUST support `--limit <agents>` to target specific
  agents (by name or group from agents.yaml).
- **FR-009**: The tool MUST support `-e`/`--extra-vars` for runtime variable
  overrides in `key=value` or `@file.yml` format.
- **FR-010**: The tool MUST support `-v`/`--verbose` with stackable verbosity
  (`-vvv`).
- **FR-011**: The tool MUST read `agents.yaml` (default: `config/agents.yaml`)
  to resolve agent names and groups referenced in playbooks.
- **FR-012**: The tool MUST support `block`/`rescue`/`always` for error
  handling within task lists.
- **FR-013**: The tool MUST support `handlers:` at the play level, triggered
  by `notify` from tasks.
- **FR-014**: The tool MUST support `roles:` at the play level, loading tasks
  from `roles/<role_name>/tasks/main.yml` with vars from
  `roles/<role_name>/defaults/main.yml`.
- **FR-015**: The tool MUST support `gather_facts: true/false` to optionally
  collect environment context before tasks.
- **FR-016**: The tool MUST support `register`, `until`, `retries`, and `delay`
  for task result tracking and retry logic.
- **FR-017**: The tool MUST support `when:` conditions on tasks.
- **FR-018**: The tool MUST support `src`/`dest` for file-transfer-like
  operations between agent outputs.
- **FR-019**: The tool MUST support `debug` module for printing variable
  values (analogous to Ansible's `debug` module).
- **FR-020**: The tool MUST support `crewai-playbook init` to scaffold a new
  project with standard directory layout.
- **FR-021**: The tool MUST support `crewai-playbook lint` to catch undefined
  variables, missing agent roles, and circular references.
- **FR-022**: The tool MUST support environment variable-based configuration
  (`CREWAI_PLAYBOOK_INVENTORY`, `CREWAI_PLAYBOOK_VAULT_PASSWORD`, etc.).
- **FR-023**: The tool MUST read `crewai-playbook.yml` (project config) for
  defaults like default inventory path, LLM provider, etc.

### Key Entities

- **Playbook**: Top-level YAML document defining a list of plays. Each play
  has `name`, `agents`, `tasks` or `roles`, `handlers`, and optional
  `become`, `gather_facts`, `vars`.
- **Agent**: Defined in `agents.yaml` with `role`, `goal`, `backstory`,
  `tools`, `llm`. Agents are referenced by name in playbook `agents:` fields.
- **Task**: A unit of work within a play. Has `name`, `agents` (list or group),
  `task` (description string), optional `src`, `dest`, `register`, `when`,
  `notify`, `until`, `retries`, `delay`.
- **Role**: A reusable set of tasks stored in `roles/<name>/`. Contains
  `defaults/main.yml`, `tasks/main.yml`, optional `handlers/` and `vars/`.
- **Handler**: Named task list triggered by `notify` from tasks. Defined at
  play level in `handlers:`.
- **Block**: A group of tasks with shared `when`, `rescue`, `always` semantics.
- **Inventory/Vars**: Environment-specific configuration files in
  `inventory/` or `group_vars/` providing LLM configs, API keys, etc.
- **Fact**: System/environment info gathered when `gather_facts: true`,
  accessible as `{{ facts.* }}`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user familiar with Ansible can write and run their first
  playbook within 15 minutes of installing the tool.
- **SC-002**: `crewai-playbook --syntax-check` validates a 100-line playbook
  in under 2 seconds.
- **SC-003**: `crewai-playbook --check` reports expected actions without
  making any LLM API calls.
- **SC-004**: All CLI flags (`--check`, `--tags`, `--syntax-check`, `--limit`,
  `-e`, `-v`) work consistently across playbooks of varying complexity.
- **SC-005**: A playbook with `block`/`rescue`/`always` correctly handles
  agent failure in rescue and always runs.
- **SC-006**: A role-based playbook runs seamlessly referencing roles from
  `roles/` directory with variable overrides.

## Assumptions

- **Target users**: Developers and ops teams familiar with Ansible who want to
  orchestrate crewAI agents. Familiarity with YAML and basic Ansible concepts
  (playbooks, roles, inventory, handlers) is assumed.
- **Scope boundaries**: v1 focuses on the `crewai-playbook run` command and
  core playbook schema. `crewai-playbook pull` (agent-less push/pull mode) is
  out of scope for v1. Web UI is out of scope.
- **Python environment**: Python 3.10+ on the control node with `crewai`
  installed. The tool wraps crewAI's Python API — it does not replace crewAI.
- **LLM access**: Assumes users have configured LLM provider access (OpenAI,
  Anthropic, etc.) via environment variables or inventory vault files.
- **Dependencies**: Requires `crewai` (PyPI), `PyYAML`, and a CLI framework
  (`click` or `typer`). The `crewai-playbook.yml` project config is optional.
- **Project structure**: The `crewai-playbook init` scaffold follows Ansible's
  convention: `playbooks/`, `roles/`, `config/agents.yaml`, `inventory/`,
  `group_vars/`.

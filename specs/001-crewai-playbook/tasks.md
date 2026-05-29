# Tasks: crewai-playbook

**Input**: Design documents from `specs/001-crewai-playbook/`
**Prerequisites**: plan.md, spec.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US7)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per plan.md (src/crewai_playbook/, tests/, config/, pyproject.toml)
- [ ] T002 Initialize pyproject.toml with dependencies (typer, PyYAML, pydantic, rich, crewai)
- [ ] T003 [P] Configure pytest, pytest-cov, conftest.py with test fixtures

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, parser, inventory, CLI shell — all user stories depend on these.

- [ ] T004 Create pydantic data models in src/crewai_playbook/models/playbook.py (Playbook, Play, Task, Block, Handler)
- [ ] T005 Create AgentDefinition model in src/crewai_playbook/models/agent.py
- [ ] T006 Create Role model in src/crewai_playbook/models/role.py
- [ ] T007 Implement YAML parser + pydantic validator in src/crewai_playbook/core/parser.py
- [ ] T008 Implement inventory loader in src/crewai_playbook/core/inventory.py (load agents.yaml, resolve `@group`)
- [ ] T009 Implement variable templating in src/crewai_playbook/utils/vars.py ({{ var }} substitution)
- [ ] T010 [P] Implement custom error types in src/crewai_playbook/utils/errors.py
- [ ] T011 Implement typer CLI app shell in src/crewai_playbook/cli/app.py (run, init, lint, --syntax-check, --check, --tags, --skip-tags, --diff, --list-tasks, --list-tags, --limit, -e, -v)
- [ ] T012 Implement project config loader in src/crewai_playbook/utils/config.py (crewai-playbook.yml)

**Checkpoint**: Foundation ready — playbooks parse, inventory loads, CLI accepts all flags.

---

## Phase 3: User Story 1 — Run a Simple Playbook (Priority: P1) 🎯 MVP

**Goal**: Users can write a YAML playbook with agents + tasks and run it.

**Independent Test**: Create minimal playbook `test.yml`, run `crewai-playbook --syntax-check test.yml` then `crewai-playbook run test.yml`, verify agents execute and output is produced.

- [ ] T013 Implement crewAI runner wrapper in src/crewai_playbook/core/runner.py (programmatic Crew/Agent/Task creation)
- [ ] T014 Implement single task execution in src/crewai_playbook/modules/task.py (run task through runner, handle `register`, `until`/`retries`/`delay`)
- [ ] T015 Implement playbook executor in src/crewai_playbook/core/executor.py (play loop: resolve agents → execute tasks sequentially)
- [ ] T016 Integrate CLI `run` command in app.py to wire parser → executor → runner
- [ ] T017 Implement `--syntax-check` validation (parse YAML, validate schema, check variable refs without executing)

**Checkpoint**: US1 fully functional — `crewai-playbook run simple.yml` works end-to-end.

---

## Phase 4: User Story 2 — Dry-Run with --check (Priority: P1)

**Goal**: Users can preview what agents would do without LLM calls.

**Independent Test**: Run `crewai-playbook --check --diff test.yml`, verify it parses and reports expected actions without any LLM calls.

- [ ] T018 Implement `--check` mode in executor (trace execution path, output planned actions, zero crewAI calls)
- [ ] T019 Implement `--diff` mode (compare `dest` file content before/after when in check mode)
- [ ] T020 [P] Verify `--check --diff` produces meaningful output for tasks with `dest` fields

**Checkpoint**: US2 fully functional — --check runs quickly with no LLM calls.

---

## Phase 5: User Story 3 — Block/Rescue/Always (Priority: P2)

**Goal**: Users can handle agent failures gracefully.

**Independent Test**: Write a playbook with `block`/`rescue`/`always`, simulate block failure, verify rescue + always run.

- [ ] T021 Implement block/rescue/always execution in src/crewai_playbook/modules/block.py (try/except/finally semantics for task groups)
- [ ] T022 Wire block handler into executor for plays that use block structures
- [ ] T023 Handle propagation: unhandled block failures → play-level error

**Checkpoint**: US3 functional — block/rescue/always works like Ansible.

---

## Phase 6: User Story 4 — Role-Based Playbook Execution (Priority: P2)

**Goal**: Users can define and reuse roles.

**Independent Test**: Create `roles/myrole/` with defaults + tasks, reference it in a playbook, verify execution.

- [ ] T024 Implement role loader in src/crewai_playbook/modules/role.py (load role tasks + defaults, apply role vars)
- [ ] T025 Integrate role loading into executor (before task execution, resolve and inject role tasks)
- [ ] T026 Handle role variable precedence (playbook vars > role vars > role defaults)

**Checkpoint**: US4 functional — role-based playbooks work with variable overriding.

---

## Phase 7: User Story 5 — Tags for Targeted Execution (Priority: P3)

**Goal**: Users can run a subset of tasks by tag.

**Independent Test**: Tag 3 tasks, run with `--tags coding`, verify only tagged task executes.

- [ ] T027 Implement `--tags` / `--skip-tags` filtering in executor (skip tasks that don't match tag filter)
- [ ] T028 Implement `--list-tags` mode (print all tags without executing)

**Checkpoint**: US5 functional — tag filtering works on any playbook.

---

## Phase 8: User Story 6 — Handlers (Priority: P3)

**Goal**: Follow-up actions only run on task change.

**Independent Test**: Write a task that `notify`s a handler; verify handler runs only when task produces output.

- [ ] T029 Implement handler queuing in src/crewai_playbook/modules/handler.py (notify tracking, deferred execution at play end)
- [ ] T030 Wire handlers into executor (collect notifications during task execution, run handlers after all tasks)
- [ ] T031 Handle edge case: handler runs only if notifying task produced output

**Checkpoint**: US6 functional — handlers fire only on output-producing tasks.

---

## Phase 9: User Story 7 — Gather Facts (Priority: P3)

**Goal**: Auto-collect environment context before tasks.

**Independent Test**: Run with `gather_facts: true`, verify `{{ facts.os }}` is populated.

- [ ] T032 Implement fact gathering in src/crewai_playbook/modules/facts.py (collect OS, Python version, tools, hardware, middleware)
- [ ] T033 Wire facts into executor (run before tasks when `gather_facts: true`, populate `{{ facts }}` variable)
- [ ] T034 Handle `gather_facts: false` — skip gathering entirely

**Checkpoint**: US7 functional — facts available in playbooks when enabled.

---

## Phase 10: Advanced Features

- [ ] T035 Implement `crewai-playbook lint` command (undefined vars, missing agents, circular role deps)
- [ ] T036 Implement `crewai-playbook init` scaffold command (create directory structure with examples)
- [ ] T037 Implement `debug` module in src/crewai_playbook/modules/debug.py (print variable values)
- [ ] T038 Implement `--limit` agent filtering (by name or @group from inventory)

---

## Phase 11: Testing & Hardening

- [ ] T039 [P] Unit tests for parser in tests/unit/test_parser.py
- [ ] T040 [P] Unit tests for inventory in tests/unit/test_inventory.py
- [ ] T041 [P] Unit tests for executor (mocked crewAI) in tests/unit/test_executor.py
- [ ] T042 [P] Unit tests for variables in tests/unit/test_vars.py
- [ ] T043 [P] Unit tests for block/rescue/always in tests/unit/test_block.py
- [ ] T044 [P] Unit tests for handlers in tests/unit/test_handler.py
- [ ] T045 [P] Unit tests for facts in tests/unit/test_facts.py
- [ ] T046 [P] Unit tests for CLI flags in tests/unit/test_cli.py
- [ ] T047 Create fixture playbooks in tests/fixtures/ (valid, invalid, roles, blocks, handlers, tags)
- [ ] T048 Create sample config/agents.yaml for tests
- [ ] T049 Integration: all US1 acceptance scenarios pass
- [ ] T050 Integration: all US2–US7 acceptance scenarios pass
- [ ] T051 Edge cases: missing agents.yaml, circular roles, failed block, handler not-triggered, --check with nonexistent dest, --syntax-check on bad YAML

---

## Implementation Strategy

### MVP First (US1 + US2)
1. Phase 1: Setup
2. Phase 2: Foundational (parser, models, inventory, CLI shell)
3. Phase 3: US1 (simple playbook execution)
4. Phase 4: US2 (--check mode)
5. **STOP and validate**: `crewai-playbook run simple.yml` + `--check` works

### Incremental Delivery
1. MVP (US1+US2) → Basic playbook execution with safety dry-run
2. Add US3 (block/rescue) → Error handling
3. Add US4 (roles) → Reusable components
4. Add US5–US7 (tags, handlers, facts) → Production polish
5. Phase 10 (init, lint, debug, limit) → Developer experience
6. Phase 11 (testing) → Coverage & hardening

### Parallel Opportunities
- T003/T004/T010 (different files)
- T039–T046 all marked [P] (different test files)
- US5 (tags) and US6 (handlers) can be developed independently since they touch different modules

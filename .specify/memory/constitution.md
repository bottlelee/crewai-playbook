<!--
  Sync Impact Report
  ===================
  Version change: (new) v1.0.0
  Modified principles: N/A (initial version)
  Added sections:
    - Five Core Principles (I through V)
    - Section 2: Technical Constraints
    - Section 3: Quality Gates
    - Governance section
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/constitution-template.md — ✅ not touched (source template)
    - .specify/templates/plan-template.md — ⚠ pending: add "Constitution Check" gates ref
    - .specify/templates/spec-template.md — ✅ no changes needed
    - .specify/templates/tasks-template.md — ✅ no changes needed
    - .specify/templates/checklist-template.md — ✅ no changes needed
  Follow-up TODOs: None — all placeholders resolved.
-->

# crewai-playbook Constitution

## Core Principles

### I. YAML-Driven Configuration
Playbooks, agent definitions, task specs, and flow orchestration MUST be
expressed declaratively in YAML — not hardcoded in Python. No Python code
should be required for standard use cases. This mirrors Ansible's philosophy
where YAML is the source of truth and code is the exception.

Rationale: YAML is readable, version-controllable, and accessible to non-
developers. Hardcoding forces re-deployment for every change; YAML allows
ops teams to modify automation without touching source code.

### II. Ansible-Compatible CLI
The CLI MUST mirror `ansible-playbook` conventions so users familiar with
Ansible can adopt `crewai-playbook` with zero learning curve:
- `crewai-playbook run playbook.yml` — execute a playbook
- `--check` — dry-run without executing agents
- `--tags` / `--skip-tags` — run subsets of tasks
- `--syntax-check` — validate YAML before execution
- `--list-hosts` / `--list-tasks` — introspection
- `--limit` — target specific "hosts" (crew instances)
- `-e` / `--extra-vars` — override variables at runtime
- `-v` — verbose mode (stackable: -vvv)

### III. Separation of Concerns
Configuration MUST be separated from orchestration logic:
- **Inventory files**: LLM provider configs, API keys, model params per
  environment (dev/staging/prod) — analogous to Ansible's `group_vars/`.
- **Playbook files**: Crew composition, agent roles, task sequences, flow
  definitions — analogous to Ansible playbooks.
- **Variable files**: Environment-specific values in YAML vars, overridable
  via `-e` at runtime.
- **Secrets**: API keys, tokens via environment variables or encrypted vault
  files — never in playbook YAML.

### IV. Idempotency & Guardrails
Every playbook run MUST be safe to re-run. The tool MUST enforce:
- **Guardrails**: Built-in output validation (length, format, content checks)
  analogous to Ansible's `changed_when` / `failed_when`.
- **Structured outputs**: Agents MUST produce typed outputs (`output_pydantic`)
  so downstream tasks can depend on well-defined schemas.
- **Check mode** (`--check`): Preview what agents would do without executing.
- **Dry-run diff** (`--check --diff`): Show expected output changes.
- **Handlers**: Only trigger follow-up actions (e.g., summarization, alerts)
  when preceding task output actually changed.

### V. Convention over Configuration
Sensible defaults MUST ship out-of-the-box:
- Default agent role templates for common patterns (researcher, writer,
  analyst, reviewer).
- Default LLM config (gpt-4o-mini) with automatic failover hints.
- Default task templates (research, draft, review, summarize).
- Users opt out explicitly, not configure from scratch.
- `crewai-playbook init` SHOULD scaffold a complete project with standard
  directory layout, sample playbook, and inventory skeleton.

## Technical Constraints

- **Runtime**: Python 3.10+ required on the control node.
- **YAML**: YAML 1.2 specification for all playbook and config files.
- **Dependency**: crewAI (open-source, latest stable) as the agent runtime.
- **CLI Framework**: Python CLI tool built with `click` or `typer`.
- **Configuration Precedence** (lowest to highest):
  1. Role defaults (bundled with tool)
  2. Project-level `crewai-playbook.yml` config
  3. Inventory `group_vars/` files
  4. Playbook `vars:` section
  5. Extra vars (`-e` / `--extra-vars`)
- **Observability**: Structured JSON logging; optional OpenTelemetry export.

## Quality Gates

- **Syntax check**: `crewai-playbook --syntax-check playbook.yml` MUST pass
  before any execute command is accepted.
- **Dry-run**: `--check` mode MUST be available for every playbook command.
- **Linting**: `crewai-playbook lint` MUST catch common issues: undefined
  variables, missing agent roles, circular crew references.
- **Test suite**: Canonical integration tests covering all CLI flags, YAML
  parsing edge cases, and playbook execution lifecycle.
- **CI pipeline**: Every commit MUST pass syntax check + lint + unit tests.

## Governance

This constitution supersedes all other practices for the crewai-playbook
project. Amendments require:
1. Documented rationale in a Pull Request.
2. Approval from at least one maintainer.
3. Migration plan for any backward-incompatible changes.
4. Version bump per SemVer rules (see below).

Versioning policy:
- **MAJOR**: Backward-incompatible CLI changes, principle removals.
- **MINOR**: New principles, materially expanded guidance, new CLI flags.
- **PATCH**: Clarifications, wording fixes, non-semantic refinements.

Compliance: All PRs MUST reference the relevant constitution principle(s).

Use `AGENTS.md` for runtime development guidance.

**Version**: 1.0.0 | **Ratified**: 2026-05-29 | **Last Amended**: 2026-05-29

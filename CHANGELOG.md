# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-29

### Added

- **CLI** — `crewai-playbook run`, `init`, and `lint` commands with Ansible-compatible flags (`--check`, `--diff`, `--syntax-check`, `--list-tasks`, `--list-tags`, `--tags`, `--skip-tags`, `--limit`, `-e`, `-v`, `-i`).
- **Playbook engine** — YAML-driven orchestration with plays, tasks, blocks, handlers, and roles.
- **Variable system** — `{{ var }}` templating with dotted-path resolution; `-e` extra vars with highest precedence (supports `key=value` and JSON formats).
- **Agent inventory** — Load agents from `config/agents.yaml` with `@group` resolution.
- **Variable precedence** — Extra vars (`-e`) > play vars (`vars:`) > role vars > role defaults.
- **Execution modes** — Sequential (default) and hierarchical (leader agent delegates to sub-agents via crewAI `Process.hierarchical`).
- **Task lifecycle** — `register`, `until`, `retries`, `delay`, `when`, `src`/`dest` file I/O.
- **Error handling** — `block`/`rescue`/`always` with fallback agents.
- **Handlers** — `notify`-driven deferred execution.
- **Roles** — Reusable task collections in `roles/<name>/tasks/main.yml` with `defaults/main.yml`.
- **Facts** — `gather_facts: true` collects OS, Python, cwd, environment, and tool availability.
- **Debug module** — `debug:` with `msg` and `var` support.
- **Check mode** — `--check` previews planned actions without LLM invocations.
- **Syntax check** — `--syntax-check` validates YAML structure and variable references.
- **Scaffold** — `crewai-playbook init` creates a complete project directory.
- **Lint** — Validates play names, agent references, group references, and duplicate roles.
- **Ollama support** — `ollama/<model>` LLM spec resolved to `ChatOpenAI` at `OLLAMA_BASE_URL`.
- **LLM provider resolution** — `_resolve_llm()` in runner converts `ollama/` prefix to LangChain `ChatOpenAI` instance.
- **Manager LLM** — Hierarchical process sets `manager_llm` on crewAI `Crew` (required for crewAI 0.22.5 compatibility).
- **106 unit tests** covering parser, executor, task execution, blocks, handlers, roles, facts, CLI, lint, scaffold, and variable resolution.

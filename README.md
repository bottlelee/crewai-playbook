# crewai-playbook

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-106%20passing-brightgreen)](tests/)
[![CLI](https://img.shields.io/badge/CLI-typer-8A2BE2)](https://typer.tiangolo.com)

**Ansible-compatible YAML playbook orchestrator for [crewAI](https://crewai.com) agents.**

Write declarative YAML playbooks — just like Ansible — to orchestrate multi-agent AI workflows. Define agents in a static inventory, compose plays with tasks, blocks, handlers, and roles, then execute locally or in your CI pipeline.

```yaml
# playbook.yml
- name: Research & Writing Pipeline
  agents: [manager, researcher, writer, reviewer]
  vars:
    topic: "Artificial Intelligence"
  tasks:
    - name: Research the topic
      agents: [researcher]
      task: 'Research "{{ topic }}" and provide key findings'
```

```bash
crewai-playbook run playbook.yml -i config/agents.yaml
```

---

## Installation

```bash
pip install crewai-playbook
# or with uv
uv pip install crewai-playbook
```

Requires Python 3.10+ and a running [Ollama](https://ollama.com) instance (or any OpenAI-compatible API).

### Quick Start

```bash
# Scaffold a new project
crewai-playbook init my-project
cd my-project

# Define agents in config/agents.yaml
# Write a playbook in playbooks/

# Validate syntax
crewai-playbook lint playbooks/research.yml -i config/agents.yaml

# Dry-run (no LLM calls)
crewai-playbook run playbooks/research.yml -i config/agents.yaml --check

# Execute
crewai-playbook run playbooks/research.yml -i config/agents.yaml

# Override variables
crewai-playbook run playbooks/research.yml -i config/agents.yaml -e "topic=Quantum Computing"
```

---

## Features

| Feature | Description |
|---------|-------------|
| **YAML-driven** | Declarative playbooks — no Python coding required |
| **Familiar syntax** | Mirrors Ansible: plays, tasks, blocks, handlers, roles, vars |
| **Dry-run** | `--check` previews planned actions without LLM calls |
| **Hierarchical mode** | Leader agent delegates work to sub-agents (crewAI `Process.hierarchical`) |
| **Sequential mode** | Tasks run in order, one agent at a time |
| **Variable templating** | `{{ var }}` interpolation in task descriptions, `src`/`dest` paths |
| **Extra vars** | `-e key=value` or `-e '{"key":"val"}'` — highest precedence |
| **Block/Rescue/Always** | Error handling with fallback agents and cleanup tasks |
| **Handlers + Notify** | Deferred actions triggered by task output |
| **Tags** | `--tags` / `--skip-tags` for selective execution |
| **Agent groups** | `@group` syntax in `--limit` and play agent lists |
| **Roles** | Reusable task collections in `roles/<name>/tasks/main.yml` |
| **Gather facts** | Automatic environment introspection (`gather_facts: true`) |
| **Syntax check** | `--syntax-check` validates YAML and variable references |
| **Lint** | `lint` command checks play names, agents, role references |
| **Scaffold** | `init` creates a complete project directory structure |
| **Ollama ready** | Built-in `ollama/` LLM prefix resolution — no cloud API needed |

---

## CLI Reference

### `run` — Execute a playbook

```bash
crewai-playbook run [OPTIONS] PLAYBOOK
```

| Flag | Description |
|------|-------------|
| `--check` | Dry-run, no LLM calls |
| `--diff` | Show expected file diffs (with `--check`) |
| `--syntax-check` | Validate YAML + variable refs, then exit |
| `--list-tasks` | Print all tasks and exit |
| `--list-tags` | Print all tags and exit |
| `--tags TEXT` | Only run tasks with these tags (repeatable) |
| `--skip-tags TEXT` | Skip tasks with these tags (repeatable) |
| `--limit TEXT` | Limit to specific agents (`name` or `@group`) |
| `-e`, `--extra-vars TEXT` | Extra variables (`key=value` or JSON) |
| `-v` | Verbosity (stackable: `-v`, `-vv`) |
| `-i`, `--inventory TEXT` | Agent inventory path (default: `config/agents.yaml`) |

### `init` — Scaffold a project

```bash
crewai-playbook init [PATH]
```

### `lint` — Validate a playbook

```bash
crewai-playbook lint [OPTIONS] PLAYBOOK
```

| Flag | Description |
|------|-------------|
| `-i`, `--inventory TEXT` | Agent inventory path |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama / OpenAI-compatible endpoint |
| `CREWAI_PLAYBOOK_INVENTORY` | `config/agents.yaml` | Default inventory path |
| `CREWAI_PLAYBOOK_CONFIG` | — | Project config path |

---

## Supported LLM Providers

| Provider | Spec | Example |
|----------|------|---------|
| OpenAI | `gpt-4`, `gpt-4o`, … | `llm: "gpt-4o"` |
| Ollama | `ollama/<model>` | `llm: "ollama/gemma4:latest"` |

Set `OLLAMA_BASE_URL` to point at any OpenAI-compatible endpoint (Ollama, vLLM, etc.).

---

## Agent Inventory

Define agents in `config/agents.yaml`:

```yaml
agents:
  researcher:
    role: "Research Specialist"
    goal: "Find and synthesize relevant information"
    backstory: "Expert researcher with years of experience."
    llm: "ollama/gemma4:latest"
    groups: ["default", "research"]

  manager:
    role: "Project Manager"
    goal: "Coordinate agents and delegate tasks"
    backstory: "Experienced team lead."
    leader: true
    groups: ["default"]
```

---

## Project Layout

```
my-project/
├── config/
│   └── agents.yaml              # Agent definitions
├── playbooks/
│   └── research.yml             # Your playbooks
├── roles/
│   └── <name>/
│       ├── defaults/
│       │   └── main.yml         # Default variables
│       └── tasks/
│           └── main.yml         # Role task definitions
└── crewai-playbook.yml          # Project config (optional)
```

---

## Development

```bash
git clone https://github.com/<your-user>/crewai-playbook.git
cd crewai-playbook

# Install in editable mode
pip install -e .

# Run tests
pip install pytest
pytest -v

# Build wheel
pip install build
python -m build
```

All 106+ tests validate:
- Playbook parsing (syntax, structure, variables)
- Executor orchestration (sequential, hierarchical, tags, limits)
- Task execution (retry, until, when, register, src/dest)
- Block/rescue/always error handling
- Handler/notify lifecycle
- Role loading and variable precedence
- CLI flags and scaffold generation

---

## Why crewai-playbook?

If you know Ansible, you already know how to orchestrate crewAI agents. The same mental model applies:

| Ansible | crewai-playbook |
|---------|----------------|
| `hosts:` | `agents:` |
| `tasks:` | `tasks:` |
| `block:`/`rescue:`/`always:` | `block:`/`rescue:`/`always:` |
| `handlers:`/`notify:` | `handlers:`/`notify:` |
| `roles:` | `roles:` |
| `vars:` | `vars:` |
| `gather_facts:` | `gather_facts:` |
| `-e` extra vars | `-e` extra vars |
| `--check` | `--check` |
| `--tags`/`--skip-tags` | `--tags`/`--skip-tags` |
| `--limit` | `--limit` |

---

## License

[MIT](LICENSE)

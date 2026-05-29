# crewai-playbook

`crewai-playbook` is a YAML-driven CLI tool that orchestrates
[crewAI](https://github.com/joaomdmoura/crewAI) agents using Ansible-compatible
playbook syntax. Write your agent workflows in YAML instead of Python.

## Philosophy

- **YAML-Driven** — All orchestration logic lives in YAML playbooks. No Python
  code required for common workflows.
- **Ansible-Compatible** — The CLI and playbook syntax mirror
  `ansible-playbook`: familiar flags (`--check`, `--tags`, `--syntax-check`,
  `--limit`, `-e`), familiar structure (plays, tasks, roles, handlers,
  block/rescue/always).
- **Convention over Configuration** — Sensible defaults (`gather_facts: true`,
  `become: false`, `config/agents.yaml`).
- **Safety First** — `--check` mode previews execution without LLM calls.
  `--syntax-check` validates playbooks before running.

## How It Works

1. Define agents in `config/agents.yaml`
2. Write a playbook YAML file describing what agents should do
3. Run `crewai-playbook run playbook.yml`

The tool parses the playbook, resolves agent definitions, and executes tasks
through crewAI's Python API — no direct LLM interaction needed from the user.

## Key Concepts

| Concept | Ansible | crewai-playbook |
|---------|---------|-----------------|
| Inventory | `hosts.ini` | `config/agents.yaml` |
| Remote nodes | Hosts | AI Agents |
| Control node | Ansible controller | Leader agent (`leader: true`) |
| Module | Built-in modules | Task descriptions |
| Play | Play with hosts | Play with agents |
| Facts | `gather_facts` | `gather_facts` |
| Role | Reusable tasks | Reusable agent task groups |
| Handler | `notify`/handler | `notify`/handler |

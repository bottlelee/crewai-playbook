# CLI Reference

## Usage

```bash
crewai-playbook [OPTIONS] COMMAND [ARGS]...
```

## Global Options

| Flag | Description |
|------|-------------|
| `--version`, `-V` | Show version and exit |
| `--help` | Show help and exit |

## Commands

### `run`

Execute a playbook.

```bash
crewai-playbook run [OPTIONS] PLAYBOOK
```

| Flag | Description |
|------|-------------|
| `--check` | Dry-run: parse playbook, report planned actions, **no LLM calls** |
| `--diff` | With `--check`, show expected file diffs |
| `--syntax-check` | Validate playbook YAML and variable references, then exit |
| `--tags TEXT` | Only run tasks with these tags (can be specified multiple times) |
| `--skip-tags TEXT` | Skip tasks with these tags (can be specified multiple times) |
| `--list-tasks` | List all tasks in the playbook and exit |
| `--list-tags` | List all tags in the playbook and exit |
| `--limit TEXT` | Limit execution to specific agents (name or `@group`) |
| `-e`, `--extra-vars TEXT` | Set additional variables (`key=value`) |
| `-v` | Increase verbosity (stackable: `-v`, `-vv`, `-vvv`) |
| `-i`, `--inventory TEXT` | Path to agent inventory file (default: `config/agents.yaml`) |

### `init`

Scaffold a new project directory.

```bash
crewai-playbook init [PATH]
```

If `PATH` is omitted, scaffolds the current directory.

### `lint`

Validate a playbook without executing it.

```bash
crewai-playbook lint [OPTIONS] PLAYBOOK
```

Checks for:
- Empty play names
- Missing or empty agents lists
- Undefined agent references
- Empty group references
- Duplicate role references

| Flag | Description |
|------|-------------|
| `-i`, `--inventory TEXT` | Path to agent inventory file |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CREWAI_PLAYBOOK_INVENTORY` | Default path to agent inventory file |
| `CREWAI_PLAYBOOK_CONFIG` | Path to `crewai-playbook.yml` project config |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid playbook, syntax check failure, lint failure) |
| 2 | Help displayed (typer internal) |

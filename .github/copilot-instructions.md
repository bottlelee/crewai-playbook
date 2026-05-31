# crewai-playbook Copilot Instructions

## Build, Test, and Lint Commands

```bash
# Install in editable mode
pip install -e .

# Run all tests
pytest -v

# Run single test module
pytest tests/unit/test_parser.py -v
pytest tests/unit/test_executor.py -v
pytest tests/unit/test_cli.py -v

# Build distribution
python -m build
```

## High-Level Architecture

**Three-layer orchestrator for crewAI agents:**

1. **CLI Layer** (`src/crewai_playbook/cli/`) - Typer-based commands (`run`, `init`, `lint`) that parse arguments and delegate to core
2. **Core Layer** (`src/crewai_playbook/core/`) - Business logic:
   - `parser.py`: YAML parsing with validation, error messages reference playbook/line numbers
   - `executor.py`: Main orchestration loop - iterates plays, gathers facts, executes tasks/blocks, fires handlers
   - `inventory.py`: Agent definition resolution from YAML
   - `runner.py`: crewAI Process management (sequential vs hierarchical)
3. **Module Layer** (`src/crewai_playbook/modules/`) - Execution units:
   - `task.py`: Task execution with retry/delay, when/until conditions, register vars
   - `block.py`: Block/rescue/always execution
   - `handler.py`: Handler notification and lifecycle
   - `role.py`: Role task loading and variable resolution
   - `facts.py`: Environment introspection
   - `tools.py`: crewAI Tool integration
   - `debug.py`: Debug command for variable inspection
4. **Models Layer** (`src/crewai_playbook/models/`) - Pydantic schemas for all YAML structures (Task, Block, Handler, Role, Play, Playbook, AgentDefinition)
5. **Utils Layer** (`src/crewai_playbook/utils/`) - Configuration, variable resolution with precedence, custom errors

**Key patterns:**
- Parser errors include context: `ParseError(f"play #{index} task #{i + 1} missing required key(s): {missing}")`
- Executor uses variable precedence: Role defaults < project config < group_vars < playbook vars < extra vars
- Magic variables are injected for templates: `playbook_dir`, `inventory_file`, `ansible_check_mode`, etc.

## Key Conventions

**Ansible compatibility mirrors:**
- `hosts:` → `agents:` in plays
- `gather_facts:` → `gather_facts:` (default: true)
- `block:`/`rescue:`/`always:` → Block execution
- `notify:`/`handlers:` → Handler lifecycle
- `roles:` → Role loading
- `-e` extra vars → Runtime variable override

**Process modes:**
- `sequential`: Tasks run one at a time
- `hierarchical`: Leader agent delegates to crew members (use `leader: true` in agent definition)

**Variable templating:**
- Use `{{ var }}` syntax in task descriptions
- Resolve using `resolve_vars()` from `utils.vars`
- Extra vars (`-e key=value`) override all other sources

**Check mode:**
- `--check`: Preview execution without LLM calls (dry-run)
- `--check --diff`: Show expected file diffs
- Validators check output length/format/content before accepting

**Agent definition:**
```yaml
agents:
  researcher:
    role: "Research Specialist"
    goal: "Find and synthesize information"
    backstory: "Expert researcher"
    llm: "ollama/gemma4:latest"
    groups: ["default", "research"]
```

## Project Structure

```
src/crewai_playbook/
├── cli/              # Typer CLI commands
├── core/             # Parser, executor, inventory, runner
├── modules/          # Task/block/handler/role/facts/debug execution
├── models/           # Pydantic schemas (Task, Play, Playbook, etc.)
├── utils/            # Config, variable resolution, errors
└── resources/        # Default templates, schemas
```

## Existing Documentation

- **Constitution** (`.specify/memory/constitution.md`): Core principles (YAML-driven, Ansible-compatible, separation of concerns, idempotency)
- **README** (`README.md`): User guide with examples
- **CLI Reference** (`docs/crewai_playbook/cli-reference.md`): All CLI flags and options
- **Overview** (`docs/crewai_playbook/overview.md`): High-level concepts
- **AGENTS.md**: Speckit runtime guidance
# Getting Started

## Installation

```bash
pip install crewai-playbook
```

Requires Python 3.10+ and crewAI.

## Quick Start

### 1. Scaffold a project

```bash
crewai-playbook init my-project
cd my-project
```

Creates:

```
my-project/
├── config/agents.yaml       # Define your agents here
├── playbooks/example.yml    # Sample playbook
├── roles/                   # Reusable role tasks
├── group_vars/              # Group-level variables
├── inventory/               # Inventory overrides
├── .gitignore
└── crewai-playbook.yml      # Project configuration
```

### 2. Define agents

Edit `config/agents.yaml`:

```yaml
agents:
  manager:
    role: "Project Manager"
    goal: "Coordinate agents and synthesize results"
    backstory: "Experienced team lead."
    leader: true
    groups: ["default"]
    llm: "ollama/gemma4:latest"  # or "gpt-4", "claude-3-opus", etc.
  researcher:
    role: "Research Specialist"
    goal: "Find and synthesize relevant information"
    backstory: "Expert researcher with years of experience."
    groups: ["default"]
    llm: "ollama/gemma4:latest"
  writer:
    role: "Content Writer"
    goal: "Transform research into clear content"
    backstory: "Professional technical writer."
    groups: ["default"]
    llm: "ollama/gemma4:latest"
```

### 3. Write a playbook

Create `playbooks/research.yml`:

```yaml
- name: "Research Pipeline"
  agents:
    - researcher
    - writer
  tasks:
    - name: "Research topic"
      agents:
        - researcher
      task: "Research the topic 'AI trends'"
      register: research_output

    - name: "Write summary"
      agents:
        - writer
      task: "Summarize the research: {{ research_output }}"
      when: research_output is defined
      dest: "/tmp/summary.md"
```

### 4. Validate and run

```bash
# Validate syntax
crewai-playbook --syntax-check playbooks/research.yml

# Dry-run (no LLM calls)
crewai-playbook --check playbooks/research.yml

# Execute
crewai-playbook run playbooks/research.yml

# Run with extra variables
crewai-playbook run playbooks/research.yml -e "topic=Quantum Computing"
```

## Next Steps

- See [Playbook Syntax](playbook-syntax.md) for the full YAML reference
- See [CLI Reference](cli-reference.md) for all available flags
- See [Roles](roles.md) for reusable task composition
- See [Example Playbook](example.yml) for a complete demo

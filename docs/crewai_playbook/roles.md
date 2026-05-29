# Roles

Roles provide reusable task composition, mirroring Ansible's role system.

## Directory Structure

```
roles/
├── research/
│   ├── defaults/
│   │   └── main.yml       # Default variables
│   └── tasks/
│       └── main.yml       # Task definitions
└── write/
    ├── defaults/
    │   └── main.yml
    └── tasks/
        └── main.yml
```

## Default Variables

`roles/research/defaults/main.yml`:

```yaml
topic: "Default topic"
depth: "basic"
```

## Tasks

`roles/research/tasks/main.yml`:

```yaml
- name: "Conduct research"
  agents:
    - researcher
  task: "Research {{ topic }} at {{ depth }} depth"

- name: "Summarize findings"
  agents:
    - researcher
  task: "Summarize the research findings"
```

## Usage in Playbooks

Reference roles in a play:

```yaml
- name: "Research & Write"
  agents:
    - researcher
    - writer
  roles:
    - role: research
      vars:
        topic: "Climate Change"
        depth: "comprehensive"
    - role: write
```

Roles execute in the order listed, before inline `tasks:`.

## Variable Precedence

Playbook role `vars:` override role defaults:

1. Role `defaults/main.yml` (lowest priority)
2. Role `vars:` in playbook (highest priority)

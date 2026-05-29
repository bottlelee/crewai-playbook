# Playbook Syntax Reference

## Overview

A playbook is a YAML list of **plays**. Each play targets a set of **agents**
and defines **tasks** for them to execute.

```yaml
- name: "Play name"
  agents:
    - agent_name
    - @group_name        # All agents in a group
  gather_facts: true      # Default: true
  become: false           # Default: false
  process: sequential     # "sequential" or "hierarchical" (default: sequential)
  vars:                   # Play-level variables
    key: value
  tasks:
    - name: "Task name"
      ...
  handlers:               # Optional
    - name: "Handler"
      tasks: [...]
  roles:                  # Alternative to inline tasks
    - role: role_name
      vars: { ... }
```

## Tasks

### Basic task

```yaml
- name: "Task name"
  agents:
    - agent_name
  task: "Description of what the agent should do"
```

### Task with register

Captures agent output into a variable:

```yaml
- name: "Research"
  agents:
    - researcher
  task: "Find information about X"
  register: research_output
```

The variable `research_output` is available to subsequent tasks.
Additional boolean flags are set: `research_output_is_defined`,
`research_output_succeeded`.

### Task with when

Conditional execution:

```yaml
- name: "Write summary"
  agents:
    - writer
  task: "Summarize findings"
  when: research_output is defined
```

Supported conditions:
- `var is defined` — true if the variable exists
- `var is not defined` — true if the variable does not exist
- `var is succeeded` — true if the task producing the var succeeded
- `false`, `no`, `0` — always skip
- `true`, `yes`, `1` — always run

### Task with until/retries/delay

Retry a task until a condition is met:

```yaml
- name: "Reliable research"
  agents:
    - researcher
  task: "Research topic"
  register: result
  until: "result contains complete"
  retries: 3
  delay: 2
```

The task retries up to 3 times with a 2-second delay until the output
contains "complete".

### Task with src/dest

```yaml
- name: "Process file"
  agents:
    - researcher
  task: "Read and analyze the input file"
  src: "/path/to/input.txt"        # Read into task context
  dest: "/path/to/output.txt"       # Write agent output to file
  register: analysis
```

- `src`: file content is prepended to the task description as context
- `dest`: task output is saved to the file after completion

Both support variable expansion: `src: "{{ data_dir }}/input.txt"`

### Task with notify

Triggers a handler when the task produces output:

```yaml
- name: "Generate report"
  agents:
    - researcher
  task: "Create report"
  notify:
    - Summarize
    - Archive
```

## Blocks

Group tasks with shared error handling:

```yaml
tasks:
  - block:
      - name: "Primary method"
        agents:
          - researcher
        task: "Try primary research"
    rescue:
      - name: "Fallback"
        agents:
          - researcher
        task: "Fall back to secondary method"
    always:
      - name: "Cleanup"
        agents:
          - reviewer
        task: "Log completion status"
```

- **block**: runs first
- **rescue**: runs only if block fails
- **always**: runs regardless of success or failure

## Handlers

Handlers are tasks triggered by `notify` from other tasks. They execute
once at the end of the play, and only if the notifying task produces output.

```yaml
handlers:
  - name: "Summarize"
    tasks:
      - name: "Print summary"
        agents:
          - writer
        task: "Summarize the play results"
```

## Process Modes

### Sequential (default)

Tasks execute one after another, each assigned to specific agents. This is the
simplest mode and works for linear pipelines.

### Hierarchical

When `process: hierarchical`, the **leader agent** (the agent with
`leader: true` in `agents.yaml`) acts as a manager that coordinates task
execution across the other agents. This mode is useful for complex workflows
where a manager should delegate and synthesize results.

```yaml
- name: "Managed Workflow"
  agents:
    - manager      # leader: true in agents.yaml
    - researcher
    - writer
  process: hierarchical
  tasks:
    - name: "Research & Write"
      agents:
        - researcher
      task: "Research topic X"
    - name: "Write article"
      agents:
        - writer
      task: "Write about the research"
```

In hierarchical mode, the manager decides how to assign and sequence work,
potentially running tasks in parallel or in an order it determines optimal.

## Roles

Roles allow reusable task composition. See [Roles](roles.md).

```yaml
roles:
  - role: research
    vars:
      topic: "Climate Change"
  - role: write
```

Role variables merge: role `defaults/main.yml` < role `vars:` in the
playbook.

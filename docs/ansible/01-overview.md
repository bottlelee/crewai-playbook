# Ansible Overview

> Sources: https://docs.ansible.com/ (official docs), GitHub
> Last fetched: 2026-05-29

## What is Ansible?

Ansible is an open-source IT automation engine that automates provisioning, configuration management, application deployment, and orchestration. It uses an agentless architecture (SSH/push-based), requires no agents on managed nodes, and uses YAML for human-readable automation content.

### Key Facts
- **Stars**: ~69,000+ on GitHub
- **Latest Release (ansible-core)**: v2.20.6 (2026-05-18)
- **Latest Ansible Package**: Ansible 9+ (ansible-core 2.16+) requires Python 3.10+ on control node
- **License**: GPLv3
- **Sponsor**: Red Hat
- **Community**: 300+ contributors, weekly newsletter (The Bullhorn)

## Architecture

```
┌──────────────────────────┐
│     Control Node         │
│  (Python 3.10+ required) │
│                          │
│  ┌────────────────────┐  │
│  │  ansible-playbook  │  │
│  └────────┬───────────┘  │
│           │              │
│  ┌────────▼───────────┐  │
│  │  Inventory         │  │
│  │  (static/dynamic)  │  │
│  └────────┬───────────┘  │
│           │              │
│  ┌────────▼───────────┐  │
│  │  Modules (via SSH) │  │
│  └────────┬───────────┘  │
└───────────┼──────────────┘
            │ SSH / WinRM
            ▼
┌──────────────────────────┐
│    Managed Nodes         │
│  (no agent required)     │
│  Python 3.6+ minimum     │
│  /usr/bin/python3        │
└──────────────────────────┘
```

### Key Characteristics
- **Agentless**: Uses SSH (Linux) or WinRM (Windows) — no agents to install
- **Push-based**: Control node pushes config to managed nodes
- **Idempotent**: Running a playbook multiple times produces the same result
- **Declarative**: Describe desired state, not how to achieve it
- **YAML-based**: Human-readable automation language

## Ecosystem Components

| Component | Description |
|-----------|-------------|
| **ansible-core** | Core language, runtime, and built-in modules |
| **Ansible Community** | Full package with curated collections |
| **Ansible Automation Platform** | Red Hat's enterprise subscription (AAP) |
| **Ansible Builder** | Create Execution Environments (container images) |
| **Ansible DevTools** | Linting, testing, and CI/CD tooling |
| **Ansible Galaxy** | Community hub for roles and collections |
| **AWX / Ansible Controller** | Web UI, RBAC, workflow orchestration |

## Core Concepts

- **Playbooks**: YAML files defining automation workflows
- **Inventory**: List of managed nodes (static or dynamic)
- **Modules**: Reusable, standalone units of work (built-in or custom)
- **Roles**: Packageable units of tasks, handlers, variables, templates
- **Collections**: Distributable bundles of roles, modules, and plugins
- **Handlers**: Tasks triggered only when notified by other tasks
- **Templates**: Jinja2 templates for dynamic config files
- **Variables**: Precedence system (20+ levels) for customization
- **Facts**: System information gathered from managed nodes

# Core Concepts

> Sources: https://docs.ansible.com/ansible/latest/index.html, official docs

## Playbooks

Playbooks are YAML files defining automation workflows. They are the foundation of Ansible.

### Structure
```yaml
---
- name: Configure web servers
  hosts: webservers
  become: yes
  vars:
    http_port: 80
    max_clients: 200

  tasks:
    - name: Install nginx
      ansible.builtin.apt:
        name: nginx
        state: present

    - name: Deploy config
      ansible.builtin.template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: restart nginx

  handlers:
    - name: restart nginx
      ansible.builtin.service:
        name: nginx
        state: restarted
```

### Key Elements
- **hosts**: Target host group from inventory
- **become**: Privilege escalation (sudo)
- **tasks**: Ordered list of module executions
- **handlers**: Tasks triggered only on change (via `notify`)
- **vars**: Variables for the play
- **tags**: Labels for selective task execution

## Inventory

Inventory defines the managed nodes. Can be static files or dynamic (from cloud APIs).

### Static Inventory (INI format)
```ini
[webservers]
web1.example.com
web2.example.com

[databases]
db1.example.com

[production:children]
webservers
databases
```

### Static Inventory (YAML format - recommended)
```yaml
all:
  children:
    webservers:
      hosts:
        web1.example.com:
        web2.example.com:
    databases:
      hosts:
        db1.example.com:
```

### Dynamic Inventory
Query cloud providers (AWS EC2, Azure, GCP) or CMDBs automatically:
```yaml
# AWS EC2 dynamic inventory
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1
keyed_groups:
  - key: tags.Environment
    prefix: env
  - key: tags.Role
    prefix: role
```

## Modules

Ansible ships with hundreds of built-in modules. Use FQCN (Fully Qualified Collection Name) for clarity:

| Module | Purpose |
|--------|---------|
| `ansible.builtin.apt` | Package management (Debian/Ubuntu) |
| `ansible.builtin.yum` / `dnf` | Package management (RHEL/Fedora) |
| `ansible.builtin.copy` | Copy files to remote hosts |
| `ansible.builtin.template` | Deploy Jinja2 templated files |
| `ansible.builtin.service` / `systemd` | Service management |
| `ansible.builtin.lineinfile` | Ensure line in file |
| `ansible.builtin.blockinfile` | Manage multi-line blocks |
| `ansible.builtin.file` | File/directory management |
| `ansible.builtin.command` / `shell` | Execute commands (last resort) |
| `ansible.builtin.debug` | Print variables for debugging |
| `ansible.builtin.assert` | Validate conditions |
| `ansible.builtin.set_fact` | Set variables at runtime |

### Module Best Practices
- Always use the dedicated module instead of `command`/`shell`
- If you must use `command`/`shell`, add `creates`, `removes`, or `changed_when`
- Use FQCN (`ansible.builtin.apt` not `apt`) for clarity and avoiding conflicts

## Roles

Roles package tasks, handlers, variables, templates, and files into reusable units.

### Directory Structure
```
roles/
└── nginx/
    ├── defaults/      # Default variables (lowest precedence)
    │   └── main.yml
    ├── vars/          # Override variables
    │   └── main.yml
    ├── tasks/         # Main task list
    │   └── main.yml
    ├── handlers/      # Handlers
    │   └── main.yml
    ├── templates/     # Jinja2 templates
    │   └── nginx.conf.j2
    ├── files/         # Static files to copy
    │   └── index.html
    └── meta/          # Role dependencies
        └── main.yml
```

### Role Best Practices
- **One role, one responsibility**: Install packages vs configure services = separate roles
- **Use `defaults/` for overridable variables**: Lowest precedence, easy for consumers to override
- **Use `vars/` for internal constants**: Higher precedence, not meant to be overridden
- **Support check mode**: Role should not fail under `--check`
- **Be idempotent**: Second run should report no changes

## Collections

Collections are the modern packaging format bundling roles, modules, plugins, and playbooks.

```yaml
# requirements.yml
collections:
  - name: community.general
    version: ">=8.0.0"
  - name: ansible.posix
    version: ">=1.5.0"
  - name: amazon.aws
```

Install: `ansible-galaxy collection install -r requirements.yml`

## Handlers

Handlers are special tasks that run only when notified by other tasks. They run once, at the end of the play, regardless of how many times notified.

```yaml
tasks:
  - name: Update nginx config
    ansible.builtin.template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
    notify: restart nginx

  - name: Update site config
    ansible.builtin.template:
      src: site.conf.j2
      dest: /etc/nginx/sites-enabled/default
    notify: restart nginx

handlers:
  - name: restart nginx
    ansible.builtin.service:
      name: nginx
      state: restarted
```

### Key Handler Rules
- Use `reloaded` when service supports hot reload (NGINX, HAProxy, rsyslog)
- Use `restarted` only when actual process restart is needed (binary upgrade)
- Handlers fire at end of play, in order defined, only once

## Variables and Precedence

Ansible has 20+ levels of variable precedence (lowest to highest):

1. Role defaults (`roles/role/defaults/main.yml`)
2. Inventory group_vars (`inventory/group_vars/all/`)
3. Inventory group_vars per group
4. Inventory host_vars
5. Playbook vars
6. `vars_files`, `vars_prompt`
7. `set_fact` / `register`
8. `include_vars`
9. Role vars (`roles/role/vars/main.yml`)
10. Block vars
11. Task vars
12. `--extra-vars` (`-e`) — highest

### Best Practice
- **Defaults** in role `defaults/`: consumable, overridable
- **Environment values** in inventory `group_vars/`
- **Secrets** in `group_vars/env/vault.yml` (encrypted with Ansible Vault)
- **Avoid** `vars:` in playbooks and `set_fact` for config values — harder to track

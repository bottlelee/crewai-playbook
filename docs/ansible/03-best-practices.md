# Best Practices

> Sources: Red Hat Good Practices for Ansible (GPA), official docs, community production experience (2026)

## Project Structure

### Recommended Directory Layout
```
project/
├── ansible.cfg                    # Project-level config
├── site.yml                       # Main entry point (orchestrator)
├── playbooks/
│   ├── webservers.yml
│   ├── databases.yml
│   └── monitoring.yml
├── roles/
│   ├── common/
│   ├── nginx/
│   └── postgresql/
├── inventory/
│   ├── production/
│   │   ├── hosts.yml
│   │   └── group_vars/
│   │       ├── all/
│   │       │   ├── vars.yml
│   │       │   └── vault.yml
│   │       ├── webservers.yml
│   │       └── databases.yml
│   └── staging/
├── collections/
│   └── requirements.yml
├── scripts/                       # Helper scripts
├── docs/
└── .ansible-lint
```

### Key Principles
- **Structure beats cleverness**: A boring, consistent structure outperforms any clever trick
- **Think in layers**: Inventory defines WHERE, variables define WHAT, roles define HOW
- **Separate environments**: Production and staging should NEVER share inventory files

## Idempotency (Most Important)

The single most important property of a production playbook: running it twice produces the same result as running it once.

### Rules for Idempotency
1. **Prefer built-in modules** over `command`/`shell` — modules are idempotent by design
2. **If you must use `command`/`shell`**, add `creates`, `removes`, or `changed_when`
3. **Use handlers** for service restarts (only restart when config actually changed)
4. **If a task reports "changed" every run**, fix it — that's drift, not idempotency
5. **A tenth run should produce zero `changed` results** when state hasn't drifted

```yaml
# ✅ GOOD: Uses module (idempotent)
- name: Install nginx
  ansible.builtin.apt:
    name: nginx
    state: present

# ✅ GOOD: command with creates guard
- name: Install Node.js
  ansible.builtin.command:
    cmd: /tmp/install_node.sh
    creates: /usr/bin/node

# ❌ BAD: shell without guard (runs every time)
- name: Install Node.js
  ansible.builtin.shell: /tmp/install_node.sh
```

## Playbook Design

### Keep Playbooks Thin
- Playbooks should orchestrate roles, not contain hundreds of tasks
- If a playbook exceeds 100 lines, refactor into roles
- Use `import_playbook` for multi-stage deployments

### Naming Conventions
- Every task MUST have a `name:` — unnamed tasks produce unreadable output
- Use FQCN for all modules (`ansible.builtin.apt`, not `apt`)
- Prefixed variables (role or app name) to avoid collisions
- Task names should describe WHAT, not HOW

```yaml
# ✅ GOOD
- name: Ensure nginx is installed
  ansible.builtin.apt:
    name: nginx
    state: present

# ❌ BAD
- apt: name=nginx state=present
```

### Use Either `tasks` or `roles`, Not Both
In a playbook, prefer one approach per play for clarity.

### Tags Strategy
Use tags for surgical reruns. Tag by component, phase, or risk level:
```yaml
- name: Configure app
  ansible.builtin.template:
    src: app.conf.j2
    dest: /etc/app/app.conf
  tags:
    - app_config
    - high_risk
```

Run subset: `ansible-playbook site.yml --tags app_config`

## Inventory Management

### Environment Separation
```yaml
# ✅ DO: Separate inventory files per environment
inventory/
├── production/
│   └── hosts.yml
├── staging/
│   └── hosts.yml
└── dev/
    └── hosts.yml

# ❌ DON'T: All environments in one file — leads to surprises
```

### Use Dynamic Inventory for Cloud
- Static inventory for on-prem / stable environments
- Dynamic inventory (AWS EC2, Azure, GCP) for cloud environments
- Use tags to differentiate production/staging roles

### Canary Group
Always have a canary group — a tiny subset of prod to target first:
```ini
[prod_canary]
web1.example.com
db1.example.com

[webservers:children]
prod_canary
web2.example.com
web3.example.com
```

## Variable Management

### Variable Precedence (Simplified)
From lowest to highest priority:
1. Role defaults (`roles/role/defaults/main.yml`)
2. Inventory `group_vars`
3. Playbook vars
4. `--extra-vars` (`-e`)

### Rules
- Put defaults in roles, environment-specific values in inventory
- Use `group_vars` for shared config; `host_vars` sparingly (snowflakes are anti-patterns)
- Never hardcode environment-specific values in playbooks
- Validate required variables early with `assert`

```yaml
- name: Pre-flight checks
  ansible.builtin.assert:
    that:
      - app_version is defined
      - db_host is defined
    fail_msg: "Missing required variables"
```

## Security

### Ansible Vault
- All secrets in `group_vars/env/vault.yml` (encrypted)
- Keep non-secret vars in normal `group_vars/env/vars.yml`
- Use separate Vault IDs/keys per environment (dev ≠ prod)
- Never commit plaintext passwords, API keys, or certificates

```bash
# Encrypt a file
ansible-vault encrypt group_vars/production/vault.yml

# Create encrypted variable
ansible-vault encrypt_string 'my_secret' --name 'db_password'
```

### no_log for Sensitive Tasks
```yaml
- name: Configure database password
  ansible.builtin.shell:
    cmd: "psql -c \"ALTER USER app PASSWORD '{{ db_password }}'\""
  no_log: true
```

### Other Security Rules
- Mark tasks with `no_log: true` where secret values might be printed
- Be careful with `debug` — don't print variables that might contain secrets
- Be careful with registered variables from commands (may include sensitive output)

## Testing & Validation

### CI/CD Pipeline
```
ansible-lint → --syntax-check → Molecule tests → Deploy to staging → Deploy to production
```

### Pre-Apply Checks
```bash
# Always run before production apply
ansible-playbook site.yml --check --diff

# Syntax check
ansible-playbook site.yml --syntax-check

# Lint
ansible-lint site.yml

# Limit to one host first (canary)
ansible-playbook site.yml --limit web1.example.com
```

### Molecule for Role Testing
Every role should have Molecule tests using Docker or Vagrant:
```bash
molecule init scenario --driver-name docker
molecule test
```

## Performance Optimization

### ansible.cfg Settings
```ini
[defaults]
# Gather only what you need
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts_cache
fact_caching_timeout = 7200

# SSH optimization
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
pipelining = True

# Parallelism
forks = 50
```

### Selective Fact Gathering
```yaml
- name: Configure app servers
  hosts: appservers
  gather_facts: false
  pre_tasks:
    - name: Gather minimal facts
      ansible.builtin.setup:
        gather_subset:
          - network
          - hardware
```

## Error Handling

### Block/Rescue/Always
```yaml
- name: Deploy application
  block:
    - name: Deploy code
      ansible.builtin.copy:
        src: app-v2.tar.gz
        dest: /opt/app/
    - name: Restart service
      ansible.builtin.service:
        name: app
        state: restarted
  rescue:
    - name: Rollback on failure
      ansible.builtin.include_role:
        name: app
        tasks_from: rollback
  always:
    - name: Notify result
      ansible.builtin.uri:
        url: "{{ slack_webhook }}"
```

### max_fail_percentage
```yaml
- hosts: webservers
  max_fail_percentage: 0   # Stop if ANY host fails
  serial: 3                 # Roll 3 at a time
```

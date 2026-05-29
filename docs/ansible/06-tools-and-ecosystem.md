# Tools, Ecosystem & Resources

> Source: https://docs.ansible.com/, Ansible Galaxy, community

## Ansible Ecosystem

### Ansible Core
The foundational runtime and language:
- **Current**: ansible-core 2.20.6 (2026-05-18)
- **Requires**: Python 3.10+ on control node
- **Managed nodes**: Python 3.6+ minimum
- **Install**: `pip install ansible-core` or `pip install ansible` (full package)

### Ansible Community Package
Full package with curated collections:
- `pip install ansible` — includes ansible-core + popular collections
- ~80+ included collections

### Ansible Automation Platform (AAP)
Red Hat's enterprise offering:
- Ansible Controller (web UI, RBAC, workflows)
- Execution Environments (containerized runtimes)
- Automation Analytics and dashboards
- Certified content collections
- Support SLA

### Ansible Builder
Create custom Execution Environments (containers):
```bash
ansible-builder build --tag my-ee:latest
```
EEs bundle Ansible, collections, dependencies, and tools into reproducible container images.

### Ansible DevTools
Integrated toolkit for content creation:
- `ansible-lint` — Static analysis and linting
- `molecule` — Role testing framework
- `ansible-test` — CI/CD test runner

## Core Tools

### ansible-lint
Static analysis for playbooks and roles:
```bash
ansible-lint site.yml
ansible-lint roles/nginx/
```
Catches: missing task names, non-FQCN modules, deprecated syntax, idempotency issues.

Configuration (`.ansible-lint`):
```yaml
skip_list:
  - fqcn-builtins
warn_list:
  - experimental
```

### Molecule
Role testing framework with driver support:
```bash
molecule init role myrole --driver-name docker
molecule test
```
Drivers: Docker, Podman, Vagrant, EC2, Azure, OpenStack.

### ansible-test
CI/CD test runner used by ansible-core development and collection maintainers.

## Collections

### Essential Collections
| Collection | Purpose |
|------------|---------|
| `ansible.builtin` | Core modules (always available) |
| `community.general` | Community-maintained modules |
| `ansible.posix` | POSIX-specific modules (SELinux, mount, ACL) |
| `community.docker` | Docker container management |
| `amazon.aws` | AWS EC2, S3, RDS, etc. |
| `azure.azcollection` | Azure services |
| `google.cloud` | GCP services |
| `community.kubernetes` / `kubernetes.core` | Kubernetes management |
| `ansible.windows` | Windows modules |
| `community.vmware` | VMware management |
| `community.network` | Network device management |

### Install Collections
```yaml
# collections/requirements.yml
---
collections:
  - name: community.general
    version: ">=8.0.0"
  - name: ansible.posix
    version: ">=1.5.0"
  - name: amazon.aws
    source: https://galaxy.ansible.com
```

```bash
ansible-galaxy collection install -r collections/requirements.yml
```

## Ansible Galaxy
Community hub for roles and collections: https://galaxy.ansible.com

### Install Roles
```bash
ansible-galaxy role install geerlingguy.nginx
```

### Role Requirements File
```yaml
# roles/requirements.yml
---
roles:
  - name: geerlingguy.nginx
    version: "3.0.0"
  - name: geerlingguy.postgresql
    version: "2.0.0"
```

## Connection Plugins

| Plugin | Protocol | Use Case |
|--------|----------|----------|
| `ansible.builtin.ssh` | SSH | Default for Linux/Unix |
| `ansible.builtin.winrm` | WinRM | Windows management |
| `community.vmware.vmware_tools` | VMware API | VM guest operations |
| `ansible.builtin.local` | Local | Run on control node |
| `kubernetes.core.kubectl` | K8s API | Kubernetes pods |

## Execution Environments (EE)
Container images that serve as Ansible control nodes:
- Reproducible — same dependencies every run
- Portable — ship EE between team members
- Isolated — no host system conflicts

```yaml
# execution-environment.yml
---
version: 3

images:
  base_image:
    name: registry.access.redhat.com/ansible-automation-platform-25/ee-minimal-rhel9:latest

dependencies:
  galaxy: collections/requirements.yml
  python: requirements.txt
  system: packages.txt
```

## Ansible Vault
Built-in secret encryption:
```bash
ansible-vault create group_vars/production/vault.yml
ansible-vault encrypt file.yml
ansible-vault decrypt file.yml --output=decrypted.yml
ansible-vault view file.yml
ansible-vault rekey file.yml        # Change password
```

Usage:
```bash
ansible-playbook site.yml --ask-vault-pass
ansible-playbook site.yml --vault-password-file ~/.vault_pass
```

## Testing & CI/CD Tools

### Minimal CI Pipeline
```yaml
# .github/workflows/ansible.yml
name: Ansible CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install Ansible
        run: pip install ansible-lint ansible-core
      - name: Syntax check
        run: ansible-playbook site.yml --syntax-check
      - name: Lint
        run: ansible-lint site.yml
      - name: Dry run
        run: ansible-playbook site.yml --check --diff --limit localhost
```

## Monitoring & Observability

### What to Track
- Playbook run duration
- Success/failure rate per task
- Host reachability
- Configuration drift (check mode results)
- Secret rotation verification

### AAP Automation Analytics
Built-in with Ansible Automation Platform:
- Job run history
- Host metrics
- Task completion rates
- Organization/team dashboards

## Official Resources
- **Docs**: https://docs.ansible.com/
- **GitHub**: https://github.com/ansible/ansible
- **Galaxy**: https://galaxy.ansible.com
- **Forum**: https://forum.ansible.com/
- **Bullhorn Newsletter**: https://forum.ansible.com/c/news/bullhorn/17
- **Red Hat AAP Docs**: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/
- **Ansible Blog**: https://www.ansible.com/blog
- **Good Practices (GPA)**: https://redhat-cop.github.io/automation-good-practices/
- **Molecule**: https://ansible.readthedocs.io/projects/molecule/

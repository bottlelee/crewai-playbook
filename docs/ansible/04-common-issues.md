# Common Issues, Bugs & Fixes

> Sources: GitHub Issues (ansible/ansible), community reports (2026)

## 1. SSH Connections Fail Under High Parallelism

**Issue**: #86658 - With forks > 100, SSH connections randomly fail: `"SSH session not active"`. Re-running typically succeeds on different hosts.

**Root Cause**: Race condition in paramiko connection plugin when many concurrent SSH sessions are established.

**Fix**: 
- Reduce `forks` in `ansible.cfg` to a lower number (e.g., 50)
- Update to ansible-core 2.20+ which has mitigations (PR #86659)
- Note: paramiko connection plugin is deprecated, pending removal in 2.21

---

## 2. apt Module Fails on Ubuntu 20.04 with Python 3.9

**Issue**: #86737 - Ubuntu 20.04 ships Python 3.8. Ansible >= 2.14.0 drops Python 3.8 support. Installing Python 3.9 causes `python3-apt` import error since it's not available for Python 3.9.

**Error**:
```
Could not import the python3-apt module using /usr/bin/python3.9
```

**Fix**:
- Option A: Use ansible-core 2.17 or earlier (last version supporting Python 3.8)
- Option B: Install `python3-apt` for Python 3.9 manually
- Option C: Upgrade Ubuntu to 22.04+ (ships Python 3.10+)

---

## 3. copy Module - "A worker was found in a dead state"

**Issue**: #86946 - `copy` module fails on illumos/Solaris systems with worker dead state error.

**Error**:
```
[ERROR]: A worker was found in a dead state
AssertionError: can only test a child process
```

**Root Cause**: Zone resource controls or process contracts on illumos killing child processes. SIGWINCH signal correlated with failures.

**Workaround**: 
- Check zone resource caps: `prctl $$`
- Use dtrace to identify signal source:
  ```
  dtrace -qn 'proc:::signal-send /args[2] == 15 || args[2] == 2/ { printf(...) }'
  ```
- Reduce parallelism or patch from the issue thread

---

## 4. PowerShell Modules Fail Without Pipelining Support

**Issue**: #86397 - PowerShell modules fail with `community.vmware.vmware_tools` and similar non-pipelining connections.

**Error**:
```
Failed to create temporary directory. Consider changing the remote tmp path in ansible.cfg to a path rooted in "/tmp"
```

**Root Cause**: The `_mkdtemp2` function in `plugins/shell/powershell.py` always uses pipelining regardless of whether the connection plugin supports it.

**Fix**: PR #86619 (merged in 2.20.4) — Added fallback to legacy `mkdtemp` when connection doesn't support pipelining.

---

## 5. WinRM FQCN Inconsistency

**Issue**: #86907 - Using `ansible.builtin.winrm` (FQCN) doesn't respect `ansible_winrm_server_cert_validation=ignore`, but `winrm` (short name) does.

**Error**:
```
SSL: CERTIFICATE_VERIFY_FAILED - certificate verify failed: self-signed certificate
```

**Root Cause**: Bug fixed in 2.18 via PR #83353, backported to 2.16. Affects versions before 2.16.

**Fix**: Update to ansible-core 2.16+ or use short name `winrm` as workaround.

---

## 6. Interpreter Discovery Caching Broken with `delegate_to`

**Issue**: #86517 - When a host is first encountered via `delegate_to`, interpreter discovery results aren't cached, causing re-discovery on every delegated task.

**Symptom**: Delegate_to tasks show interpreter discovery on EVERY run instead of once.

**Fix**: PR #86520 in progress. The strategy needs to call `self._variable_manager.set_host_facts` to cache interpreter discovery for delegated hosts.

---

## 7. python3-apt Auto-Install Doesn't Mark Task as Changed

**Issue**: #86471 - When `auto_install_module_deps` triggers a python3-apt install, the task reports `changed: false`.

**Root Cause**: The module is respawned after installing deps, and the respawned instance doesn't know about the preceding install.

**Resolution**: Determined to be intentional behavior — installing module dependencies is tangential to the module's actual purpose. Not considered a bug.

---

## 8. ansiballz FileNotFoundError During exit_json()

**Issue**: #86738 - `/tmp` mount changes (e.g., `systemd` managing `tmp.mount`) or `noexec` mounts cause ansiballz zip payload deletion before result serialization.

**Error**: `FileNotFoundError` for `_internal/_json` during `exit_json()`

**Root Cause**: Two related bugs:
1. Lazy import of JSON serialization profile reads from zip after cleanup
2. `/tmp` unmount changes mid-execution make zip inaccessible

**Fix**: PR #86739:
- Eager-load JSON profile before module execution (caches in `sys.modules`)
- Use `scriptdir` (under `remote_tmp`) instead of `/tmp` for zip extraction

---

## 9. dnf Package Install with Architecture (No Version)

**Issue**: Fixed in 2.20.x — `dnf` fails when specifying package architecture without version (e.g., `libgcc.i686`) when another arch of same package is already installed.

**Fix**: Update to ansible-core 2.20.4+ (fix in CHANGELOG-v2.20.rst)

---

## 10. `import_tasks` Keyword Validation Issues

**Issue**: Fixed in 2.20.x — Keywords incorrectly validated on `import_tasks`, and tags double-applied from `import_tasks` onto blocks.

**Affected**: Play tags prevented executing notified handlers (#85475), import_tasks keyword validation (#85855, #85856).

**Fix**: Update to ansible-core 2.20.4+.

---

## 11. copy Module "changed" False for Local Directory

**Issue**: Fixed in 2.20.x — When copying a single-file local directory as source, `changed` was `false` even when the source was actually copied.

**Fix**: Update to ansible-core 2.20.4+.

---

## 12. rpm_key PGP v6 Key Support

**Issue**: Fixed in 2.20.x — `rpm_key` module failed with PGP v6 keys because it used external `gpg` utility instead of librpm library API.

**Fix**: Updated to use librpm library API directly (#86157), included in 2.20.4+.

---

## 13. YAML Loading Traceback with Pure Python

**Issue**: Fixed in 2.20.x — Traceback when parsing YAML strings (not files) using the pure Python implementation of PyYAML.

**Fix**: Update to ansible-core 2.20.4+.

---

## 14. async Delegated Task Interpreter Discovery

**Issue**: Fixed in 2.20.x — Interpreter discovery fails on delegated `async` tasks (#86491).

**Fix**: Update to ansible-core 2.20.4+.

---

## Common StackOverflow Issues

### "Failed to connect via SSH: Connection refused"
**Causes**: SSH not running, wrong port, firewall, host key mismatch
**Fix**: Verify `ansible_host`, `ansible_port`, `ansible_user`, `ansible_ssh_private_key_file`

### "ERROR! The field 'hosts' is required"
**Cause**: Missing `hosts:` line in playbook or mis-indented YAML
**Fix**: Ensure `hosts:` is at the play level (not task level) and YAML is valid

### "ERROR! 'become' is not a valid attribute for a Task"
**Cause**: Indentation error — `become:` placed under a task instead of play level
**Fix**: Indent `become:` at the play level or use `become: yes` per task

### "ModuleNotFoundError: No module named 'ansible'"
**Cause**: Running ansible outside the virtual environment or before installing
**Fix**: Activate venv: `source .venv/bin/activate` or install: `pip install ansible`

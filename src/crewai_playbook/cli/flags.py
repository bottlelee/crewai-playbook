"""Shared CLI flag definitions for crewai-playbook."""

from __future__ import annotations

from typing import List, Optional

CHECK_HELP = "Do not execute any agents; instead, report what would be done."
DIFF_HELP = "When used with --check, show diff of expected file changes."
SYNTAX_HELP = "Parse the playbook and validate variable references without executing."
TAGS_HELP = "Only run tasks tagged with these values."
SKIP_TAGS_HELP = "Skip tasks tagged with these values."
LIST_TASKS_HELP = "List all tasks in the playbook without executing."
LIST_TAGS_HELP = "List all tags in the playbook without executing."
LIMIT_HELP = "Limit execution to specific agents (by name or @group)."
EXTRA_VARS_HELP = "Set additional variables (key=value or @file.yml)."
VERBOSE_HELP = "Increase verbosity level (-v, -vv, -vvv)."
INVENTORY_HELP = "Path to agent inventory file (default: config/agents.yaml)."

from pathlib import Path

import pytest

from crewai_playbook.modules.role import load_role_tasks, resolve_role_tasks
from crewai_playbook.models.playbook import Role
from crewai_playbook.utils.errors import RoleError

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestLoadRoleTasks:
    def test_loads_role_tasks_and_defaults(self):
        tasks, merged_vars = load_role_tasks(
            "research", roles_path=str(FIXTURES / "roles")
        )
        assert len(tasks) == 2
        assert tasks[0].name == "Conduct research"
        assert tasks[1].name == "Summarize findings"
        assert merged_vars["topic"] == "default topic"
        assert merged_vars["depth"] == "basic"

    def test_role_vars_override_defaults(self):
        tasks, merged_vars = load_role_tasks(
            "research",
            roles_path=str(FIXTURES / "roles"),
            role_vars={"topic": "AI", "depth": "deep"},
        )
        assert merged_vars["topic"] == "AI"
        assert merged_vars["depth"] == "deep"

    def test_missing_role_raises(self):
        with pytest.raises(RoleError, match="not found"):
            load_role_tasks("nonexistent", roles_path=str(FIXTURES / "roles"))

    def test_empty_roles_path_raises(self):
        with pytest.raises(RoleError):
            load_role_tasks("research", roles_path="/nonexistent/path")

    def test_write_role_without_overrides(self):
        tasks, merged_vars = load_role_tasks(
            "write", roles_path=str(FIXTURES / "roles")
        )
        assert len(tasks) == 1
        assert tasks[0].name == "Write content"
        assert "format" in merged_vars
        assert merged_vars["format"] == "markdown"

    def test_write_role_with_override(self):
        tasks, merged_vars = load_role_tasks(
            "write",
            roles_path=str(FIXTURES / "roles"),
            role_vars={"format": "html"},
        )
        assert merged_vars["format"] == "html"


class TestResolveRoleTasks:
    def test_resolve_multiple_roles(self):
        roles = [
            Role(role="research", vars={"topic": "AI"}),
            Role(role="write"),
        ]
        result = resolve_role_tasks(roles, roles_path=str(FIXTURES / "roles"))
        assert len(result) == 3  # 2 from research + 1 from write

    def test_task_vars_merged(self):
        roles = [Role(role="research", vars={"topic": "Machine Learning"})]
        result = resolve_role_tasks(roles, roles_path=str(FIXTURES / "roles"))
        task, merged_vars = result[0]
        assert merged_vars["topic"] == "Machine Learning"
        assert merged_vars["depth"] == "basic"  # from defaults

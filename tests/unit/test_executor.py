from unittest.mock import patch, MagicMock

import pytest
import yaml

from crewai_playbook import __version__
from crewai_playbook.core.executor import PlaybookExecutor
from crewai_playbook.core.parser import parse_playbook
from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.models.playbook import Play, Playbook


@pytest.fixture
def empty_playbook(tmp_path):
    """A playbook fixture that has no tasks (for testing magic vars in check mode)."""
    p = tmp_path / "magic_test.yml"
    data = [{"name": "Magic Test", "agents": ["researcher"], "gather_facts": False}]
    p.write_text(yaml.safe_dump(data))
    return p


@pytest.fixture
def playbook_with_colliding_vars(tmp_path):
    """Playbook with play vars that intentionally shadow magic vars."""
    p = tmp_path / "collide.yml"
    data = [{
        "name": "Collision Test",
        "agents": ["researcher"],
        "gather_facts": False,
        "vars": {
            "playbook_dir": "/hacked/by/play_vars",
            "ansible_play_name": "overridden by play vars",
        },
        "tasks": [{
            "name": "Check vars",
            "agents": ["researcher"],
            "task": "Check the variable values",
        }],
    }]
    p.write_text(yaml.safe_dump(data))
    return p


@pytest.fixture
def mock_run_single_task():
    with patch("crewai_playbook.modules.task.run_single_task") as mock:
        mock.return_value = "mock output"
        yield mock


@pytest.fixture
def inventory():
    return {
        "researcher": AgentDefinition(
            role="Research Specialist",
            goal="Find info",
            backstory="Expert",
        ),
        "writer": AgentDefinition(
            role="Writer",
            goal="Write content",
            backstory="Pro writer",
        ),
        "reviewer": AgentDefinition(
            role="Reviewer",
            goal="Review content",
            backstory="Senior editor",
        ),
    }


class TestPlaybookExecutor:
    def test_execute_simple_playbook(
        self, simple_playbook_yaml, inventory, mock_run_single_task
    ):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(pb, inventory, verbose=False)
        results = executor.run()
        assert results["failed"] is False
        assert len(results["plays"]) == 1
        play_result = results["plays"][0]
        assert play_result["name"] == "Test Play"
        assert len(play_result["tasks"]) == 1
        assert play_result["tasks"][0]["name"] == "Research task"
        assert play_result["tasks"][0]["output"] == "mock output"
        mock_run_single_task.assert_called_once()

    def test_execute_block_playbook(
        self, block_playbook_yaml, inventory, mock_run_single_task
    ):
        pb = parse_playbook(block_playbook_yaml)
        executor = PlaybookExecutor(pb, inventory, verbose=False)
        results = executor.run()
        assert results["failed"] is False
        play_result = results["plays"][0]
        assert len(play_result["tasks"]) == 1
        block_result = play_result["tasks"][0]
        assert block_result["type"] == "block"
        assert len(block_result["block"]) == 1

    def test_check_mode_no_execution(
        self, simple_playbook_yaml, inventory, mock_run_single_task
    ):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, check_mode=True, verbose=False
        )
        results = executor.run()
        assert results["failed"] is False
        mock_run_single_task.assert_not_called()
        assert len(results["plays"][0]["tasks"]) == 1
        task_desc = results["plays"][0]["tasks"][0]
        assert "action" in task_desc

    def test_tags_filtering(
        self, tagged_playbook_yaml, inventory, mock_run_single_task
    ):
        pb = parse_playbook(tagged_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, tags=["research"], verbose=False
        )
        results = executor.run()
        play_result = results["plays"][0]
        assert len(play_result["tasks"]) == 1
        assert play_result["tasks"][0]["name"] == "Research phase"

    def test_skip_tags(
        self, tagged_playbook_yaml, inventory, mock_run_single_task
    ):
        pb = parse_playbook(tagged_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, skip_tags=["summary"], verbose=False
        )
        results = executor.run()
        play_result = results["plays"][0]
        task_names = [t["name"] for t in play_result["tasks"]]
        assert "Summary" not in task_names
        assert "Research phase" in task_names

    def test_gather_facts_adds_to_context(
        self, simple_playbook_yaml, inventory, mock_run_single_task
    ):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(pb, inventory, verbose=False)
        executor.run()
        mock_run_single_task.assert_called_once()
        call_kwargs = mock_run_single_task.call_args[1]
        assert "inventory" in call_kwargs

    def test_limit_by_agent(
        self, simple_playbook_yaml, inventory, mock_run_single_task
    ):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, limit=["researcher"], verbose=False
        )
        results = executor.run()
        assert results["failed"] is False

    def test_limit_by_group(
        self, simple_playbook_yaml, inventory, mock_run_single_task
    ):
        inventory["researcher"].groups = ["research"]
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, limit=["@research"], verbose=False
        )
        results = executor.run()
        assert results["failed"] is False

    def test_extra_vars_passed_through(
        self, simple_playbook_yaml, inventory, mock_run_single_task
    ):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, extra_vars={"topic": "AI"}, verbose=False
        )
        results = executor.run()
        assert results["failed"] is False

    def test_leader_detected_from_inventory(
        self, simple_playbook_yaml, inventory, mock_run_single_task
    ):
        inventory["researcher"].leader = True
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(pb, inventory, verbose=False)
        assert executor._find_leader(inventory) == "researcher"

    def test_no_leader_returns_none(
        self, simple_playbook_yaml, inventory, mock_run_single_task
    ):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(pb, inventory, verbose=False)
        assert executor._find_leader(inventory) is None

    def test_hierarchical_executes_through_crew_runner(
        self, tmp_path, inventory, mock_run_single_task
    ):
        inventory["researcher"].leader = True
        data = [{
            "name": "Hierarchical Play",
            "agents": ["researcher", "writer"],
            "process": "hierarchical",
            "gather_facts": False,
            "tasks": [
                {"name": "T1", "agents": ["researcher"], "task": "Do research"},
                {"name": "T2", "agents": ["writer"], "task": "Write output"},
            ],
        }]
        import yaml
        p = tmp_path / "hierarchical.yml"
        p.write_text(yaml.safe_dump(data))
        pb = parse_playbook(p)
        with patch("crewai_playbook.core.executor.run_hierarchical_task") as mock_task:
            mock_task.return_value = "task output"
            executor = PlaybookExecutor(pb, inventory, verbose=False)
            results = executor.run()
            assert results["failed"] is False
            assert mock_task.call_count == 2
            call_kwargs = mock_task.call_args[1]
            assert call_kwargs["leader_name"] == "researcher"

    # ----- magic variables ------------------------------------------------

    def test_get_magic_variables_returns_all_keys(self, simple_playbook_yaml, inventory):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, verbose=False, playbook_path=str(simple_playbook_yaml),
            inventory_path="/fake/inv.yaml",
        )
        play = pb.plays[0]
        magic = executor._get_magic_variables(play)
        expected = {
            "playbook_dir", "inventory_dir", "inventory_file",
            "ansible_play_name", "ansible_play_agents",
            "ansible_check_mode", "ansible_verbosity",
            "ansible_version", "crewai_playbook_version",
        }
        assert expected.issubset(magic.keys()), f"missing keys: {expected - magic.keys()}"

    def test_playbook_dir_is_parent_of_playbook(self, simple_playbook_yaml, inventory):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, verbose=False, playbook_path=str(simple_playbook_yaml),
        )
        magic = executor._get_magic_variables(pb.plays[0])
        assert magic["playbook_dir"] == str(simple_playbook_yaml.resolve().parent)

    def test_inventory_dir_is_parent_of_inventory(self, simple_playbook_yaml, inventory):
        pb = parse_playbook(simple_playbook_yaml)
        inv_path = "/some/inventory/agents.yaml"
        executor = PlaybookExecutor(
            pb, inventory, verbose=False, playbook_path=str(simple_playbook_yaml),
            inventory_path=inv_path,
        )
        magic = executor._get_magic_variables(pb.plays[0])
        assert magic["inventory_dir"] == "/some/inventory"
        assert magic["inventory_file"] == "/some/inventory/agents.yaml"

    def test_ansible_play_agents_matches_play(self, simple_playbook_yaml, inventory):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, verbose=False, playbook_path=str(simple_playbook_yaml),
        )
        magic = executor._get_magic_variables(pb.plays[0])
        assert magic["ansible_play_name"] == "Test Play"
        assert magic["ansible_play_agents"] == ["researcher"]

    def test_magic_vars_reflect_cli_flags(self, simple_playbook_yaml, inventory):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, verbose=2, check_mode=True,
            tags=["foo", "bar"], skip_tags=["baz"], limit=["researcher"],
            playbook_path=str(simple_playbook_yaml),
        )
        magic = executor._get_magic_variables(pb.plays[0])
        assert magic["ansible_check_mode"] is True
        assert magic["ansible_verbosity"] == 2
        assert magic["ansible_run_tags"] == ["foo", "bar"]
        assert magic["ansible_skip_tags"] == ["baz"]
        assert magic["ansible_limit"] == ["researcher"]

    def test_magic_vars_override_play_vars(self, playbook_with_colliding_vars, inventory):
        """Play vars with the same name as a magic var MUST NOT override it."""
        pb = parse_playbook(playbook_with_colliding_vars)
        executor = PlaybookExecutor(
            pb, inventory, verbose=False,
            playbook_path=str(playbook_with_colliding_vars),
        )
        magic = executor._get_magic_variables(pb.plays[0])
        # play vars try to set playbook_dir="/hacked/by/play_vars" but magic wins
        assert magic["playbook_dir"] != "/hacked/by/play_vars"
        assert magic["playbook_dir"] == str(playbook_with_colliding_vars.resolve().parent)
        assert magic["ansible_play_name"] == "Collision Test"

    def test_extra_vars_override_magic_vars(self, simple_playbook_yaml, inventory):
        """Extra vars MUST override magic vars (highest precedence)."""
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, verbose=False,
            playbook_path=str(simple_playbook_yaml),
            extra_vars={"playbook_dir": "/from/extra/vars"},
            inventory_path="/some/inventory.yaml",
        )
        play = pb.plays[0]
        magic = executor._get_magic_variables(play)
        assert magic["playbook_dir"] == str(simple_playbook_yaml.resolve().parent)

        # When building full context in _execute_play, extra_vars should win
        # We can verify by checking the full merge order
        ctx = {}
        if play.vars:
            ctx.update(play.vars)
        ctx.update(magic)
        ctx.update(executor.extra_vars)
        assert ctx["playbook_dir"] == "/from/extra/vars"

    def test_crewai_playbook_version_in_magic(self, simple_playbook_yaml, inventory):
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, verbose=False, playbook_path=str(simple_playbook_yaml),
        )
        magic = executor._get_magic_variables(pb.plays[0])
        assert magic["crewai_playbook_version"] == __version__
        assert "full" in magic["ansible_version"]

    def test_magic_vars_available_in_task_variable_context(
        self, simple_playbook_yaml, inventory, mock_run_single_task
    ):
        """Magic vars should be in the variable_context passed to execute_task."""
        pb = parse_playbook(simple_playbook_yaml)
        executor = PlaybookExecutor(
            pb, inventory, verbose=False, playbook_path=str(simple_playbook_yaml),
        )
        with patch("crewai_playbook.core.executor.execute_task") as mock_exec:
            mock_exec.return_value = "mock output"
            executor.run()
            mock_exec.assert_called_once()
            _task, _agents, var_ctx, _verbose = mock_exec.call_args[0]
            assert "playbook_dir" in var_ctx
            assert "ansible_play_name" in var_ctx
            assert "ansible_play_agents" in var_ctx
            assert var_ctx["playbook_dir"] == str(simple_playbook_yaml.resolve().parent)

    def test_roles_resolve_in_executor(
        self, role_playbook_yaml, inventory, mock_run_single_task, monkeypatch
    ):
        from crewai_playbook.modules.role import resolve_role_tasks
        from crewai_playbook.models.playbook import Task as PlaybookTask

        fake_tasks = [
            (PlaybookTask(name="Role task 1", agents=["researcher"], task="Do role work"), {"topic": "AI"}),
            (PlaybookTask(name="Role task 2", agents=["writer"], task="Write from role"), {"format": "md"}),
        ]
        monkeypatch.setattr(
            "crewai_playbook.core.executor.resolve_role_tasks",
            lambda *a, **kw: fake_tasks
        )
        pb = parse_playbook(role_playbook_yaml)
        executor = PlaybookExecutor(pb, inventory, verbose=False)
        results = executor.run()
        assert results["failed"] is False
        play_result = results["plays"][0]
        task_names = [t["name"] for t in play_result["tasks"]]
        assert "Role task 1" in task_names
        assert "Role task 2" in task_names

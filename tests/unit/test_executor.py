from unittest.mock import patch, MagicMock

import pytest
import yaml

from crewai_playbook.core.executor import PlaybookExecutor
from crewai_playbook.core.parser import parse_playbook
from crewai_playbook.models.agent import AgentDefinition


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
        with patch("crewai_playbook.core.executor.run_crew_for_play") as mock_crew:
            mock_crew.return_value = {"T1": "research done", "T2": "article written"}
            executor = PlaybookExecutor(pb, inventory, verbose=False)
            results = executor.run()
            assert results["failed"] is False
            mock_crew.assert_called_once()
            call_kwargs = mock_crew.call_args[1]
            assert call_kwargs["leader_name"] == "researcher"
            assert call_kwargs["process"] == "hierarchical"

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

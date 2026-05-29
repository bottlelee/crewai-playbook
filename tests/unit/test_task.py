from unittest.mock import patch, MagicMock

import pytest

from crewai_playbook.models.playbook import Task as PlaybookTask
from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.modules.task import execute_task, _evaluate_when


@pytest.fixture
def inventory():
    return {
        "researcher": AgentDefinition(
            role="Research Specialist",
            goal="Find info",
            backstory="Expert",
        ),
    }


class TestExecuteTask:
    def test_execute_success(self, inventory):
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "research output"
            task = PlaybookTask(
                name="Research",
                agents=["researcher"],
                task="Find information",
            )
            result = execute_task(task, inventory, {})
            assert result == "research output"

    def test_register_var_stores_output(self, inventory):
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "important data"
            task = PlaybookTask(
                name="Research",
                agents=["researcher"],
                task="Find info",
                register_var="output_data",
            )
            ctx = {}
            execute_task(task, inventory, ctx)
            assert ctx["output_data"] == "important data"
            assert ctx["output_data_is_defined"] is True
            assert ctx["output_data_succeeded"] is True

    def test_when_condition_skips_execution(self, inventory):
        task = PlaybookTask(
            name="Skipped task",
            agents=["researcher"],
            task="Should not run",
            when="false",
        )
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            result = execute_task(task, inventory, {})
            assert result == ""
            mock.assert_not_called()

    def test_retry_on_failure(self, inventory):
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.side_effect = [ValueError("fail"), "success"]
            task = PlaybookTask(
                name="Retry task",
                agents=["researcher"],
                task="Retry me",
                retries=2,
                delay=0,
            )
            result = execute_task(task, inventory, {})
            assert result == "success"
            assert mock.call_count == 2

    def test_retry_exhausted(self, inventory):
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.side_effect = ValueError("always fail")
            task = PlaybookTask(
                name="Failing task",
                agents=["researcher"],
                task="Will fail",
                retries=2,
                delay=0,
            )
            with pytest.raises(Exception, match="failed after 2 retries"):
                execute_task(task, inventory, {})

    def test_until_condition_retries(self, inventory):
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.side_effect = ["bad result", "good result contains X"]
            task = PlaybookTask(
                name="Until task",
                agents=["researcher"],
                task="Retry until good",
                until="result contains X",
                retries=3,
                delay=0,
            )
            result = execute_task(task, inventory, {})
            assert "X" in result
            assert mock.call_count == 2


    def test_src_file_appended_to_task(self, inventory, tmp_path):
        src_file = tmp_path / "context.txt"
        src_file.write_text("Important context data")
        task = PlaybookTask(
            name="With src",
            agents=["researcher"],
            task="Use the context",
            src=str(src_file),
        )
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "used context"
            result = execute_task(task, inventory, {})
            assert result == "used context"
            call_desc = mock.call_args[1]["task_description"]
            assert "Important context data" in call_desc
            assert "Use the context" in call_desc

    def test_dest_file_written(self, inventory, tmp_path):
        dest_file = tmp_path / "output.txt"
        task = PlaybookTask(
            name="With dest",
            agents=["researcher"],
            task="Generate output",
            dest=str(dest_file),
        )
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "generated content"
            result = execute_task(task, inventory, {})
            assert result == "generated content"
            assert dest_file.exists()
            assert dest_file.read_text() == "generated content"

    def test_dest_not_written_on_empty_output(self, inventory, tmp_path):
        dest_file = tmp_path / "empty.txt"
        task = PlaybookTask(
            name="Empty dest",
            agents=["researcher"],
            task="Produce nothing",
            dest=str(dest_file),
        )
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = ""
            result = execute_task(task, inventory, {})
            assert result == ""
            assert not dest_file.exists()

    def test_src_missing_file_does_not_break(self, inventory):
        task = PlaybookTask(
            name="Missing src",
            agents=["researcher"],
            task="Work without context",
            src="/nonexistent/file.txt",
        )
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "result"
            result = execute_task(task, inventory, {})
            assert result == "result"

    def test_src_resolves_variable(self, inventory, tmp_path):
        src_file = tmp_path / "ai_context.txt"
        src_file.write_text("AI-specific data")
        task = PlaybookTask(
            name="Var src",
            agents=["researcher"],
            task="Use {{ topic }} context",
            src="{{ src_path }}",
        )
        ctx = {"topic": "AI", "src_path": str(src_file)}
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "done"
            result = execute_task(task, inventory, ctx)
            assert result == "done"

    def test_dest_resolves_variable(self, inventory, tmp_path):
        task = PlaybookTask(
            name="Var dest",
            agents=["researcher"],
            task="Write to dynamic path",
            dest="{{ output_dir }}/result.txt",
        )
        ctx = {"output_dir": str(tmp_path)}
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "dynamic path content"
            result = execute_task(task, inventory, ctx)
            assert result == "dynamic path content"
            assert (tmp_path / "result.txt").exists()
            assert (tmp_path / "result.txt").read_text() == "dynamic path content"


class TestEvaluateWhen:
    def test_is_defined_true(self):
        assert _evaluate_when("result is defined", {"result": "data"}) is True

    def test_is_defined_false(self):
        assert _evaluate_when("result is defined", {}) is False

    def test_is_not_defined_true(self):
        assert _evaluate_when("result is not defined", {}) is True

    def test_is_succeeded_true(self):
        assert _evaluate_when("result is succeeded",
                               {"result_succeeded": True}) is True

    def test_is_succeeded_false(self):
        assert _evaluate_when("result is succeeded", {}) is False

from unittest.mock import patch, MagicMock

import pytest

from crewai_playbook.models.playbook import Task as PlaybookTask
from crewai_playbook.models.agent import AgentDefinition
from crewai_playbook.modules.task import execute_task


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

    def test_when_condition_added_to_context(self, inventory):
        task = PlaybookTask(
            name="Conditional task",
            agents=["researcher"],
            task="Should check condition",
            when="result_var is defined",
        )
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "executed"
            result = execute_task(task, inventory, {})
            assert result == "executed"
            call_desc = mock.call_args[1]["task_description"]
            assert "Condition: only execute this task if" in call_desc
            assert "result_var is defined" in call_desc

    def test_retry_instruction_in_context(self, inventory):
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "result"
            task = PlaybookTask(
                name="Retry task",
                agents=["researcher"],
                task="Retry me",
                retries=2,
                delay=5,
            )
            result = execute_task(task, inventory, {})
            assert result == "result"
            call_desc = mock.call_args[1]["task_description"]
            assert "Retry up to 2 times" in call_desc
            assert "Wait 5 seconds between retries" in call_desc

    def test_error_wraps_in_execution_error(self, inventory):
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.side_effect = ValueError("always fail")
            task = PlaybookTask(
                name="Failing task",
                agents=["researcher"],
                task="Will fail",
            )
            from crewai_playbook.utils.errors import ExecutionError
            with pytest.raises(ExecutionError, match="task 'Failing task' failed"):
                execute_task(task, inventory, {})

    def test_until_instruction_in_context(self, inventory):
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "result with X"
            task = PlaybookTask(
                name="Until task",
                agents=["researcher"],
                task="Retry until good",
                until="result contains X",
                retries=3,
                delay=0,
            )
            result = execute_task(task, inventory, {})
            assert result == "result with X"
            call_desc = mock.call_args[1]["task_description"]
            assert "Keep retrying until: result contains X" in call_desc

    def test_notify_instruction_in_context(self, inventory):
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "notified"
            task = PlaybookTask(
                name="Notify task",
                agents=["researcher"],
                task="Do work",
                notify=["email_admin", "log_handler"],
            )
            result = execute_task(task, inventory, {})
            assert result == "notified"
            call_desc = mock.call_args[1]["task_description"]
            assert "After completion, notify:" in call_desc
            assert "email_admin" in call_desc
            assert "log_handler" in call_desc

    def test_register_instruction_in_context(self, inventory):
        with patch("crewai_playbook.modules.task.run_single_task") as mock:
            mock.return_value = "registered data"
            task = PlaybookTask(
                name="Register task",
                agents=["researcher"],
                task="Store result",
                register_var="my_output",
            )
            ctx = {}
            result = execute_task(task, inventory, ctx)
            assert result == "registered data"
            assert ctx["my_output"] == "registered data"
            assert ctx["my_output_is_defined"] is True
            call_desc = mock.call_args[1]["task_description"]
            assert "Save your output as 'my_output'" in call_desc

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
            assert "read file" in call_desc
            assert str(src_file) in call_desc
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
            call_desc = mock.call_args[1]["task_description"]
            assert "output to file" in call_desc
            assert str(dest_file) in call_desc

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
            call_desc = mock.call_args[1]["task_description"]
            assert "output to file" in call_desc
            assert str(dest_file) in call_desc

    def test_src_missing_file_sets_context(self, inventory):
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
            call_desc = mock.call_args[1]["task_description"]
            assert "read file" in call_desc
            assert "/nonexistent/file.txt" in call_desc

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
            call_desc = mock.call_args[1]["task_description"]
            assert "output to file" in call_desc
            assert str(tmp_path / "result.txt") in call_desc




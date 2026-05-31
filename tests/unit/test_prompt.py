from unittest.mock import patch, MagicMock

import pytest
import yaml

from crewai_playbook.models.playbook import VarPrompt
from crewai_playbook.modules.prompt import prompt_vars, _prompt_single
from crewai_playbook.core.parser import parse_playbook
from crewai_playbook.core.executor import PlaybookExecutor
from crewai_playbook.models.agent import AgentDefinition


# ---------------------------------------------------------------------------
# VarPrompt model
# ---------------------------------------------------------------------------

class TestVarPromptModel:
    def test_defaults(self):
        vp = VarPrompt(name="x")
        assert vp.name == "x"
        assert vp.prompt is None
        assert vp.default is None
        assert vp.private is False
        assert vp.choices is None

    def test_full(self):
        vp = VarPrompt(
            name="env",
            prompt="Which env?",
            default="dev",
            choices=["dev", "prod"],
            private=True,
        )
        assert vp.name == "env"
        assert vp.choices == ["dev", "prod"]


# ---------------------------------------------------------------------------
# prompt_vars
# ---------------------------------------------------------------------------

class TestPromptVars:
    @patch("builtins.input", return_value="hello")
    def test_basic_prompt(self, _mock_input):
        prompts = [VarPrompt(name="greeting")]
        result = prompt_vars(prompts)
        assert result == {"greeting": "hello"}

    @patch("builtins.input", return_value="")
    def test_default_used_when_empty(self, _mock_input):
        prompts = [VarPrompt(name="topic", default="AI")]
        result = prompt_vars(prompts)
        assert result == {"topic": "AI"}

    @patch("builtins.input", return_value="custom")
    def test_default_overridden(self, _mock_input):
        prompts = [VarPrompt(name="topic", default="AI")]
        result = prompt_vars(prompts)
        assert result == {"topic": "custom"}

    def test_skip_when_already_defined(self):
        prompts = [VarPrompt(name="topic")]
        result = prompt_vars(prompts, already_defined={"topic": "from_extra"})
        assert result == {}

    @patch("builtins.input", side_effect=["bad", "dev"])
    def test_choices_validation_retries(self, _mock_input):
        prompts = [VarPrompt(name="env", choices=["dev", "prod"])]
        result = prompt_vars(prompts)
        assert result == {"env": "dev"}
        assert _mock_input.call_count == 2

    @patch("builtins.input", return_value="prod")
    def test_choices_valid_input(self, _mock_input):
        prompts = [VarPrompt(name="env", choices=["dev", "prod"])]
        result = prompt_vars(prompts)
        assert result == {"env": "prod"}

    @patch("builtins.input", return_value="")
    def test_default_satisfies_choices(self, _mock_input):
        prompts = [VarPrompt(name="env", default="dev", choices=["dev", "prod"])]
        result = prompt_vars(prompts)
        assert result == {"env": "dev"}

    @patch("builtins.input", side_effect=EOFError)
    def test_eof_falls_back_to_default(self, _mock_input):
        prompts = [VarPrompt(name="topic", default="fallback")]
        result = prompt_vars(prompts)
        assert result == {"topic": "fallback"}

    @patch("builtins.input", side_effect=EOFError)
    def test_eof_no_default_returns_empty(self, _mock_input):
        prompts = [VarPrompt(name="topic")]
        result = prompt_vars(prompts)
        assert result == {"topic": ""}

    @patch("builtins.input", return_value="val")
    def test_multiple_prompts(self, _mock_input):
        prompts = [VarPrompt(name="a"), VarPrompt(name="b")]
        result = prompt_vars(prompts)
        assert result == {"a": "val", "b": "val"}

    @patch("builtins.input", return_value="val")
    def test_prompt_text_passed_to_input(self, mock_input):
        prompts = [VarPrompt(name="x", prompt="Enter X")]
        prompt_vars(prompts)
        call_arg = mock_input.call_args[0][0]
        assert "Enter X" in call_arg

    @patch("builtins.input", return_value="val")
    def test_prompt_text_includes_default_hint(self, mock_input):
        prompts = [VarPrompt(name="x", prompt="Enter X", default="dflt")]
        prompt_vars(prompts)
        call_arg = mock_input.call_args[0][0]
        assert "dflt" in call_arg


# ---------------------------------------------------------------------------
# Parser integration
# ---------------------------------------------------------------------------

class TestParserVarsPrompt:
    def test_parse_vars_prompt(self, tmp_path):
        p = tmp_path / "vp.yml"
        data = [{
            "name": "Test",
            "agents": ["r"],
            "gather_facts": False,
            "vars_prompt": [
                {"name": "topic", "prompt": "What?", "default": "AI"},
                {"name": "env", "choices": ["dev", "prod"], "private": True},
            ],
            "tasks": [{"name": "T", "agents": ["r"], "task": "Do {{ topic }} in {{ env }}"}],
        }]
        p.write_text(yaml.safe_dump(data))
        pb = parse_playbook(p)
        play = pb.plays[0]
        assert play.vars_prompt is not None
        assert len(play.vars_prompt) == 2
        assert play.vars_prompt[0].name == "topic"
        assert play.vars_prompt[0].default == "AI"
        assert play.vars_prompt[1].choices == ["dev", "prod"]
        assert play.vars_prompt[1].private is True

    def test_parse_no_vars_prompt(self, simple_playbook_yaml):
        pb = parse_playbook(simple_playbook_yaml)
        assert pb.plays[0].vars_prompt is None

    def test_parse_vars_prompt_must_be_list(self, tmp_path):
        p = tmp_path / "bad.yml"
        data = [{
            "name": "Test",
            "agents": ["r"],
            "vars_prompt": "not a list",
            "tasks": [{"name": "T", "agents": ["r"], "task": "x"}],
        }]
        p.write_text(yaml.safe_dump(data))
        from crewai_playbook.utils.errors import ParseError
        with pytest.raises(ParseError, match="vars_prompt"):
            parse_playbook(p)

    def test_parse_vars_prompt_entry_needs_name(self, tmp_path):
        p = tmp_path / "bad.yml"
        data = [{
            "name": "Test",
            "agents": ["r"],
            "vars_prompt": [{"prompt": "no name field"}],
            "tasks": [{"name": "T", "agents": ["r"], "task": "x"}],
        }]
        p.write_text(yaml.safe_dump(data))
        from crewai_playbook.utils.errors import ParseError
        with pytest.raises(ParseError, match="name"):
            parse_playbook(p)


# ---------------------------------------------------------------------------
# Syntax check integration
# ---------------------------------------------------------------------------

class TestSyntaxCheckVarsPrompt:
    def test_vars_prompt_vars_known(self, tmp_path):
        p = tmp_path / "vp.yml"
        data = [{
            "name": "Test",
            "agents": ["r"],
            "gather_facts": False,
            "vars_prompt": [{"name": "topic"}],
            "tasks": [{"name": "T", "agents": ["r"], "task": "Do {{ topic }}"}],
        }]
        p.write_text(yaml.safe_dump(data))
        from crewai_playbook.core.parser import syntax_check
        errors = syntax_check(p)
        assert errors == []


# ---------------------------------------------------------------------------
# Executor integration
# ---------------------------------------------------------------------------

class TestExecutorVarsPrompt:
    @pytest.fixture
    def inventory(self):
        return {
            "researcher": AgentDefinition(
                role="R", goal="G", backstory="B",
            ),
        }

    @patch("crewai_playbook.core.executor.prompt_vars")
    @patch("crewai_playbook.core.executor.execute_task", return_value="ok")
    def test_executor_calls_prompt_vars(
        self, _mock_task, mock_prompt, tmp_path, inventory
    ):
        mock_prompt.return_value = {"topic": "prompted_value"}
        p = tmp_path / "vp.yml"
        data = [{
            "name": "Test",
            "agents": ["researcher"],
            "gather_facts": False,
            "vars_prompt": [{"name": "topic", "prompt": "What?"}],
            "tasks": [{"name": "T", "agents": ["researcher"], "task": "Research {{ topic }}"}],
        }]
        p.write_text(yaml.safe_dump(data))
        pb = parse_playbook(p)
        executor = PlaybookExecutor(pb, inventory)
        executor.run()
        mock_prompt.assert_called_once()
        call_kwargs = mock_prompt.call_args
        assert call_kwargs[1]["already_defined"] == {}

    @patch("crewai_playbook.core.executor.prompt_vars")
    @patch("crewai_playbook.core.executor.execute_task", return_value="ok")
    def test_executor_passes_extra_vars_to_prompt(
        self, _mock_task, mock_prompt, tmp_path, inventory
    ):
        mock_prompt.return_value = {}
        p = tmp_path / "vp.yml"
        data = [{
            "name": "Test",
            "agents": ["researcher"],
            "gather_facts": False,
            "vars_prompt": [{"name": "topic"}],
            "tasks": [{"name": "T", "agents": ["researcher"], "task": "Research {{ topic }}"}],
        }]
        p.write_text(yaml.safe_dump(data))
        pb = parse_playbook(p)
        executor = PlaybookExecutor(
            pb, inventory, extra_vars={"topic": "from_cli"}
        )
        executor.run()
        call_kwargs = mock_prompt.call_args
        assert call_kwargs[1]["already_defined"] == {"topic": "from_cli"}

    @patch("crewai_playbook.core.executor.prompt_vars")
    @patch("crewai_playbook.core.executor.execute_task", return_value="ok")
    def test_prompt_value_used_in_task(
        self, mock_task, mock_prompt, tmp_path, inventory
    ):
        mock_prompt.return_value = {"topic": "quantum"}
        p = tmp_path / "vp.yml"
        data = [{
            "name": "Test",
            "agents": ["researcher"],
            "gather_facts": False,
            "vars_prompt": [{"name": "topic"}],
            "tasks": [{"name": "T", "agents": ["researcher"], "task": "Research {{ topic }}"}],
        }]
        p.write_text(yaml.safe_dump(data))
        pb = parse_playbook(p)
        executor = PlaybookExecutor(pb, inventory)
        executor.run()
        # execute_task receives (task, inventory, variable_context, verbose)
        var_ctx = mock_task.call_args[0][2]
        assert var_ctx["topic"] == "quantum"

    @patch("builtins.input", return_value="")
    def test_no_vars_prompt_no_prompt(self, _mock_input, tmp_path, inventory):
        p = tmp_path / "no_vp.yml"
        data = [{
            "name": "Test",
            "agents": ["researcher"],
            "gather_facts": False,
            "tasks": [{"name": "T", "agents": ["researcher"], "task": "Do something"}],
        }]
        p.write_text(yaml.safe_dump(data))
        pb = parse_playbook(p)
        with patch("crewai_playbook.core.executor.execute_task", return_value="ok"):
            executor = PlaybookExecutor(pb, inventory)
            executor.run()
        _mock_input.assert_not_called()

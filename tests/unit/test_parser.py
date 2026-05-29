import yaml
import pytest
from crewai_playbook.core.parser import parse_playbook, syntax_check
from crewai_playbook.models.playbook import Playbook, Task, Block
from crewai_playbook.utils.errors import ParseError


class TestParsePlaybook:
    def test_parse_simple_playbook(self, simple_playbook_yaml):
        pb = parse_playbook(simple_playbook_yaml)
        assert isinstance(pb, Playbook)
        assert len(pb.plays) == 1
        play = pb.plays[0]
        assert play.name == "Test Play"
        assert play.agents == ["researcher"]
        assert play.gather_facts is False
        assert len(play.tasks) == 1
        task = play.tasks[0]
        assert isinstance(task, Task)
        assert task.name == "Research task"
        assert task.task == "Find information about AI"

    def test_parse_block_playbook(self, block_playbook_yaml):
        pb = parse_playbook(block_playbook_yaml)
        assert len(pb.plays) == 1
        play = pb.plays[0]
        assert len(play.tasks) == 1
        block = play.tasks[0]
        assert isinstance(block, Block)
        assert len(block.block) == 1
        assert len(block.rescue) == 1
        assert len(block.always) == 1
        assert block.block[0].name == "Main task"
        assert block.rescue[0].name == "Fallback"
        assert block.always[0].name == "Cleanup"

    def test_parse_handler_playbook(self, handler_playbook_yaml):
        pb = parse_playbook(handler_playbook_yaml)
        play = pb.plays[0]
        assert play.handlers is not None
        assert len(play.handlers) == 1
        handler = play.handlers[0]
        assert handler.name == "Summarize"
        assert len(handler.tasks) == 1
        assert handler.tasks[0].name == "Create summary"

    def test_parse_missing_file(self):
        with pytest.raises(ParseError, match="not found"):
            parse_playbook("/nonexistent/playbook.yml")

    def test_parse_invalid_yaml(self, tmp_path):
        p = tmp_path / "bad.yml"
        p.write_text("{{ invalid yaml: }")
        with pytest.raises(ParseError, match="YAML parse error"):
            parse_playbook(p)

    def test_parse_not_a_list(self, tmp_path):
        p = tmp_path / "bad.yml"
        p.write_text("name: not a list")
        with pytest.raises(ParseError, match="must be a list"):
            parse_playbook(p)

    def test_parse_missing_required_keys(self, tmp_path):
        p = tmp_path / "bad.yml"
        p.write_text(yaml.safe_dump([{"name": "no agents"}]))
        with pytest.raises(ParseError, match="missing required key"):
            parse_playbook(p)

    def test_parse_roles(self, role_playbook_yaml):
        pb = parse_playbook(role_playbook_yaml)
        play = pb.plays[0]
        assert play.roles is not None
        assert len(play.roles) == 2
        assert play.roles[0].role == "research"
        assert play.roles[0].vars == {"topic": "AI"}
        assert play.roles[1].role == "write"

    def test_parse_tags_on_task(self, tagged_playbook_yaml):
        pb = parse_playbook(tagged_playbook_yaml)
        play = pb.plays[0]
        tasks = play.tasks
        assert tasks[0].tags == ["research"]
        assert tasks[1].tags == ["coding"]
        assert tasks[2].tags == ["summary"]


class TestSyntaxCheck:
    def test_valid_playbook_passes(self, simple_playbook_yaml):
        errors = syntax_check(simple_playbook_yaml)
        assert errors == []

    def test_empty_name_fails(self, tmp_path):
        p = tmp_path / "bad.yml"
        data = [{"name": "", "agents": ["researcher"], "tasks": []}]
        p.write_text(yaml.safe_dump(data))
        errors = syntax_check(p)
        assert any("name' must not be empty" in e for e in errors)

    def test_missing_playbook_file(self, tmp_path):
        errors = syntax_check(tmp_path / "nope.yml")
        assert len(errors) > 0

from typer.testing import CliRunner
from crewai_playbook.cli.app import app

runner = CliRunner()


class TestCLI:
    def test_version(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "crewai-playbook v" in result.stdout

    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        assert result.exit_code in (0, 2)
        assert "crewai-playbook" in result.stdout

    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "crewai-playbook" in result.stdout

    def test_run_syntax_check_valid(self, simple_playbook_yaml):
        result = runner.invoke(app, [
            "run", str(simple_playbook_yaml), "--syntax-check"
        ])
        assert result.exit_code == 0
        assert "Syntax check passed" in result.stdout

    def test_run_syntax_check_invalid(self, tmp_path):
        p = tmp_path / "bad.yml"
        p.write_text("name: not a list")
        result = runner.invoke(app, [
            "run", str(p), "--syntax-check"
        ])
        assert result.exit_code == 1
        assert "SYNTAX ERROR" in result.stdout or "ERROR" in result.stdout

    def test_run_check_mode(self, simple_playbook_yaml):
        result = runner.invoke(app, [
            "run", str(simple_playbook_yaml), "--check"
        ])
        assert result.exit_code == 0
        assert "CHECK MODE" in result.stdout

    def test_list_tasks(self, simple_playbook_yaml):
        result = runner.invoke(app, [
            "run", str(simple_playbook_yaml), "--list-tasks"
        ])
        assert result.exit_code == 0
        assert "Research task" in result.stdout

    def test_list_tags(self, tagged_playbook_yaml):
        result = runner.invoke(app, [
            "run", str(tagged_playbook_yaml), "--list-tags"
        ])
        assert result.exit_code == 0
        assert "coding" in result.stdout
        assert "research" in result.stdout
        assert "summary" in result.stdout

    def test_run_invalid_playbook(self, tmp_path):
        p = tmp_path / "bad.yml"
        p.write_text("name: not a list")
        result = runner.invoke(app, ["run", str(p)])
        assert result.exit_code == 1

    def test_run_missing_playbook(self):
        result = runner.invoke(app, ["run", "/nonexistent/playbook.yml"])
        assert result.exit_code == 1
        assert "ERROR" in result.stdout or "not found" in result.stdout

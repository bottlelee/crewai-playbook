from typer.testing import CliRunner
import yaml

from crewai_playbook.cli.app import app

runner = CliRunner()


class TestLintCLI:
    def test_lint_valid_playbook(self, simple_playbook_yaml, inventory_yaml):
        result = runner.invoke(app, [
            "lint", str(simple_playbook_yaml),
            "--inventory", str(inventory_yaml),
        ])
        assert result.exit_code == 0
        assert "Lint passed" in result.stdout

    def test_lint_missing_agent(self, tmp_path, inventory_yaml):
        p = tmp_path / "bad.yml"
        data = [{"name": "Test", "agents": ["nonexistent"], "tasks": []}]
        p.write_text(yaml.safe_dump(data))
        result = runner.invoke(app, [
            "lint", str(p),
            "--inventory", str(inventory_yaml),
        ])
        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_lint_empty_play_name(self, tmp_path, inventory_yaml):
        p = tmp_path / "bad.yml"
        data = [{"name": "", "agents": ["researcher"], "tasks": []}]
        p.write_text(yaml.safe_dump(data))
        result = runner.invoke(app, [
            "lint", str(p),
            "--inventory", str(inventory_yaml),
        ])
        assert result.exit_code == 1
        assert "must not be empty" in result.stdout

    def test_lint_duplicate_role(self, tmp_path, inventory_yaml):
        p = tmp_path / "bad.yml"
        data = [{
            "name": "Test",
            "agents": ["researcher"],
            "roles": [{"role": "research"}, {"role": "research"}],
        }]
        p.write_text(yaml.safe_dump(data))
        result = runner.invoke(app, [
            "lint", str(p),
            "--inventory", str(inventory_yaml),
        ])
        assert result.exit_code == 1
        assert "more than once" in result.stdout

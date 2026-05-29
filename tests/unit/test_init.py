from pathlib import Path

from typer.testing import CliRunner
from crewai_playbook.cli.app import app
from crewai_playbook.resources.scaffold import create_project

runner = CliRunner()


class TestScaffold:
    def test_create_project_creates_structure(self, tmp_path):
        dest = tmp_path / "my_project"
        create_project(dest)
        assert (dest / "config" / "agents.yaml").exists()
        assert (dest / "playbooks" / "example.yml").exists()
        assert (dest / "roles").exists()
        assert (dest / "group_vars").exists()
        assert (dest / "inventory").exists()
        assert (dest / ".gitignore").exists()
        assert (dest / "crewai-playbook.yml").exists()

    def test_create_project_on_existing_nonempty_raises(self, tmp_path):
        dest = tmp_path / "existing"
        dest.mkdir()
        (dest / "some_file.txt").write_text("hello")
        from crewai_playbook.utils.errors import CrewAIBookError
        import pytest
        with pytest.raises(CrewAIBookError, match="exists and is not empty"):
            create_project(dest)


class TestInitCLI:
    def test_init_command(self, tmp_path):
        dest = tmp_path / "new_project"
        result = runner.invoke(app, ["init", str(dest)])
        assert result.exit_code == 0
        assert "Project scaffolded" in result.stdout
        assert (dest / "config" / "agents.yaml").exists()



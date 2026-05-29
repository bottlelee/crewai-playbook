import pytest
import yaml
from crewai_playbook.core.inventory import load_inventory, resolve_agents
from crewai_playbook.utils.errors import InventoryError


class TestLoadInventory:
    def test_load_valid_inventory(self, inventory_yaml):
        agents = load_inventory(inventory_yaml)
        assert "researcher" in agents
        assert "writer" in agents
        assert agents["researcher"].role == "Research Specialist"

    def test_missing_file(self):
        with pytest.raises(InventoryError, match="not found"):
            load_inventory("/nonexistent/agents.yaml")

    def test_missing_agents_key(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(yaml.safe_dump({"not_agents": {}}))
        with pytest.raises(InventoryError, match="must contain an 'agents' mapping"):
            load_inventory(p)

    def test_invalid_agent_entry(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(yaml.safe_dump({"agents": {"bad": {"role": "x"}}}))
        with pytest.raises(InventoryError):
            load_inventory(p)


class TestResolveAgents:
    def test_resolve_by_name(self, sample_inventory):
        result = resolve_agents(["researcher", "writer"], sample_inventory)
        assert set(result.keys()) == {"researcher", "writer"}

    def test_resolve_by_group(self, sample_inventory):
        result = resolve_agents(["@research"], sample_inventory)
        assert "researcher" in result
        assert "writer" not in result

    def test_resolve_group_with_multiple(self, sample_inventory):
        result = resolve_agents(["@default"], sample_inventory)
        assert set(result.keys()) == {"researcher", "writer", "reviewer"}

    def test_missing_agent_raises(self, sample_inventory):
        with pytest.raises(InventoryError, match="not found"):
            resolve_agents(["nonexistent"], sample_inventory)

    def test_empty_group_raises(self, sample_inventory):
        with pytest.raises(InventoryError, match="no agents found"):
            resolve_agents(["@phantom"], sample_inventory)

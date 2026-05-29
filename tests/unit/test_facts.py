from crewai_playbook.modules.facts import gather_facts, _detect_tools


class TestGatherFacts:
    def test_gather_facts_returns_dict(self):
        facts = gather_facts()
        assert isinstance(facts, dict)

    def test_os_section(self):
        facts = gather_facts()
        assert "os" in facts
        assert "system" in facts["os"]
        assert "hostname" in facts["os"]

    def test_python_section(self):
        facts = gather_facts()
        assert "python" in facts
        assert "version" in facts["python"]
        assert "executable" in facts["python"]

    def test_cwd_section(self):
        facts = gather_facts()
        assert "cwd" in facts

    def test_environment_section(self):
        facts = gather_facts()
        assert "environment" in facts
        assert "user" in facts["environment"]

    def test_tools_section(self):
        facts = gather_facts()
        assert "tools" in facts
        assert isinstance(facts["tools"], dict)


class TestDetectTools:
    def test_detect_returns_bools(self):
        tools = _detect_tools()
        assert isinstance(tools, dict)
        for key, val in tools.items():
            assert isinstance(val, bool)

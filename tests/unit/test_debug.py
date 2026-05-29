from crewai_playbook.modules.debug import debug


class TestDebug:
    def test_debug_with_msg(self):
        result = debug(msg="Hello world")
        assert "Hello world" in result

    def test_debug_with_var(self):
        result = debug(msg="Check value", var="myvar",
                        variable_context={"myvar": 42})
        assert "42" in result
        assert "myvar" in result

    def test_debug_undefined_var(self):
        result = debug(msg="Check", var="missing",
                        variable_context={})
        assert "UNDEFINED" in result

    def test_debug_empty(self):
        result = debug(msg="")
        assert result == ""

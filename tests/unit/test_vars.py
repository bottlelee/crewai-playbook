import pytest
from crewai_playbook.utils.vars import resolve_vars, collect_variable_refs
from crewai_playbook.utils.errors import VariableError


class TestResolveVars:
    def test_simple_substitution(self):
        result = resolve_vars("Hello {{ name }}", {"name": "World"})
        assert result == "Hello World"

    def test_dotted_path(self):
        result = resolve_vars("{{ facts.os }}", {"facts": {"os": "Linux"}})
        assert result == "Linux"

    def test_undefined_variable(self):
        with pytest.raises(VariableError, match="undefined"):
            resolve_vars("{{ missing }}", {})

    def test_partial_dotted_path_failure(self):
        with pytest.raises(VariableError, match="undefined"):
            resolve_vars("{{ facts.missing }}", {"facts": {"os": "Linux"}})

    def test_no_variables(self):
        result = resolve_vars("plain string", {})
        assert result == "plain string"

    def test_dict_values(self):
        result = resolve_vars({"key": "{{ val }}"}, {"val": "hello"})
        assert result == {"key": "hello"}

    def test_list_values(self):
        result = resolve_vars(["{{ a }}", "{{ b }}"], {"a": "1", "b": "2"})
        assert result == ["1", "2"]

    def test_non_string_value(self):
        result = resolve_vars(42, {})
        assert result == 42

    def test_nested_variable_resolution(self):
        context = {
            "playbook_dir": "/path/to/project",
            "project_dir": "{{ playbook_dir }}/output/sdd",
            "feature": "task-board",
        }
        result = resolve_vars(
            "{{ project_dir }}/specs/{{ feature }}/constitution.md",
            context,
        )
        assert result == "/path/to/project/output/sdd/specs/task-board/constitution.md"

    def test_double_nested_variables(self):
        context = {
            "base": "/base/path",
            "project": "{{ base }}/project",
            "output": "{{ project }}/output",
        }
        result = resolve_vars("path: {{ output }}/file.md", context)
        assert result == "path: /base/path/project/output/file.md"

    def test_circular_variable_reference(self):
        context = {"a": "{{ b }}", "b": "{{ a }}"}
        with pytest.raises(VariableError, match="circular"):
            resolve_vars("{{ a }}", context)


class TestCollectVariableRefs:
    def test_finds_variables(self):
        refs = collect_variable_refs("{{ name }} and {{ age }}")
        assert refs == {"name", "age"}

    def test_dotted_paths(self):
        refs = collect_variable_refs("{{ facts.os }}")
        assert refs == {"facts.os"}

    def test_no_variables(self):
        assert collect_variable_refs("no templates") == set()

    def test_collect_from_dict(self):
        refs = collect_variable_refs({"a": "{{ x }}", "b": "{{ y }}"})
        assert refs == {"x", "y"}

    def test_collect_from_list(self):
        refs = collect_variable_refs(["{{ a }}", "{{ b }}"])
        assert refs == {"a", "b"}

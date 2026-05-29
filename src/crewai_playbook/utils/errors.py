class CrewAIBookError(Exception):
    """Base error for all crewai-playbook errors."""


class ParseError(CrewAIBookError):
    """Raised when a playbook YAML file cannot be parsed or validated."""


class InventoryError(CrewAIBookError):
    """Raised when agents.yaml is missing, malformed, or references an undefined agent."""


class VariableError(CrewAIBookError):
    """Raised when a variable reference cannot be resolved."""


class ExecutionError(CrewAIBookError):
    """Raised when a play or task execution fails."""


class ConfigError(CrewAIBookError):
    """Raised when crewai-playbook.yml is misconfigured."""


class RoleError(CrewAIBookError):
    """Raised when a role is missing or misconfigured."""


class LintError(CrewAIBookError):
    """Raised when --lint finds issues in a playbook."""

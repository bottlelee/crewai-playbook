# 🐍 Python Coding Standards and Best Practices (2026 Edition)

**Document Purpose:** This document outlines the mandatory coding standards and best practices for all Python development within the team. Adherence to these standards ensures code quality, maintainability, readability, and robustness, allowing for efficient collaboration and future scalability.

**Revision History:**
* 2026 Q1: Initial Release (Incorporating modern async/await and structured logging practices)
* **Owners:** Development Team / 沙悟淨 (Research & Support)

***

## 📜 1. General Principles and Philosophy

* **Readability First:** The primary goal is code that is easy for any developer on the team to understand quickly.
* **DRY (Don't Repeat Yourself):** Use functions, classes, and modules to encapsulate logic rather than repeating code blocks.
* **Single Responsibility Principle (SRP):** Every class, function, or module should have one, and only one, reason to change.
* **Type Safety:** Use type hints ubiquitously to enhance static analysis and catch errors early.
* **Idempotency:** Design functions where possible to be called multiple times without changing the outcome if the state hasn't changed.

## 🏷️ 2. Naming Conventions

Adherence to **PEP 8** is mandatory.

| Element | Convention | Example | Notes |
| :--- | :--- | :--- | :--- |
| **Modules/Packages** | `lowercase_with_underscores` | `data_processing.py` | Should be descriptive and lowercase. |
| **Classes** | `PascalCase` | `DataProcessor`, `ServiceManager` | Always start with a capital letter. |
| **Functions/Methods** | `snake_case` | `calculate_metrics()`, `fetch_user_data()` | Should be descriptive verbs. |
| **Variables** | `snake_case` | `user_id`, `total_count` | Local variables and parameters. |
| **Constants** | `ALL_CAPS_WITH_UNDERSCORES` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` | Global, unchanging values. |
| **Private Members** | Leading underscore (`_`) | `_internal_cache` | Indicates a member intended for internal use (convention only). |
| **Name Mangling** | Double leading underscore (`__`) | `__private_method` | Used sparingly; signals name collision avoidance. |

## 💡 3. Type Hinting (PEP 484 and Beyond)

Type hinting is **mandatory** for all function signatures, class attributes, and complex structures.

### 🔑 Best Practices:
1. **Always Hint:** Do not omit type hints, even for simple functions.
2. **Use `typing` Module:** Use generics from the `typing` module (`List`, `Dict`, `Optional`, `Union`, `Any`, etc.) correctly.
3. **Asynchronous Typing:** When dealing with `async` functions, ensure correct return type hinting (e.g., `-> Awaitable[List[str]]`).
4. **Protocol Usage:** For defining required methods on a class without inheritance (Structural Typing), use `typing.Protocol`.

**Example:**
```python
from typing import List, Optional

def process_data(data: List[Dict[str, Any]], config: Optional[str] = None) -> List[str]:
    # ... function body ...
    pass
```

## 📑 4. Docstrings

All public classes, methods, and functions **must** include a docstring.

### ✍️ Recommended Format: Google Style
We recommend the Google Docstring format for its readability and comprehensive structure.

**Required Sections:**
* **Summary:** A brief, single-line description of the function/class.
* **Detailed Description:** (Optional) Elaborate on complex behavior, assumptions, or limitations.
* **`Args:`:** Lists all parameters, their types, and their purpose.
* **`Returns:`:** Describes the return value and its type.
* **`Raises:`:** Documents any specific exceptions that the function is expected to raise (e.g., `ValueError`, `FileNotFoundError`).
* **`Example:`:** Provides a minimal, runnable code snippet demonstrating usage.

**Example:**
```python
def calculate_checksum(data: str) -> str:
    """
    Calculates a cryptographic checksum (SHA-256) for the given string.

    Args:
        data: The input string data to be hashed.

    Returns:
        The SHA-256 hash string.

    Raises:
        TypeError: If the input data is not a string.

    Example:
        >>> calculate_checksum("hello world")
        'b94d27b9934d3e08a52e52d7da7dee35'
    """
    # implementation...
    pass
```

## ⚙️ 5. Error Handling and Context Management

### 🚀 Exception Handling
1. **Specific Exceptions:** Never use bare `except:` clauses. Always catch specific exceptions (e.g., `except FileNotFoundError:` instead of `except:`).
2. **Custom Exceptions:** Define and use custom exception classes (inheriting from `Exception`) for application-specific errors. This allows calling code to handle business logic failures explicitly.
3. **Minimize `try/except`:** If the goal is simply to suppress an error, consider a more robust mechanism or rethink the code flow.
4. **Log Errors:** When catching an exception, always log the error traceback and the exception object (`logger.exception("Failed to process data")`).

### 🚧 Context Managers
* **Mandatory Use:** Use `with` statements (context managers) for any resource that needs explicit cleanup (files, database connections, locks).
* **Example:**
```python
# Correct: Resource is guaranteed to be closed
with open("file.txt", "r") as f:
    data = f.read()
```

## 🗂️ 6. Logging Patterns

Logging is for observability, not for providing runtime feedback to the user. Use print statements only for debugging; they must be removed before merging.

### 🔬 Best Practices:
1. **Use `logging` Module:** Always use the built-in Python `logging` module.
2. **Structured Logging (Mandatory):** Log messages must be structured (JSON format is preferred). Include key-value pairs for context (e.g., `user_id`, `request_id`, `service_name`).
3. **Log Levels:** Use appropriate levels:
    * **DEBUG:** Detailed information, useful only when diagnosing problems.
    * **INFO:** Confirmation that things are working as expected (e.g., "User processed successfully").
    * **WARNING:** An issue that might cause problems but doesn't stop execution (e.g., "API endpoint deprecated").
    * **ERROR:** A failure that prevented a specific operation (e.g., "Database connection failed").
    * **CRITICAL:** A severe error that causes the application to shut down.
4. **Avoid Logging Sensitive Data:** Never log passwords, API keys, or highly sensitive PII.

**Example:**
```python
import logging
# Setup logger once at the module level
logger = logging.getLogger(__name__)

# Structured logging example
def process_user(user_id: int, data: dict):
    try:
        # ... logic ...
        logger.info("Successfully processed user data.", extra={"user_id": user_id, "source": "API"})
    except Exception as e:
        logger.error("Failed to process user data.", extra={"user_id": user_id, "reason": str(e)})
```

## 🧪 7. Testing Conventions

All new functionality must be accompanied by corresponding tests.

### 🎯 Testing Strategy
1. **Unit Tests:** Test the smallest isolated unit of code (functions, methods). These should be fast and deterministic.
2. **Integration Tests:** Test how different components interact (e.g., calling the database layer from the service layer).
3. **Acceptance/E2E Tests:** Simulate a full user journey through the application.

### 🛠️ Tools and Structure
* **Framework:** Use `pytest` as the primary testing framework.
* **Coverage:** Maintain a minimum of **85%** test coverage for core business logic modules.
* **Test Structure:** Place tests in a `tests/` directory mirroring the production code structure.
* **Fixtures:** Utilize `pytest` fixtures extensively to manage setup and teardown (e.g., creating mock database connections, initializing service objects).
* **Mocking:** Use `unittest.mock` (or `pytest-mock`) to isolate units under test and prevent actual dependencies (like external APIs or databases) from running during unit tests.

**Example:**
```python
# test_data_processor.py
import pytest
from data_processing import DataProcessor

def test_processor_initialization():
    processor = DataProcessor()
    assert processor is not None

def test_processor_calculate_valid(mock_db):
    # Use fixtures/mocks to ensure external dependencies are controlled
    mock_db.get_data.return_value = [{"id": 1, "value": 10}]
    processor = DataProcessor()
    result = processor.calculate_metrics()
    assert result['total'] == 10
```
"""Base classes and protocols for Elegant Objects checkers."""

from abc import ABC, abstractmethod
import ast


class ErrorCodes:
    """Centralized error message definitions."""

    # Naming violations (EO001-EO004)
    EO001 = "EO001 Class name '{name}' violates -er principle (describes what it does, not what it is)"
    EO002 = (
        "EO002 Method name '{name}' violates -er principle (should be noun, not verb)"
    )
    EO003 = (
        "EO003 Variable name '{name}' violates -er principle (should be noun, not verb)"
    )
    EO004 = (
        "EO004 Function name '{name}' violates -er principle (should be noun, not verb)"
    )

    # Core EO principles (EO005-EO008)
    EO005 = "EO005 Null (None) usage violates EO principle (avoid None)"
    EO006 = "EO006 Code in constructor violates EO principle (constructors should only assign parameters)"
    EO007 = "EO007 Getter/setter method '{name}' violates EO principle (avoid getters/setters)"
    EO008 = "EO008 Mutable object violation: '{name}' should be immutable"

    # Advanced EO principles (EO009-EO014)
    EO009 = (
        "EO009 Static method '{name}' violates EO principle (no static methods allowed)"
    )
    EO010 = "EO010 isinstance/type casting violates EO principle (avoid type discrimination)"
    EO011 = "EO011 Public method '{name}' without contract (Protocol/ABC) violates EO principle"
    EO012 = "EO012 Test method '{name}' contains non-assertThat statements (only assertThat allowed)"
    EO013 = "EO013 ORM/ActiveRecord pattern '{name}' violates EO principle"
    EO014 = "EO014 Implementation inheritance violates EO principle (class '{name}' inherits from non-abstract class)"


class Violation:
    """Represents a detected violation."""

    def __init__(self, line: int, column: int, message: str) -> None:
        self._line = line
        self._column = column
        self._message = message

    @property
    def line(self) -> int:
        return self._line

    @property
    def column(self) -> int:
        return self._column

    @property
    def message(self) -> str:
        return self._message


Violations = list[Violation]


class Principles(ABC):
    """Base class for Elegant Objects principles analysis."""

    def __init__(self, current_class: ast.ClassDef | None = None) -> None:
        self._current_class = current_class

    @abstractmethod
    def check(self, node: ast.AST) -> Violations:
        """Check node for violations and return list of detected violations."""

    def _violation(self, node: ast.AST, message: str) -> Violations:
        """Create a violation if node has location information."""
        if hasattr(node, "lineno") and hasattr(node, "col_offset"):
            return [Violation(node.lineno, node.col_offset, message)]
        return []

    def _is_method(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function is a method (has self parameter)."""
        if not node.args.args:
            return False
        return node.args.args[0].arg in ("self", "cls")

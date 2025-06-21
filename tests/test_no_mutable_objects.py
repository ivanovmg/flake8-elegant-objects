"""Unit tests for NoMutableObjects principle."""

import ast

from flake8_elegant_objects.base import Source
from flake8_elegant_objects.no_mutable_objects import NoMutableObjects


class TestNoMutableObjectsPrinciple:
    """Test cases for mutable objects violations detection."""

    def _check_code(self, code: str) -> list[str]:
        """Helper to check code and return violation messages."""
        tree = ast.parse(code)
        checker = NoMutableObjects()
        violations = []

        def visit(node: ast.AST, current_class: ast.ClassDef | None = None) -> None:
            if isinstance(node, ast.ClassDef):
                current_class = node
            source = Source(node, current_class, tree)
            violations.extend(checker.check(source))
            for child in ast.iter_child_nodes(node):
                visit(child, current_class)

        visit(tree)
        return [v.message for v in violations]

    def test_mutable_dataclass_violation(self) -> None:
        """Test detection of mutable dataclasses."""
        code = """
from dataclasses import dataclass

@dataclass
class MutableUser:
    name: str
    email: str

@dataclass()
class AnotherMutable:
    data: list
"""
        violations = self._check_code(code)
        assert len(violations) == 2
        assert all("EO008" in v for v in violations)
        assert any("MutableUser" in v for v in violations)
        assert any("AnotherMutable" in v for v in violations)

    def test_frozen_dataclass_valid(self) -> None:
        """Test that frozen dataclasses don't trigger violations."""
        code = """
from dataclasses import dataclass

@dataclass(frozen=True)
class ImmutableUser:
    name: str
    email: str

@dataclass(frozen=True, slots=True)
class ImmutableData:
    value: int
"""
        violations = self._check_code(code)
        assert len(violations) == 0

    def test_mutable_class_attributes_violation(self) -> None:
        """Test detection of mutable class attributes."""
        code = """
class DataContainer:
    items = []  # Mutable class attribute
    config = {}  # Mutable class attribute
    tags = set()  # Mutable class attribute

class ProcessorConfig:
    allowed_types = ["str", "int"]  # Mutable class attribute
"""
        violations = self._check_code(code)
        assert len(violations) == 4
        assert all("EO008" in v for v in violations)

    def test_mutable_type_constructors_violation(self) -> None:
        """Test detection of mutable type constructors as class attributes."""
        code = """
class Configuration:
    data = list()  # Mutable
    settings = dict()  # Mutable
    cache = set()  # Mutable
    buffer = bytearray()  # Mutable

class ValidConfig:
    name = str()  # Immutable - OK
    count = int()  # Immutable - OK
"""
        violations = self._check_code(code)
        assert len(violations) == 4
        assert all("EO008" in v for v in violations)

    def test_immutable_class_attributes_valid(self) -> None:
        """Test that immutable class attributes don't trigger violations."""
        code = """
class Constants:
    MAX_SIZE = 100
    DEFAULT_NAME = "user"
    PI = 3.14159
    ENABLED = True

class ImmutableData:
    empty_tuple = ()
    frozen_set = frozenset([1, 2, 3])
"""
        violations = self._check_code(code)
        assert len(violations) == 0

    def test_mixed_dataclass_parameters(self) -> None:
        """Test dataclass with various parameter combinations."""
        code = """
from dataclasses import dataclass

@dataclass(frozen=False)
class ExplicitlyMutable:
    name: str

@dataclass(order=True, frozen=True)
class FrozenWithOrder:
    value: int

@dataclass(unsafe_hash=True)  # No frozen=True
class UnsafeHash:
    data: str
"""
        violations = self._check_code(code)
        mutable_violations = [v for v in violations if "EO008" in v]
        assert len(mutable_violations) == 2
        assert any("ExplicitlyMutable" in v for v in mutable_violations)
        assert any("UnsafeHash" in v for v in mutable_violations)

    def test_regular_classes_ignored(self) -> None:
        """Test that regular classes (non-dataclass) don't trigger dataclass violations."""
        code = """
class RegularClass:
    def __init__(self, name):
        self.name = name

class AnotherRegular:
    data = []  # This should trigger mutable attribute violation
"""
        violations = self._check_code(code)
        # Should only have 1 violation for the mutable class attribute
        assert len(violations) == 1
        assert "data" in violations[0]
        assert "EO008" in violations[0]

    def test_instance_attributes_ignored(self) -> None:
        """Test that instance attributes in methods are ignored."""
        code = """
class DataProcessor:
    def __init__(self):
        self.data = []  # Instance attribute - OK
        self.cache = {}  # Instance attribute - OK

    def process(self):
        self.temp = set()  # Instance attribute - OK
"""
        violations = self._check_code(code)
        # Instance attributes should not trigger this violation
        mutable_violations = [v for v in violations if "EO008" in v]
        assert len(mutable_violations) == 0

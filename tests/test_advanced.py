"""Unit tests for advanced principles (AdvancedPrinciples)."""

import ast

from flake8_elegant_objects.advanced import AdvancedPrinciples
from flake8_elegant_objects.base import Source


class TestAdvancedPrinciples:
    """Test cases for advanced violations detection."""

    def _check_code(self, code: str) -> list[str]:
        """Helper to check code and return violation messages."""
        tree = ast.parse(code)
        checker = AdvancedPrinciples()
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

    def test_static_method_violation(self) -> None:
        """Test detection of static methods."""
        code = """
class Test:
    @staticmethod
    def process_data():
        pass

    @classmethod
    def create_instance(cls):
        pass
"""
        violations = self._check_code(code)
        static_violations = [v for v in violations if "EO009" in v]
        assert len(static_violations) == 2

    def test_isinstance_violation(self) -> None:
        """Test detection of isinstance usage."""
        code = """
def check_data(data):
    if isinstance(data, str):
        return True
    return False
"""
        violations = self._check_code(code)
        isinstance_violations = [v for v in violations if "EO010" in v]
        assert len(isinstance_violations) == 1

    def test_reflection_violation(self) -> None:
        """Test detection of reflection usage."""
        code = """
def check_object(obj):
    if hasattr(obj, "name"):
        name = getattr(obj, "name")
        setattr(obj, "name", "new")
        return callable(obj.method)
    return type(obj)
"""
        violations = self._check_code(code)
        reflection_violations = [v for v in violations if "EO010" in v]
        assert (
            len(reflection_violations) == 5
        )  # hasattr, getattr, setattr, callable, type

    def test_implementation_inheritance_violation(self) -> None:
        """Test detection of implementation inheritance."""
        code = """
class UserManager(list):
    pass

class DataProcessor(dict):
    pass
"""
        violations = self._check_code(code)
        inheritance_violations = [v for v in violations if "EO014" in v]
        assert len(inheritance_violations) == 2

    def test_valid_inheritance_patterns(self) -> None:
        """Test that valid inheritance patterns don't trigger violations."""
        code = """
from abc import ABC
from typing import Protocol

class ValidABC(ABC):
    pass

class ValidProtocol(Protocol):
    pass

class ValidException(Exception):
    pass

class ValidEnum(Enum):
    VALUE = 1
"""
        violations = self._check_code(code)
        inheritance_violations = [v for v in violations if "EO014" in v]
        assert len(inheritance_violations) == 0

    def test_test_method_violation(self) -> None:
        """Test detection of non-assertThat statements in test methods."""
        code = """
class TestUser:
    def test_user_creation(self):
        x = 5
        print("hello")
        user = User()
        assert user is not None
"""
        violations = self._check_code(code)
        test_violations = [v for v in violations if "EO012" in v]
        assert len(test_violations) == 4  # x=5, print, user=User(), assert

    def test_orm_pattern_violation(self) -> None:
        """Test detection of ORM/ActiveRecord patterns."""
        code = """
user = User()
user.save()
user.delete()

result = Model.find(123)
users = User.where(name="John")
"""
        violations = self._check_code(code)
        orm_violations = [v for v in violations if "EO013" in v]
        assert len(orm_violations) == 4  # save, delete, find, where

    def test_public_methods_without_contracts_violation(self) -> None:
        """Test detection of public methods without contracts."""
        code = """
class DataProcessor:
    def process_data(self):  # Should trigger violation
        pass

    def _private_method(self):  # Should not trigger violation
        pass

    @property
    def data(self):  # Should not trigger violation
        return self._data
"""
        violations = self._check_code(code)
        contract_violations = [v for v in violations if "EO011" in v]
        assert len(contract_violations) == 1
        assert "process_data" in contract_violations[0]

    def test_complex_inheritance_violation(self) -> None:
        """Test detection of complex inheritance scenarios."""
        code = """
from abc import ABC
from typing import Protocol

class ValidABC(ABC):
    pass

class ValidProtocol(Protocol):
    pass

class InvalidInheritance(str):
    pass

class AnotherInvalid(Exception):
    pass  # Exception is allowed
"""
        violations = self._check_code(code)
        inheritance_violations = [v for v in violations if "EO014" in v]
        assert len(inheritance_violations) == 1
        assert "InvalidInheritance" in inheritance_violations[0]

    def test_mixed_violations(self) -> None:
        """Test class with multiple advanced principle violations."""
        code = """
class DataManager(list):  # EO014 - implementation inheritance
    @staticmethod  # EO009 - static method
    def process(data):
        if isinstance(data, str):  # EO010 - type discrimination
            return data.upper()
        return None

    def save_data(self):  # EO011 - no contract
        self.save()  # EO013 - ORM pattern
"""
        violations = self._check_code(code)

        static_violations = [v for v in violations if "EO009" in v]
        isinstance_violations = [v for v in violations if "EO010" in v]
        contract_violations = [v for v in violations if "EO011" in v]
        orm_violations = [v for v in violations if "EO013" in v]
        inheritance_violations = [v for v in violations if "EO014" in v]

        assert len(static_violations) >= 1
        assert len(isinstance_violations) >= 1
        assert len(contract_violations) >= 1
        assert len(orm_violations) >= 1
        assert len(inheritance_violations) >= 1

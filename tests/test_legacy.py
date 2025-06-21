"""Unit tests for Elegant Objects flake8 plugin violations."""

import ast

from flake8_elegant_objects import ElegantObjectsPlugin


class TestEOViolations:
    """Test cases for Elegant Objects violations detection."""

    def _check_code(self, code: str) -> list[tuple[int, int, str]]:
        """Helper to check code and return violations."""
        tree = ast.parse(code)
        checker = ElegantObjectsPlugin(tree)
        return [(line, col, msg) for line, col, msg, _ in checker.run()]

    def test_er_class_name_violation(self) -> None:
        """Test detection of -er class names."""
        code = """
class Manager:
    pass
"""
        violations = self._check_code(code)
        assert len(violations) == 1
        assert "EO001" in violations[0][2]
        assert "Manager" in violations[0][2]

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
        static_violations = [v for v in violations if "EO009" in v[2]]
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
        isinstance_violations = [v for v in violations if "EO010" in v[2]]
        assert len(isinstance_violations) == 1

    def test_getter_setter_violation(self) -> None:
        """Test detection of getter/setter methods."""
        code = """
class User:
    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def getName(self):
        return self.name
"""
        violations = self._check_code(code)
        getter_setter_violations = [v for v in violations if "EO007" in v[2]]
        assert len(getter_setter_violations) == 3

    def test_none_usage_violation(self) -> None:
        """Test detection of None usage."""
        code = """
def get_user():
    return None

value = None
"""
        violations = self._check_code(code)
        none_violations = [v for v in violations if "EO005" in v[2]]
        assert len(none_violations) == 2

    def test_implementation_inheritance_violation(self) -> None:
        """Test detection of implementation inheritance."""
        code = """
class UserManager(list):
    pass

class DataProcessor(dict):
    pass
"""
        violations = self._check_code(code)
        inheritance_violations = [v for v in violations if "EO014" in v[2]]
        assert len(inheritance_violations) == 2

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
        test_violations = [v for v in violations if "EO012" in v[2]]
        assert len(test_violations) == 3  # x=5, print, user=User() (assert is valid)

    def test_procedural_function_name_violation(self) -> None:
        """Test detection of procedural function names."""
        code = """
def analyze_data():
    pass

def process_information():
    pass

def handle_request():
    pass
"""
        violations = self._check_code(code)
        function_violations = [v for v in violations if "EO004" in v[2]]
        assert len(function_violations) == 3

    def test_procedural_method_name_violation(self) -> None:
        """Test detection of procedural method names."""
        code = """
class DataHandler:
    def process_data(self):
        pass

    def analyze_results(self):
        pass
"""
        violations = self._check_code(code)
        method_violations = [v for v in violations if "EO002" in v[2]]
        assert len(method_violations) == 2

    def test_procedural_variable_name_violation(self) -> None:
        """Test detection of procedural variable names."""
        code = """
manager = DataManager()
processor = DataProcessor()
handler = RequestHandler()
"""
        violations = self._check_code(code)
        variable_violations = [v for v in violations if "EO003" in v[2]]
        assert len(variable_violations) == 3

    def test_allowed_exceptions(self) -> None:
        """Test that allowed exceptions don't trigger violations."""
        code = """
class User:
    pass

class Order:
    pass

def _private_method():
    pass

def __special_method__(self):
    pass
"""
        violations = self._check_code(code)
        # Should not have violations for User, Order, or private methods
        class_violations = [v for v in violations if "EO001" in v[2]]
        function_violations = [v for v in violations if "EO004" in v[2]]
        assert len(class_violations) == 0
        assert len(function_violations) == 0

    def test_mutable_class_violation(self) -> None:
        """Test detection of mutable classes."""
        code = """
from dataclasses import dataclass

@dataclass
class MutableUser:
    name: str

@dataclass(frozen=True)
class ImmutableUser:
    name: str
"""
        violations = self._check_code(code)
        mutable_violations = [v for v in violations if "EO008" in v[2]]
        assert len(mutable_violations) == 1
        assert "MutableUser" in mutable_violations[0][2]

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
        orm_violations = [v for v in violations if "EO013" in v[2]]
        assert len(orm_violations) == 4  # save, delete, find, where

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
        reflection_violations = [v for v in violations if "EO010" in v[2]]
        assert (
            len(reflection_violations) == 5
        )  # hasattr, getattr, setattr, callable, type

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
        inheritance_violations = [v for v in violations if "EO014" in v[2]]
        assert len(inheritance_violations) == 1
        assert "InvalidInheritance" in inheritance_violations[0][2]

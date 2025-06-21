"""Unit tests for naming principle (NoErNamePrinciple)."""

import ast

from flake8_elegant_objects.base import Source
from flake8_elegant_objects.no_er_name import NoErName


class TestNamingPrinciple:
    """Test cases for naming violations detection."""

    def _check_code(self, code: str) -> list[str]:
        """Helper to check code and return violation messages."""
        tree = ast.parse(code)
        checker = NoErName()
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

    def test_er_class_name_violation(self) -> None:
        """Test detection of -er class names."""
        code = """
class Manager:
    pass

class Controller:
    pass

class Helper:
    pass
"""
        violations = self._check_code(code)
        assert len(violations) == 3
        assert any("Manager" in v and "EO001" in v for v in violations)
        assert any("Controller" in v and "EO001" in v for v in violations)
        assert any("Helper" in v and "EO001" in v for v in violations)

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
        assert len(violations) == 3
        assert any("analyze_data" in v and "EO004" in v for v in violations)
        assert any("process_information" in v and "EO004" in v for v in violations)
        assert any("handle_request" in v and "EO004" in v for v in violations)

    def test_procedural_method_name_violation(self) -> None:
        """Test detection of procedural method names."""
        code = """
class DataHandler:
    def process_data(self):
        pass

    def analyze_results(self):
        pass

    def get_data(self):
        pass
"""
        violations = self._check_code(code)
        method_violations = [v for v in violations if "EO002" in v]
        assert len(method_violations) == 3
        assert any("process_data" in v for v in method_violations)
        assert any("analyze_results" in v for v in method_violations)
        assert any("get_data" in v for v in method_violations)

    def test_procedural_variable_name_violation(self) -> None:
        """Test detection of procedural variable names."""
        code = """
manager = DataManager()
processor = DataProcessor()
handler = RequestHandler()
"""
        violations = self._check_code(code)
        assert len(violations) == 3
        assert any("manager" in v and "EO003" in v for v in violations)
        assert any("processor" in v and "EO003" in v for v in violations)
        assert any("handler" in v and "EO003" in v for v in violations)

    def test_allowed_exceptions(self) -> None:
        """Test that allowed exceptions don't trigger violations."""
        code = """
class User:
    pass

class Order:
    pass

class Buffer:
    pass

def _private_method():
    pass

def __special_method__(self):
    pass

SERVER = "localhost"
"""
        violations = self._check_code(code)
        # Should not have violations for User, Order, Buffer, or private methods
        assert len(violations) == 0

    def test_compound_names_with_er_suffixes(self) -> None:
        """Test detection of compound names with -er suffixes."""
        code = """
class UserManager:
    pass

class DataProcessor:
    pass

class RequestHandler:
    pass
"""
        violations = self._check_code(code)
        assert len(violations) == 3
        assert any("UserManager" in v and "EO001" in v for v in violations)
        assert any("DataProcessor" in v and "EO001" in v for v in violations)
        assert any("RequestHandler" in v and "EO001" in v for v in violations)

    def test_camel_case_procedural_names(self) -> None:
        """Test detection of camelCase procedural names."""
        code = """
def analyzeData():
    pass

def processInformation():
    pass

class DataProcessor:
    def handleRequest(self):
        pass
"""
        violations = self._check_code(code)
        assert len(violations) >= 3
        assert any("analyzeData" in v and "EO004" in v for v in violations)
        assert any("processInformation" in v and "EO004" in v for v in violations)
        assert any("handleRequest" in v and "EO002" in v for v in violations)

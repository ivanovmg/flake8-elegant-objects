"""Core principles checker for Elegant Objects violations."""

import ast

from .base import ErrorCodes, Principles, Violations


class CorePrinciples(Principles):
    """Checks for core EO principles: no null, no constructor code, no getters/setters, no mutable objects."""

    def check(self, node: ast.AST) -> Violations:
        """Check node for core principle violations."""
        violations = []

        if isinstance(node, ast.Constant):
            violations.extend(self._check_none_usage(node))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            violations.extend(self._check_constructor_code(node))
            violations.extend(self._check_getters_setters(node))
        elif isinstance(node, ast.ClassDef):
            violations.extend(self._check_mutable_class(node))

        return violations

    def _check_none_usage(self, node: ast.Constant) -> Violations:
        """Check for None usage violations."""
        if node.value is None:
            return self._violation(node, ErrorCodes.EO005)
        return []

    def _check_constructor_code(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Violations:
        """Check for code in constructors beyond parameter assignments."""
        if node.name != "__init__" or not self._is_method(node):
            return []

        # Constructors should only contain assignments to self.attribute = parameter
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                # Check if it's a simple self.attr = param assignment
                if len(stmt.targets) == 1 and isinstance(
                    stmt.targets[0], ast.Attribute
                ):
                    target = stmt.targets[0]
                    if isinstance(target.value, ast.Name) and target.value.id == "self":
                        # This is a self.attr assignment, check if value is a simple name
                        if not isinstance(stmt.value, ast.Name):
                            return self._violation(stmt, ErrorCodes.EO006)
                    else:
                        return self._violation(stmt, ErrorCodes.EO006)
                else:
                    return self._violation(stmt, ErrorCodes.EO006)
            elif not isinstance(stmt, ast.Pass):  # Allow pass statements
                return self._violation(stmt, ErrorCodes.EO006)

        return []

    def _check_getters_setters(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Violations:
        """Check for getter/setter methods."""
        if not self._is_method(node) or node.name.startswith("_"):
            return []

        name = node.name.lower()
        original_name = node.name

        # Check for getter patterns
        if (
            name.startswith("get_")
            or (
                name.startswith("get")
                and len(original_name) > 3
                and original_name[3].isupper()
            )
            or name == "get"
        ):
            return self._violation(node, ErrorCodes.EO007.format(name=node.name))

        # Check for setter patterns
        if (
            name.startswith("set_")
            or (
                name.startswith("set")
                and len(original_name) > 3
                and original_name[3].isupper()
            )
            or name == "set"
        ):
            return self._violation(node, ErrorCodes.EO007.format(name=node.name))

        return []

    def _check_mutable_class(self, node: ast.ClassDef) -> Violations:
        """Check for mutable class violations."""
        # Look for @dataclass decorator without frozen=True
        has_dataclass = False
        has_frozen = False

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                has_dataclass = True
            elif isinstance(decorator, ast.Call):
                if (
                    isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "dataclass"
                ):
                    has_dataclass = True
                    # Check for frozen=True
                    for keyword in decorator.keywords:
                        if keyword.arg == "frozen" and isinstance(
                            keyword.value, ast.Constant
                        ):
                            if keyword.value.value is True:
                                has_frozen = True

        # If it's a dataclass without frozen=True, it's mutable
        if has_dataclass and not has_frozen:
            return self._violation(node, ErrorCodes.EO008.format(name=node.name))

        # Check for mutable instance attributes in class body
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        # This is a class attribute, check if it's mutable
                        if self._is_mutable_type(stmt.value):
                            return self._violation(
                                stmt, ErrorCodes.EO008.format(name=target.id)
                            )

        return []

    def _is_mutable_type(self, node: ast.AST) -> bool:
        """Check if a node represents a mutable type."""
        if isinstance(node, ast.List | ast.Dict | ast.Set):
            return True

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            mutable_types = {"list", "dict", "set", "bytearray"}
            return node.func.id in mutable_types

        return False

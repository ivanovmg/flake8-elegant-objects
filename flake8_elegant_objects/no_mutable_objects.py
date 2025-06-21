"""No mutable objects principle checker for Elegant Objects violations."""

import ast

from .base import ErrorCodes, Source, Violations, violation


class NoMutableObjects:
    """Checks for mutable object violations (EO008)."""

    def check(self, source: Source) -> Violations:
        """Check source for mutable object violations."""
        node = source.node
        if not isinstance(node, ast.ClassDef):
            return []
        return self._check_mutable_class(node)

    def _check_mutable_class(self, node: ast.ClassDef) -> Violations:
        """Check for mutable class violations."""
        violations = []

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
            violations.extend(violation(node, ErrorCodes.EO008.format(name=node.name)))

        # Check for mutable instance attributes in class body
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        # This is a class attribute, check if it's mutable
                        if self._is_mutable_type(stmt.value):
                            violations.extend(
                                violation(stmt, ErrorCodes.EO008.format(name=target.id))
                            )

        return violations

    def _is_mutable_type(self, node: ast.AST) -> bool:
        """Check if a node represents a mutable type."""
        if isinstance(node, ast.List | ast.Dict | ast.Set):
            return True

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            mutable_types = {"list", "dict", "set", "bytearray"}
            return node.func.id in mutable_types

        return False

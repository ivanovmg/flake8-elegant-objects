"""No static methods principle checker for Elegant Objects violations."""

import ast

from .base import ErrorCodes, Source, Violations, violation


class NoStatic:
    """Checks for static method violations (EO009)."""

    def check(self, source: Source) -> Violations:
        """Check source for static method violations."""
        node = source.node

        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            return self._check_static_methods(node)

        return []

    def _check_static_methods(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Violations:
        """Check for static methods violations."""
        # Check for @staticmethod decorator
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in {
                "staticmethod",
                "classmethod",
            }:
                return violation(node, ErrorCodes.EO009.format(name=node.name))
        return []

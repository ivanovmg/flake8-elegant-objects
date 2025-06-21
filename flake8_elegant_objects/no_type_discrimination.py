"""No type discrimination principle checker for Elegant Objects violations."""

import ast

from .base import ErrorCodes, Source, Violations, violation


class NoTypeDiscrimination:
    """Checks for type discrimination violations (EO010)."""

    def check(self, source: Source) -> Violations:
        """Check source for type discrimination violations."""
        node = source.node

        if isinstance(node, ast.Call):
            return self._check_isinstance_usage(node)

        return []

    def _check_isinstance_usage(self, node: ast.Call) -> Violations:
        """Check for isinstance, type casting, or reflection usage."""
        if isinstance(node.func, ast.Name):
            forbidden_funcs = {
                "isinstance",
                "type",
                "hasattr",
                "getattr",
                "setattr",
                "delattr",
                "callable",
            }
            if node.func.id in forbidden_funcs:
                return violation(node, ErrorCodes.EO010)
        return []

"""No null principle checker for Elegant Objects violations."""

import ast

from .base import ErrorCodes, Source, Violations, violation


class NoNull:
    """Checks for None usage violations (EO005)."""

    def check(self, source: Source) -> Violations:
        """Check source for None usage violations."""
        node = source.node
        if isinstance(node, ast.Constant) and node.value is None:
            return violation(node, ErrorCodes.EO005)
        return []
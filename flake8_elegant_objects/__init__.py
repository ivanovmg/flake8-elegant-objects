"""Flake8 plugin for Elegant Objects violations.

This plugin detects violations of the Elegant Objects principles including
"-er" entities, null usage, mutable objects, static methods, and more.

Based on Yegor Bugayenko's principles from elegantobjects.org
"""

import ast
from collections.abc import Iterator
from typing import Any

from .advanced import AdvancedPrinciples
from .base import Violation
from .core import CorePrinciples
from .naming import NoErNamePrinciple


class ElegantObjectsPlugin:
    """Flake8 plugin to check for Elegant Objects violations."""

    name = "flake8-elegant-objects"
    version = "1.0.0"

    def __init__(self, tree: ast.AST) -> None:
        self.tree = tree

    def run(self) -> Iterator[tuple[int, int, str, type["ElegantObjectsPlugin"]]]:
        """Run the checker and yield errors."""
        for violation in self.visit(self.tree, None):
            yield (violation.line, violation.column, violation.message, type(self))

    def visit(
        self, node: ast.AST, current_class: ast.ClassDef | None = None
    ) -> Iterator[Violation]:
        """Visit AST nodes and check for violations."""
        if isinstance(node, ast.ClassDef):
            current_class = node

        yield from self._check_principles(node, current_class)

        for child in ast.iter_child_nodes(node):
            yield from self.visit(child, current_class)

    def _check_principles(
        self, node: ast.AST, current_class: ast.ClassDef | None
    ) -> Iterator[Violation]:
        """Check all principles against the given node."""
        principles = [
            NoErNamePrinciple(current_class),
            CorePrinciples(current_class),
            AdvancedPrinciples(current_class),
        ]

        for principle in principles:
            violations = principle.check(node)
            yield from violations


# Entry point for flake8 plugin registration
def factory(_app: Any) -> type[ElegantObjectsPlugin]:
    """Factory function for flake8 plugin."""
    return ElegantObjectsPlugin

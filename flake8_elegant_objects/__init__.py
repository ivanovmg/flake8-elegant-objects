"""Flake8 plugin for Elegant Objects violations.

This plugin detects violations of the Elegant Objects principles including
"-er" entities, null usage, mutable objects, static methods, and more.

Based on Yegor Bugayenko's principles from elegantobjects.org
"""

import ast
from collections.abc import Iterator
from typing import Any

from .advanced import AdvancedPrinciples
from .core import CorePrinciples
from .naming import NamingViolations


class ElegantObjectsViolation:
    """Flake8 plugin to check for Elegant Objects violations."""

    name = "flake8-elegant-objects"
    version = "1.0.0"

    def __init__(self, tree: ast.AST) -> None:
        self.tree = tree
        self.errors: list[tuple[int, int, str]] = []
        self._current_class: ast.ClassDef | None = None

    def run(self) -> Iterator[tuple[int, int, str, type["ElegantObjectsViolation"]]]:
        """Run the checker and yield errors."""
        self.visit(self.tree)
        for line, col, msg in self.errors:
            yield (line, col, msg, type(self))

    def visit(self, node: ast.AST) -> None:
        """Visit AST nodes and check for violations."""
        if isinstance(node, ast.ClassDef):
            # Store current class context
            previous_class = self._current_class
            self._current_class = node

            # Run all analysis on the class node
            self._run_analysis(node)

            # Visit child nodes with class context
            for child in ast.iter_child_nodes(node):
                self.visit(child)

            # Restore previous class context
            self._current_class = previous_class
            return

        # Run analysis on other nodes
        self._run_analysis(node)

        # Continue visiting child nodes
        for child in ast.iter_child_nodes(node):
            self.visit(child)

    def _run_analysis(self, node: ast.AST) -> None:
        """Run all violation analysis on the given node."""
        analyses = [
            NamingViolations(self._current_class),
            CorePrinciples(self._current_class),
            AdvancedPrinciples(self._current_class),
        ]

        for analysis in analyses:
            violations = analysis.analyze(node)
            for violation in violations:
                self.errors.append((violation.line, violation.column, violation.message))


# Entry point for flake8 plugin registration
def factory(_app: Any) -> type[ElegantObjectsViolation]:
    """Factory function for flake8 plugin."""
    return ElegantObjectsViolation
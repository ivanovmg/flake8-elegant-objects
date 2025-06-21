"""Standalone command-line interface for flake8-elegant-objects."""

import argparse
import ast
import sys

from .advanced import AdvancedPrinciples
from .base import Principle, Source
from .naming import NoErNamePrinciple
from .no_constructor_code import NoConstructorCode
from .no_getters_setters import NoGettersSetters
from .no_mutable_objects import NoMutableObjects
from .no_null import NoNull


class ElegantObjectsAnalysis:
    """Standalone analysis for Elegant Objects violations."""

    def __init__(self, tree: ast.AST) -> None:
        self.tree = tree
        self.errors: list[tuple[int, int, str]] = []
        self._current_class: ast.ClassDef | None = None

    def analyze(self) -> list[tuple[int, int, str]]:
        """Analyze for violations and return list of errors."""
        self.visit(self.tree)
        return self.errors

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
        source = Source(node, self._current_class)
        analyses: list[Principle] = [
            NoErNamePrinciple(),
            NoNull(),
            NoConstructorCode(),
            NoGettersSetters(),
            NoMutableObjects(),
            AdvancedPrinciples(),
        ]

        for analysis in analyses:
            violations = analysis.check(source)
            for violation in violations:
                self.errors.append(
                    (violation.line, violation.column, violation.message)
                )


def main() -> None:
    """Standalone command-line interface."""
    parser = argparse.ArgumentParser(
        description="Check Python files for Elegant Objects violations"
    )
    parser.add_argument("files", nargs="+", help="Python files to check")
    parser.add_argument(
        "--show-source",
        action="store_true",
        help="Show source code context for violations",
    )

    args = parser.parse_args()

    total_errors = 0

    for file_path in args.files:
        if not file_path.endswith(".py"):
            continue

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=file_path)
            analysis = ElegantObjectsAnalysis(tree)

            file_errors = 0
            for line, col, msg in analysis.analyze():
                print(f"{file_path}:{line}:{col}: {msg}")

                if args.show_source:
                    lines = source.split("\n")
                    if 0 <= line - 1 < len(lines):
                        print(f"    {lines[line - 1].strip()}")
                    print()

                file_errors += 1
                total_errors += 1

            if file_errors == 0:
                print(f"{file_path}: No violations found ✓")

        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)

    if total_errors > 0:
        print(f"\nTotal violations found: {total_errors}")
        sys.exit(1)
    else:
        print("\nAll files comply with Elegant Objects principles! ✓")


if __name__ == "__main__":
    main()

"""Flake8 plugin for Elegant Objects "-er" principle violations.

This plugin detects violations of the Elegant Objects principle that prohibits
"-er" entities (classes, methods, variables that describe what they do rather than what they are).

Based on Yegor Bugayenko's principles from elegantobjects.org
"""

import ast
from collections.abc import Iterator
import re
from typing import Any, ClassVar


class ElegantObjectsViolation:
    """Flake8 plugin to check for Elegant Objects -er principle violations."""

    name = "flake8-elegant-objects"
    version = "1.0.0"

    # Error codes
    EO001 = "EO001 Class name '{name}' violates -er principle (describes what it does, not what it is)"
    EO002 = (
        "EO002 Method name '{name}' violates -er principle (should be noun, not verb)"
    )
    EO003 = (
        "EO003 Variable name '{name}' violates -er principle (should be noun, not verb)"
    )
    EO004 = (
        "EO004 Function name '{name}' violates -er principle (should be noun, not verb)"
    )
    EO005 = "EO005 Null (None) usage violates EO principle (avoid None)"
    EO006 = "EO006 Code in constructor violates EO principle (constructors should only assign parameters)"
    EO007 = "EO007 Getter/setter method '{name}' violates EO principle (avoid getters/setters)"
    EO008 = "EO008 Mutable object violation: '{name}' should be immutable"
    EO009 = (
        "EO009 Static method '{name}' violates EO principle (no static methods allowed)"
    )
    EO010 = "EO010 isinstance/type casting violates EO principle (avoid type discrimination)"
    EO011 = "EO011 Public method '{name}' without contract (Protocol/ABC) violates EO principle"
    EO012 = "EO012 Test method '{name}' contains non-assertThat statements (only assertThat allowed)"
    EO013 = "EO013 ORM/ActiveRecord pattern '{name}' violates EO principle"
    EO014 = "EO014 Implementation inheritance violates EO principle (class '{name}' inherits from non-abstract class)"

    # Hall of shame: common -er suffixes (from elegantobjects.org)
    ER_SUFFIXES: ClassVar[set[str]] = {
        "accumulator",
        "adapter",
        "aggregator",
        "analyzer",
        "broker",
        "builder",
        "calculator",
        "checker",
        "collector",
        "compiler",
        "compressor",
        "consumer",
        "controller",
        "converter",
        "coordinator",
        "creator",
        "decoder",
        "decompressor",
        "deserializer",
        "dispatcher",
        "displayer",
        "encoder",
        "evaluator",
        "executor",
        "exporter",
        "factory",
        "fetcher",
        "filter",
        "finder",
        "formatter",
        "generator",
        "handler",
        "helper",
        "importer",
        "interpreter",
        "joiner",
        "listener",
        "loader",
        "manager",
        "mediator",
        "merger",
        "monitor",
        "observer",
        "orchestrator",
        "organizer",
        "parser",
        "printer",
        "processor",
        "producer",
        "provider",
        "reader",
        "renderer",
        "reporter",
        "router",
        "runner",
        "saver",
        "scanner",
        "scheduler",
        "serializer",
        "sorter",
        "splitter",
        "supplier",
        "synchronizer",
        "tracker",
        "transformer",
        "validator",
        "worker",
        "wrapper",
        "writer",
    }

    # Common procedural verbs that should be nouns
    PROCEDURAL_VERBS: ClassVar[set[str]] = {
        "accumulate",
        "add",
        "aggregate",
        "analyze",
        "append",
        "build",
        "calculate",
        "change",
        "check",
        "clean",
        "clear",
        "close",
        "collect",
        "compile",
        "compress",
        "control",
        "convert",
        "create",
        "decode",
        "decompress",
        "delete",
        "deserialize",
        "dispatch",
        "display",
        "do",
        "encode",
        "evaluate",
        "execute",
        "export",
        "fetch",
        "filter",
        "find",
        "format",
        "generate",
        "get",
        "handle",
        "hide",
        "import",
        "insert",
        "interpret",
        "join",
        "load",
        "manage",
        "merge",
        "modify",
        "open",
        "organize",
        "parse",
        "pause",
        "prepend",
        "print",
        "process",
        "put",
        "read",
        "receive",
        "refresh",
        "remove",
        "render",
        "reset",
        "resume",
        "retrieve",
        "route",
        "run",
        "save",
        "schedule",
        "search",
        "send",
        "serialize",
        "set",
        "show",
        "sort",
        "split",
        "start",
        "stop",
        "store",
        "transform",
        "transmit",
        "update",
        "validate",
        "write",
    }

    # Allowed exceptions (common patterns that are OK)
    ALLOWED_EXCEPTIONS: ClassVar[set[str]] = {
        "buffer",
        "character",
        "cluster",
        "container",
        "counter",
        "error",
        "footer",
        "header",
        "identifier",
        "number",
        "order",
        "owner",
        "parameter",
        "pointer",
        "register",
        "server",
        "timer",
        "user",
    }

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

            self._check_class_name(node)
            self._check_mutable_class(node)
            self._check_implementation_inheritance(node)

            # Visit child nodes with class context
            for child in ast.iter_child_nodes(node):
                self.visit(child)

            # Restore previous class context
            self._current_class = previous_class
            return

        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            self._check_function_name(node)
            self._check_constructor_code(node)
            self._check_getters_setters(node)
            self._check_static_methods(node)
            self._check_public_methods_contracts(node)
            self._check_test_methods(node)
        elif isinstance(node, ast.Assign):
            self._check_variable_assignment(node)
        elif isinstance(node, ast.AnnAssign):
            self._check_annotated_assignment(node)
        elif isinstance(node, ast.Constant):
            self._check_none_usage(node)
        elif isinstance(node, ast.Call):
            self._check_isinstance_usage(node)
            self._check_orm_patterns(node)

        # Continue visiting child nodes
        for child in ast.iter_child_nodes(node):
            self.visit(child)

    def _check_class_name(self, node: ast.ClassDef) -> None:
        """Check if class name violates -er principle."""
        name = node.name.lower()

        # Skip if it's an allowed exception
        if name in self.ALLOWED_EXCEPTIONS:
            return

        # Check for -er suffixes (the hall of shame)
        for suffix in self.ER_SUFFIXES:
            if name.endswith(suffix):
                self.errors.append(
                    (node.lineno, node.col_offset, self.EO001.format(name=node.name))
                )
                return

        # Check for procedural patterns in compound names
        if self._contains_procedural_pattern(name):
            self.errors.append(
                (node.lineno, node.col_offset, self.EO001.format(name=node.name))
            )

    def _check_function_name(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check if function/method name violates -er principle."""
        # Skip special methods (__init__, __str__, etc.)
        if node.name.startswith("_"):
            return

        # Skip common property patterns
        if node.name in ("property", "getter", "setter"):
            return

        name = node.name.lower()

        # Check for procedural verbs
        if self._starts_with_procedural_verb(name):
            # Determine if it's a method or standalone function
            error_code = self.EO002 if self._is_method(node) else self.EO004
            self.errors.append(
                (node.lineno, node.col_offset, error_code.format(name=node.name))
            )

    def _check_variable_assignment(self, node: ast.Assign) -> None:
        """Check variable names in assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._check_variable_name(target)

    def _check_annotated_assignment(self, node: ast.AnnAssign) -> None:
        """Check variable names in annotated assignments."""
        if isinstance(node.target, ast.Name):
            self._check_variable_name(node.target)

    def _check_variable_name(self, node: ast.Name) -> None:
        """Check if variable name violates -er principle."""
        # Skip private variables and common patterns
        if node.id.startswith("_") or node.id.isupper():
            return

        name = node.id.lower()

        # Skip if it's an allowed exception
        if name in self.ALLOWED_EXCEPTIONS:
            return

        # Check for -er suffixes
        for suffix in self.ER_SUFFIXES:
            if name.endswith(suffix):
                self.errors.append(
                    (node.lineno, node.col_offset, self.EO003.format(name=node.id))
                )
                return

        # Check for procedural verbs as variable names
        if self._starts_with_procedural_verb(name):
            self.errors.append(
                (node.lineno, node.col_offset, self.EO003.format(name=node.id))
            )

    def _contains_procedural_pattern(self, name: str) -> bool:
        """Check if name contains procedural patterns."""
        # Split camelCase/snake_case into words
        words = re.findall(r"[a-z]+", name)

        # Check if any word is a procedural verb
        return any(word in self.PROCEDURAL_VERBS for word in words)

    def _starts_with_procedural_verb(self, name: str) -> bool:
        """Check if name starts with a procedural verb."""
        # Split camelCase/snake_case and check first word
        words = re.findall(r"[a-z]+", name)
        if not words:
            return False

        first_word = words[0]
        return first_word in self.PROCEDURAL_VERBS

    def _is_method(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function is a method (has self parameter)."""
        if not node.args.args:
            return False
        return node.args.args[0].arg in ("self", "cls")

    def _check_none_usage(self, node: ast.AST) -> None:
        """Check for None usage violations."""
        # Check if the constant is None
        if (hasattr(node, "value") and node.value is None) or (
            hasattr(node, "id") and getattr(node, "id", None) == "None"
        ):
            if hasattr(node, "lineno") and hasattr(node, "col_offset"):
                self.errors.append((node.lineno, node.col_offset, self.EO005))

    def _check_constructor_code(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check for code in constructors beyond parameter assignments."""
        if node.name != "__init__" or not self._is_method(node):
            return

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
                            self.errors.append(
                                (stmt.lineno, stmt.col_offset, self.EO006)
                            )
                    else:
                        self.errors.append((stmt.lineno, stmt.col_offset, self.EO006))
                else:
                    self.errors.append((stmt.lineno, stmt.col_offset, self.EO006))
            elif not isinstance(stmt, ast.Pass):  # Allow pass statements
                self.errors.append((stmt.lineno, stmt.col_offset, self.EO006))

    def _check_getters_setters(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check for getter/setter methods."""
        if not self._is_method(node) or node.name.startswith("_"):
            return

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
            self.errors.append(
                (node.lineno, node.col_offset, self.EO007.format(name=node.name))
            )

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
            self.errors.append(
                (node.lineno, node.col_offset, self.EO007.format(name=node.name))
            )

    def _check_mutable_class(self, node: ast.ClassDef) -> None:
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
            self.errors.append(
                (node.lineno, node.col_offset, self.EO008.format(name=node.name))
            )

        # Check for mutable instance attributes in class body
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        # This is a class attribute, check if it's mutable
                        if self._is_mutable_type(stmt.value):
                            self.errors.append(
                                (
                                    stmt.lineno,
                                    stmt.col_offset,
                                    self.EO008.format(name=target.id),
                                )
                            )

    def _is_mutable_type(self, node: ast.AST) -> bool:
        """Check if a node represents a mutable type."""
        if isinstance(node, ast.List | ast.Dict | ast.Set):
            return True

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            mutable_types = {"list", "dict", "set", "bytearray"}
            return node.func.id in mutable_types

        return False

    def _check_static_methods(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check for static methods violations."""
        # Check for @staticmethod decorator
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in {
                "staticmethod",
                "classmethod",
            }:
                self.errors.append(
                    (node.lineno, node.col_offset, self.EO009.format(name=node.name))
                )

    def _check_isinstance_usage(self, node: ast.Call) -> None:
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
                self.errors.append((node.lineno, node.col_offset, self.EO010))

    def _check_public_methods_contracts(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check if public methods have contracts (Protocol/ABC)."""
        # Skip private methods, special methods, and property decorators
        if node.name.startswith("_") or any(
            isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list
        ):
            return

        # Skip if not a method (no current class context)
        if not self._current_class or not self._is_method(node):
            return

        # Check if class implements a protocol or ABC
        has_contract = any(
            (isinstance(base, ast.Name) and base.id in {"Protocol", "ABC"})
            or (isinstance(base, ast.Attribute) and base.attr in {"Protocol", "ABC"})
            or (
                isinstance(base, ast.Attribute)
                and isinstance(base.value, ast.Name)
                and base.value.id in {"abc", "typing"}
                and base.attr in {"Protocol", "ABC"}
            )
            for base in self._current_class.bases
        )

        # Also check for abstract decorators
        has_abstract_decorator = any(
            (isinstance(d, ast.Name) and d.id in {"abstractmethod", "abstractproperty"})
            or (
                isinstance(d, ast.Attribute)
                and d.attr in {"abstractmethod", "abstractproperty"}
            )
            for d in node.decorator_list
        )

        # Skip if class has contracts or method is abstract
        if has_contract or has_abstract_decorator:
            return

        # Public method without contract - violation
        self.errors.append(
            (node.lineno, node.col_offset, self.EO011.format(name=node.name))
        )

    def _check_test_methods(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check that test methods only contain assertThat statements."""
        if not node.name.startswith("test_"):
            return

        for stmt in node.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                # Check if it's an assertThat call
                if (
                    isinstance(stmt.value.func, ast.Name)
                    and stmt.value.func.id == "assertThat"
                ) or (
                    isinstance(stmt.value.func, ast.Attribute)
                    and stmt.value.func.attr == "assertThat"
                ):
                    continue
                self.errors.append(
                    (stmt.lineno, stmt.col_offset, self.EO012.format(name=node.name))
                )
            elif not isinstance(stmt, ast.Pass):  # Allow pass statements
                self.errors.append(
                    (stmt.lineno, stmt.col_offset, self.EO012.format(name=node.name))
                )

    def _check_orm_patterns(self, node: ast.Call) -> None:
        """Check for ORM/ActiveRecord patterns."""
        if not isinstance(node.func, ast.Attribute):
            return

        orm_methods = {
            "save",
            "delete",
            "destroy",
            "update",
            "create",
            "reload",
            "find",
            "find_by",
            "where",
            "filter",
            "filter_by",
            "get",
            "get_or_create",
            "select",
            "insert",
            "update_all",
            "delete_all",
            "execute",
            "query",
            "order_by",
            "group_by",
            "having",
            "limit",
            "offset",
            "join",
            "includes",
            "eager_load",
            "preload",
            "create_table",
            "drop_table",
            "add_column",
            "remove_column",
        }
        if node.func.attr not in orm_methods:
            return

        value = node.func.value
        if isinstance(value, ast.Name) and value.id in {
            "list",
            "dict",
            "set",
            "tuple",
            "str",
            "int",
            "float",
            "bool",
        }:
            return

        if isinstance(value, ast.Constant | ast.List | ast.Dict | ast.Tuple | ast.Set):
            return

        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id
            in {"open", "int", "str", "list", "dict", "set", "tuple", "bool", "float"}
        ):
            return

        self.errors.append(
            (
                node.lineno,
                node.col_offset,
                self.EO013.format(name=node.func.attr),
            )
        )

    def _check_implementation_inheritance(self, node: ast.ClassDef) -> None:
        """Check for implementation inheritance violations."""
        for base in node.bases:
            is_abstract_base = False

            if isinstance(base, ast.Name):
                # Allow inheritance from abstract base classes and common patterns
                allowed_bases = {
                    # Abstract bases
                    "ABC",
                    "Protocol",
                    # Exception hierarchy (standard pattern)
                    "Exception",
                    "BaseException",
                    "ValueError",
                    "TypeError",
                    "RuntimeError",
                    "AttributeError",
                    "KeyError",
                    "IndexError",
                    "ImportError",
                    "OSError",
                    # Standard library abstract bases
                    "Enum",
                    "IntEnum",
                    "Flag",
                    "IntFlag",
                    # Generic object (unavoidable in Python)
                    "object",
                }
                is_abstract_base = base.id in allowed_bases

            elif isinstance(base, ast.Attribute):
                # Check for module.AbstractBase patterns
                if base.attr in {"Protocol", "ABC"}:
                    is_abstract_base = True
                elif isinstance(base.value, ast.Name) and base.value.id in {
                    "abc",
                    "typing",
                    "collections",
                    "enum",
                }:
                    is_abstract_base = True

            # If not an abstract base, it's implementation inheritance
            if not is_abstract_base:
                self.errors.append(
                    (node.lineno, node.col_offset, self.EO014.format(name=node.name))
                )


# Entry point for flake8 plugin registration
def factory(_app: Any) -> type[ElegantObjectsViolation]:
    """Factory function for flake8 plugin."""
    return ElegantObjectsViolation


# For standalone usage
if __name__ == "__main__":
    import argparse
    import sys

    def main() -> None:
        """Standalone command-line interface."""
        parser = argparse.ArgumentParser(
            description="Check Python files for Elegant Objects -er principle violations"
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
                checker = ElegantObjectsViolation(tree)

                file_errors = 0
                for line, col, msg, _ in checker.run():
                    print(f"{file_path}:{line}:{col}: {msg}")

                    if args.show_source:
                        lines = source.split("\n")
                        if 0 <= line - 1 < len(lines):
                            print(f"    {lines[line - 1].strip()}")
                        print()

                    file_errors += 1
                    total_errors += 1

                if file_errors == 0:
                    print(f"{file_path}: No -er violations found ✓")

            except Exception as e:
                print(f"Error processing {file_path}: {e}", file=sys.stderr)

        if total_errors > 0:
            print(f"\nTotal violations found: {total_errors}")
            sys.exit(1)
        else:
            print("\nAll files comply with Elegant Objects -er principle! ✓")

    main()

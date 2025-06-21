"""Advanced principles checker for Elegant Objects violations."""

import ast

from .base import ErrorCodes, Principles, Violations


class AdvancedPrinciples(Principles):
    """Checks for advanced EO principles: no static methods, no type discrimination, contracts, test purity, no ORM, no implementation inheritance."""

    def check(self, node: ast.AST) -> Violations:
        """Check node for advanced principle violations."""
        violations = []

        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            violations.extend(self._check_static_methods(node))
            violations.extend(self._check_public_methods_contracts(node))
            violations.extend(self._check_test_methods(node))
        elif isinstance(node, ast.Call):
            violations.extend(self._check_isinstance_usage(node))
            violations.extend(self._check_orm_patterns(node))
        elif isinstance(node, ast.ClassDef):
            violations.extend(self._check_implementation_inheritance(node))

        return violations

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
                return self._violation(node, ErrorCodes.EO009.format(name=node.name))
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
                return self._violation(node, ErrorCodes.EO010)
        return []

    def _check_public_methods_contracts(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Violations:
        """Check if public methods have contracts (Protocol/ABC)."""
        # Skip private methods, special methods, and property decorators
        if node.name.startswith("_") or any(
            isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list
        ):
            return []

        # Skip if not a method (no current class context)
        if not self._current_class or not self._is_method(node):
            return []

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
            return []

        # Public method without contract - violation
        return self._violation(node, ErrorCodes.EO011.format(name=node.name))

    def _check_test_methods(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Violations:
        """Check that test methods only contain assertThat statements."""
        if not node.name.startswith("test_"):
            return []

        violations = []
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
                violations.extend(
                    self._violation(stmt, ErrorCodes.EO012.format(name=node.name))
                )
            elif not isinstance(stmt, ast.Pass):  # Allow pass statements
                violations.extend(
                    self._violation(stmt, ErrorCodes.EO012.format(name=node.name))
                )

        return violations

    def _check_orm_patterns(self, node: ast.Call) -> Violations:
        """Check for ORM/ActiveRecord patterns."""
        if not isinstance(node.func, ast.Attribute):
            return []

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
            return []

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
            return []

        if isinstance(value, ast.Constant | ast.List | ast.Dict | ast.Tuple | ast.Set):
            return []

        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id
            in {"open", "int", "str", "list", "dict", "set", "tuple", "bool", "float"}
        ):
            return []

        return self._violation(node, ErrorCodes.EO013.format(name=node.func.attr))

    def _check_implementation_inheritance(self, node: ast.ClassDef) -> Violations:
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
                return self._violation(node, ErrorCodes.EO014.format(name=node.name))

        return []

"""No impure tests principle checker for Elegant Objects violations."""

import ast

from .base import ErrorCodes, Source, Violations, violation


class NoImpureTests:
    """Checks for impure test methods violations (EO012)."""

    def check(self, source: Source) -> Violations:
        """Check source for impure test method violations."""
        node = source.node

        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            return self._check_test_methods(node)

        return []

    def _check_test_methods(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Violations:
        """Check that test methods only contain single assertion statements."""
        if not node.name.startswith("test_"):
            return []

        violations = []
        assertion_count = 0

        for stmt in node.body:
            if isinstance(stmt, ast.Pass):
                continue  # Allow pass statements

            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                # Check if it's an assertion
                if self._is_assertion_call(stmt.value):
                    assertion_count += 1
                    continue
                else:
                    # Non-assertion expression call
                    violations.extend(
                        violation(stmt, ErrorCodes.EO012.format(name=node.name))
                    )

            elif isinstance(stmt, ast.Assert):
                # Direct assert statement
                assertion_count += 1
                continue

            elif isinstance(stmt, ast.With):
                # Check for pytest.raises or similar context managers
                if self._is_assertion_context_manager(stmt):
                    assertion_count += 1
                    continue
                else:
                    violations.extend(
                        violation(stmt, ErrorCodes.EO012.format(name=node.name))
                    )

            else:
                # Any other statement (assignments, etc.) is a violation
                violations.extend(
                    violation(stmt, ErrorCodes.EO012.format(name=node.name))
                )

        # Test must have exactly one assertion
        if assertion_count == 0:
            violations.extend(violation(node, ErrorCodes.EO012.format(name=node.name)))
        elif assertion_count > 1:
            violations.extend(violation(node, ErrorCodes.EO012.format(name=node.name)))

        return violations

    def _is_assertion_call(self, call: ast.Call) -> bool:
        """Check if a call is an assertion."""
        # Check for unittest style assertions (self.assertEqual, self.assertTrue, etc.)
        if isinstance(call.func, ast.Attribute):
            if call.func.attr.startswith("assert"):
                return True
            # Check for chained assertions like assertThat(...).isEqualTo(...)
            if self._contains_assertion_in_chain(call):
                return True

        # Check for standalone assertion functions
        if isinstance(call.func, ast.Name):
            if call.func.id.startswith("assert") or call.func.id == "assertThat":
                return True

        return False

    def _contains_assertion_in_chain(self, call: ast.Call) -> bool:
        """Check if assertion exists anywhere in the call chain."""
        current = call
        while isinstance(current, ast.Call):
            if isinstance(current.func, ast.Name):
                if (
                    current.func.id.startswith("assert")
                    or current.func.id == "assertThat"
                ):
                    return True
            elif isinstance(current.func, ast.Attribute):
                if (
                    current.func.attr.startswith("assert")
                    or current.func.attr == "assertThat"
                ):
                    return True
                # Move to the next level in the chain
                if isinstance(current.func.value, ast.Call):
                    current = current.func.value
                else:
                    break
            else:
                break
        return False

    def _is_assertion_context_manager(self, with_stmt: ast.With) -> bool:
        """Check if with statement is for assertions like pytest.raises."""
        for item in with_stmt.items:
            if isinstance(item.context_expr, ast.Call):
                if isinstance(item.context_expr.func, ast.Attribute):
                    # Check for pytest.raises, unittest.assertRaises, etc.
                    if item.context_expr.func.attr in {"raises", "assertRaises"}:
                        return True
                elif isinstance(item.context_expr.func, ast.Name):
                    if item.context_expr.func.id in {"raises", "assertRaises"}:
                        return True
        return False

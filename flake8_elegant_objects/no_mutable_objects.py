"""No mutable objects principle checker for Elegant Objects violations."""

import ast
from typing import Iterator

from .base import ErrorCodes, Source, Violations, violation


class NoMutableObjects:
    """Checks for mutable object violations (EO008)."""

    def check(self, source: Source) -> Violations:
        """Check source for mutable object violations."""
        node = source.node
        if not isinstance(node, ast.ClassDef):
            return []
        violations = self._check_mutable_class(node)

        mutation_visitor = AttributeMutationVisitor()
        mutation_visitor.visit(node)
        return [
            *violations,
            *mutation_visitor.violations,
        ]

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


MUTATING_METHODS = {
    # List methods
    'append', 'extend', 'insert', 'remove', 'pop', 'clear', 'sort', 'reverse',
    # Dict methods
    'update', 'popitem', 'setdefault',
    # Set methods
    'add', 'discard',
    # General
    '__setitem__', '__delitem__', '__iadd__', '__imul__'
}


class AttributeMutationVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations: Violations = []
        self.current_class = None
        self.in_init = False
        self.class_attributes = set()
        self.self_arg_name = "self"

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.class_attributes = set()
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if not self.current_class:
            return

        decorator_names = {
            d.id for d in node.decorator_list if isinstance(d, ast.Name)
        }
        if 'classmethod' in decorator_names or 'staticmethod' in decorator_names:
            return

        # Save previous state
        prev_in_init = self.in_init
        prev_self_name = self.self_arg_name
        
        self.in_init = (node.name == '__init__')
        self.self_arg_name = node.args.args[0].arg if node.args.args else "self"
        
        self.generic_visit(node)
        
        # Restore previous state
        self.in_init = prev_in_init
        self.self_arg_name = prev_self_name

    def visit_Assign(self, node):
        if self.in_init:
            for target in node.targets:
                self._collect_attribute(target)
        elif self.current_class:
            for target in node.targets:
                self._check_mutation(target)

    def visit_AnnAssign(self, node):
        if self.in_init:
            self._collect_attribute(node.target)
        elif self.current_class:
            self._check_mutation(node.target)

    def visit_AugAssign(self, node):
        if self.in_init:
            self._collect_attribute(node.target)
        elif self.current_class:
            self._check_mutation(node.target)

    def visit_Call(self, node):
        if self.in_init or not self.current_class:
            return
            
        chain_info = self._attribute_chain(node)
        if not chain_info:
            return
            
        base_name, attr_path, _ = chain_info
        if not attr_path:  # self.method() - not an attribute mutation
            return
            
        # Check if the last attribute in the chain was defined in __init__
        if (base_name == self.self_arg_name and 
            attr_path[0] in self.class_attributes and 
            hasattr(node.func, 'attr') and 
            node.func.attr in MUTATING_METHODS):
            
            full_path = '.'.join(attr_path)
            msg = f"EO008: Mutating method '{node.func.attr}' called on attribute '{full_path}'"
            self.violations.extend(violation(node, msg))

    def _attribute_chain(self, node):
        """Recursively get (base_name, attribute_path, method_name) for method calls.
        For self.data.append() returns ('self', ['data'], 'append')
        For self.container.data.clear() returns ('self', ['container', 'data'], 'clear')
        """
        if isinstance(node, ast.Call):
            return self._attribute_chain(node.func)
            
        if isinstance(node, ast.Attribute):
            parent_info = self._attribute_chain(node.value)
            if not parent_info:
                return None
                
            base_name, attr_path, _ = parent_info
            if base_name == self.self_arg_name:
                return (base_name, attr_path + [node.attr], None)
            return None
            
        if isinstance(node, ast.Name):
            if node.id == self.self_arg_name:
                return (node.id, [], None)
            return None
        
        return None

    def _collect_attribute(self, node):
        if (isinstance(node, ast.Attribute) and
                isinstance(node.value, ast.Name) and
                node.value.id == self.self_arg_name):
            self.class_attributes.add(node.attr)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                self._collect_attribute(elt)
        elif isinstance(node, ast.Starred):
            self._collect_attribute(node.value)

    def _check_mutation(self, node):
        if (isinstance(node, ast.Attribute) and
                isinstance(node.value, ast.Name) and
                node.value.id == self.self_arg_name and
                node.attr in self.class_attributes):
            msg = f"EO008: Attribute '{node.attr}' mutated outside __init__"
            self.violations.extend(violation(node, msg))
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                self._check_mutation(elt)
        elif isinstance(node, ast.Starred):
            self._check_mutation(node.value)

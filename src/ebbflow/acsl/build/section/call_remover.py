"""Remove ACSL statements that are not needed in the executable function."""

import ast
from typing import Set

class CallRemover(ast.NodeTransformer):
    """Remove ACSL statements that are not needed in the executable function.

    Parameters
    ----------
    methods_to_remove : Set[str]
        A set of method names to remove.
    
    Attributes
    ----------
    methods_to_remove : Set[str]
        A set of method names to remove.
    new_tree : ast.AST
        The transformed AST.

    Returns
    -------
    None
    """
    def __init__(self, methods_to_remove: Set[str]):
        self.methods_to_remove = methods_to_remove
        self.new_tree = None

    def visit(self, node: ast.AST) -> ast.AST:
        """Override the main visit method to store the transformed tree.

        Parameters
        ----------
        node : ast.AST
            The AST of the function.

        Returns
        -------
        ast.AST
            The transformed AST.
        """
        transformed_node = super().visit(node)
        self.new_tree = transformed_node
        return transformed_node

    def visit_Expr(self, node: ast.Expr) -> ast.AST: # pylint: disable=invalid-name
        """Remove expression statements that are self method calls.

        Parameters
        ----------
        node : ast.Expr
            The AST of the expression.

        Returns
        -------
        ast.AST
            The transformed AST.
        """
        if (isinstance(node.value, ast.Call) and
            self._is_target_self_call(node.value)):
            return None
        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> ast.AST: # pylint: disable=invalid-name
        """Handle assignment statements that call self methods.

        Parameters
        ----------
        node : ast.Assign
            The AST of the assignment.

        Returns
        -------
        ast.AST
            The transformed AST.
        """
        if (isinstance(node.value, ast.Call) and
            self._is_target_self_call(node.value)):
            return None
        return self.generic_visit(node)

    def _is_target_self_call(self, call_node: ast.Call) -> bool:
        """Check if a call node is a target self method call.

        Parameters
        ----------
        call_node : ast.Call
            The AST of the call.

        Returns
        -------
        bool
            True if the call node is an ACSL statement that is not needed in
            the executable function, False otherwise.
        """
        return (isinstance(call_node.func, ast.Attribute) and
                isinstance(call_node.func.value, ast.Name) and
                call_node.func.value.id == "self" and
                call_node.func.attr in self.methods_to_remove)

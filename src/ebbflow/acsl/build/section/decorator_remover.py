"""Remove decorators from a function."""

import ast

class DecoratorRemover(ast.NodeTransformer):
    """Remove decorators from a function.

    Parameters
    ----------
    None

    Attributes
    ----------
    new_tree : ast.AST
        The transformed AST.

    Returns
    -------
    None
    """
    def __init__(self):
        self.new_tree = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef: #pylint: disable=invalid-name
        """Remove decorators from a function.

        Parameters
        ----------
        node : ast.FunctionDef
            The AST of the function.

        Returns
        -------
        ast.FunctionDef
            The transformed AST.
        """
        node.decorator_list = []
        self.generic_visit(node)
        self.new_tree = node

    def visit_AsyncFunctionDef( #pylint: disable=invalid-name
        self,
        node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        """Remove decorators from an async function.

        Parameters
        ----------
        node : ast.AsyncFunctionDef
            The AST of the async function.

        Returns
        -------
        ast.AsyncFunctionDef
            The transformed AST.
        """
        node.decorator_list = []
        self.generic_visit(node)
        self.new_tree = node

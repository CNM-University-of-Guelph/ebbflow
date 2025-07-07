"""Modify the signature of a function to inlcude keyword arguments."""
import ast
from typing import Dict

class SignatureModifier(ast.NodeVisitor):
    """Modify the signature of a function to inlcude keyword arguments.

    Parameters
    ----------
    constants : Dict
        A dictionary mapping constant names to their values.
    statevars : Dict
        A dictionary mapping state variable names to their values.
    
    Attributes
    ----------
    new_kwargs : List[str]
        A list of keyword arguments to add to the function signature.
    new_tree : ast.AST
        The transformed AST.

    Returns
    -------
    None
    """
    def __init__(self, constants: Dict, statevars: Dict):
        self.new_kwargs = [
            *list(constants.keys()),
            *list(statevars.keys())
        ]
        self.new_tree = None

    def visit_FunctionDef(self, node: ast.FunctionDef): #pylint: disable=invalid-name
        """Modify the signature of a function to inlcude keyword arguments.

        Parameters
        ----------
        node : ast.FunctionDef
            The AST of the function.

        Returns
        -------
        None
        """
        for kwarg in self.new_kwargs:
            new_arg = ast.arg(arg=kwarg, annotation=None)
            node.args.args.append(new_arg)
            node.args.defaults.append(ast.Constant(value=None))
        
        self.generic_visit(node)
        self.new_tree = node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef): #pylint: disable=invalid-name
        """Modify signature of an async function to inlcude keyword arguments.

        Parameters
        ----------
        node : ast.AsyncFunctionDef
            The AST of the async function.

        Returns
        -------
        None
        """
        self.visit_FunctionDef(node)

"""Modify the signature of a function to inlcude keyword arguments"""
import ast
from typing import Dict

class SignatureModifier(ast.NodeVisitor):
    def __init__(self, constants: Dict, statevars: Dict):
        self.new_kwargs = [
            "t",
            *list(constants.keys()),
            *list(statevars.keys())
        ]
        self.new_tree = None

    def visit_FunctionDef(self, node):
        for kwarg in self.new_kwargs:
            new_arg = ast.arg(arg=kwarg, annotation=None)
            node.args.args.append(new_arg)
            node.args.defaults.append(ast.Constant(value=None))
        
        self.generic_visit(node)
        self.new_tree = node

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

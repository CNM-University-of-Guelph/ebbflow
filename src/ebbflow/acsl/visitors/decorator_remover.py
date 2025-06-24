"""Remove decorators from a function"""

import ast

class DecoratorRemover(ast.NodeTransformer):
    def __init__(self):
        self.new_tree = None

    def visit_FunctionDef(self, node):
        node.decorator_list = []
        self.generic_visit(node)
        self.new_tree = node

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

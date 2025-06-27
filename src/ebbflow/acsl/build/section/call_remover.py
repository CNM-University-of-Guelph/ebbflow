"""Remove calls to self from a function"""

import ast

class CallRemover(ast.NodeTransformer):
    def __init__(self, methods_to_remove: set):
        self.methods_to_remove = methods_to_remove
        self.new_tree = None
    
    def visit(self, node):
        """Override the main visit method to store the transformed tree"""
        transformed_node = super().visit(node)
        self.new_tree = transformed_node
        return transformed_node
    
    def visit_Expr(self, node):
        """Remove expression statements that are self method calls"""
        if (isinstance(node.value, ast.Call) and
            self._is_target_self_call(node.value)):
            return None
        return self.generic_visit(node)

    def visit_Assign(self, node):
        """Handle assignment statements - remove if RHS is a target self call"""
        if (isinstance(node.value, ast.Call) and
            self._is_target_self_call(node.value)):
            return None
        return self.generic_visit(node)

    def _is_target_self_call(self, call_node):
        """Check if a call node is a target self method call"""
        return (isinstance(call_node.func, ast.Attribute) and
                isinstance(call_node.func.value, ast.Name) and
                call_node.func.value.id == "self" and
                call_node.func.attr in self.methods_to_remove)

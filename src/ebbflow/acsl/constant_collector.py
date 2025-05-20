import ast

class ConstantCollector(ast.NodeVisitor):
    def __init__(self, constant_manager):
        self.constant_manager = constant_manager
        self.found_constant_calls = []

    def visit_Call(self, node):
        """
        Visit a Call node in the AST.
        """
        # Check if the node is calling self.set_constant
        if (isinstance(node.func, ast.Attribute) and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id == "self" and
            node.func.attr == "set_constant"
            ):

            if len(node.args) == 2:
                try:
                    if isinstance(node.args[0], ast.Constant):
                        const_name = node.args[0].value
                    else:
                        raise ValueError(
                            "Constant name must be a string literal."
                        )

                    if (
                        isinstance(node.args[1], ast.Constant) and
                        isinstance(node.args[1].value, (int, float, bool))
                        ):
                        const_value = node.args[1].value
                    else:
                        raise ValueError(
                            f"Constant value for '{const_name}' must be an int, float, or bool literal."
                        )

                    self.found_constant_calls.append((const_name, const_value))

                except ValueError as e:
                    print(
                        f"Warning: Skipping invalid constant definition at line {node.lineno} in AST: {e}"
                    )
                except Exception as e:
                    print(
                        f"Warning: Unexpected error parsing constant at line {node.lineno}: {e}"
                    )

        # Check for nested calls
        self.generic_visit(node)

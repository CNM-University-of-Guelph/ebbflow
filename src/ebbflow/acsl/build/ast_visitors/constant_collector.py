import ast

class ConstantCollector(ast.NodeVisitor):
    def __init__(self):
        self.found_constant_calls = []

    def visit_Call(self, node):
        """
        Visit a Call node in the AST.
        """
        if (isinstance(node.func, ast.Attribute) and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id == "self" and
            node.func.attr == "constant"
            ):

            if len(node.args) == 2:
                try:
                    # Check name is a string
                    if isinstance(node.args[0], ast.Constant):
                        const_name = node.args[0].value
                    else:
                        raise ValueError(
                            "Constant name must be a string literal."
                        )

                    # Handle list value
                    if isinstance(node.args[1], ast.List):
                        const_value = []
                        for elt in node.args[1].elts:
                            if (
                                isinstance(elt, ast.Constant) and
                                isinstance(elt.value, (int, float, bool))
                                ):
                                const_value.append(elt.value)
                            else:
                                raise ValueError(
                                    f"Values in {const_name} must be an int, float, or bool literal."
                                )

                    # Handle int, float or bool value
                    elif (
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

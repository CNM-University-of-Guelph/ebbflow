"""AST visitor to collect self.constant calls from the AST of a section.
"""

import ast

class ConstantCollector(ast.NodeVisitor):
    """AST NodeVisitor to collect self.constant calls from the AST of a section.

    Attributes
    ----------
    found_constant_calls : list
        A list of tuples containing the name and value of the constant calls.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    def __init__(self):
        self.found_constant_calls = []

    def visit_Call(self, node: ast.Call): # pylint: disable=invalid-name
        """Visit a Call node in the AST and collect the values assigned by 
        self.constant() calls.

        Parameters
        ----------
        node : ast.Call
            The Call node to visit.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the constant name is not a string literal.
        ValueError
            If the constant value is not an int, float, or bool literal.
        ValueError
            If an invalid constant definition is found.
        """
        if (isinstance(node.func, ast.Attribute) and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id == "self" and
            node.func.attr == "constant"
        ):
            arguments = len(node.args)
            if not arguments == 2:
                raise ValueError(
                    f"self.constant() must have 2 arguments, got {arguments}"
            )
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
                                f"Values in {const_name} must be an int, float,"
                                " or bool literal."
                            )

                # Handle int, float or bool value
                elif (
                    isinstance(node.args[1], ast.Constant) and
                    isinstance(node.args[1].value, (int, float, bool))
                    ):
                    const_value = node.args[1].value
                else:
                    raise ValueError(
                        f"Constant value for '{const_name}' must be an int, "
                        "float, or bool literal."
                    )

                self.found_constant_calls.append((const_name, const_value))

            except ValueError as e:
                print(
                    "Warning: Skipping invalid constant definition at line "
                    f"{node.lineno} in AST: {e}"
                )

        # Check for nested calls
        self.generic_visit(node)

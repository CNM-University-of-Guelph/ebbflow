"""AST visitor to collect the state variables.
"""

import ast

class StatevarCollector(ast.NodeVisitor):
    """AST visitor to collect the state variables.

    Parameters
    ----------
    None

    Attributes
    ----------
    integ_calls : Dict[str, str]
        A dictionary mapping the state variable names to the names of the 
        derivative variables passed to the integ function.

    Returns
    -------
    None
    """
    def __init__(self):
        self.integ_calls = {}

    def visit_Assign(self, node): # pylint: disable=invalid-name
        if (
            isinstance(node.value, ast.Call) and
            isinstance(node.value.func, ast.Attribute) and
            node.value.func.attr == "integ"
            ):
            # Variable passed as ic
            if (
                len(node.targets) == 1 and
                isinstance(node.value.args[1], ast.Name)
            ):
                self.integ_calls[node.targets[0].id] = node.value.args[1].id

            # Constant passed as ic
            elif (
                len(node.targets) == 1 and
                isinstance(node.value.args[1], ast.Constant)
            ):
                self.integ_calls[node.targets[0].id] = node.value.args[1].value

            else:
                raise ValueError(
                    f"Expected 1 target for integ call, got {len(node.targets)}"
                )
        self.generic_visit(node)

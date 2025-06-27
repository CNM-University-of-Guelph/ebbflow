import ast

class StatevarCollector(ast.NodeVisitor):
    def __init__(self):
        self.integ_calls = {}

    def visit_Assign(self, node):
        if (
            isinstance(node.value, ast.Call) and
            isinstance(node.value.func, ast.Attribute) and
            node.value.func.attr == "integ"
            ):
            # Variable passed as ic
            if len(node.targets) == 1 and isinstance(node.value.args[1], ast.Name):
                self.integ_calls[node.targets[0].id] = node.value.args[1].id

            # Constant passed as ic 
            elif len(node.targets) == 1 and isinstance(node.value.args[1], ast.Constant):
                self.integ_calls[node.targets[0].id] = node.value.args[1].value

            else:
                raise ValueError(
                    f"Expected 1 target for integ call, got {len(node.targets)}"
                )
        self.generic_visit(node)

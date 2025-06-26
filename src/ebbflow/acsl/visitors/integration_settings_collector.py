import ast

class IntegrationSettingsCollector(ast.NodeVisitor):
    def __init__(self):
        self.settings = {}
        self.settings_names = ['IALG', 'NSTP', 'MAXT', 'MINT', 'CINT']

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Tuple) and len(node.targets[0].elts) > 1:
            raise ValueError("Multiple assignments are not allowed!")

        if node.targets[0].id not in self.settings_names:
            return

        self.settings[node.targets[0].id] = node.value.value
        self.generic_visit(node)

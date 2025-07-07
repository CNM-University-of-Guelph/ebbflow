"""AST visitor to collect integration settings from the DYNAMIC section.
"""

import ast

class IntegrationSettingsCollector(ast.NodeVisitor):
    """AST visitor to collect integration settings from the DYNAMIC section.

    Attributes
    ----------
    settings : Dict[str, Any]
        A dictionary of integration settings.
    settings_names : List[str]
        A list of the names of the integration settings.

    Returns
    -------
    None
    """
    def __init__(self):
        self.settings = {}
        self.settings_names = ["IALG", "NSTP", "MAXT", "MINT", "CINT"]

    def visit_Assign(self, node: ast.Assign): # pylint: disable=invalid-name
        """Visit an Assign node in the AST and collect the integration settings.

        Parameters
        ----------
        node : ast.Assign
            The Assign node to visit.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If multiple assignments are found.

        Notes
        -----
        This method only captures the following variables:
        - IALG: Integration algorithm
        - NSTP: Number of steps per time period
        - MAXT: Maximum time step
        - MINT: Minimum time step
        - CINT: Communication interval
        """
        if (
            isinstance(node.targets[0], ast.Tuple) and
            len(node.targets[0].elts) > 1
        ):
            raise ValueError("Multiple assignments are not allowed!")

        if node.targets[0].id not in self.settings_names:
            return

        self.settings[node.targets[0].id] = node.value.value
        self.generic_visit(node)

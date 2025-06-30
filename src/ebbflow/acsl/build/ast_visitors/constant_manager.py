"""Manager for constants in an ACSL model.
"""

import ast
from typing import Dict, Tuple

from ebbflow.acsl.build.ast_visitors.constant_collector import ConstantCollector

class ConstantManager:
    """Manager for constants in an ACSL model.
     
    Handles collecting constants from all the sections of an ACSL model.

    Parameters
    ----------
    initial_scope : Tuple[str, Dict]
        A tuple containing the scope of the INITIAL section.

    Attributes
    ----------
    constants : Dict[str, Any]
        A dictionary of constants.
    valid_types : Tuple[Type[int], Type[float], Type[bool], Type[list]]
        A tuple of the valid types for constants.

    Returns
    -------
    None
    """
    def __init__(self, initial_scope: Tuple[str, Dict]):
        self.constants = {
            "t": 0
        }
        self.valid_types = (int, float, bool, list)
        self.collect_initial_constants(initial_scope)

    def set_constant(self, name: str, value: int | float | bool | list):
        """Add a constant to the constants dictionary.

        Parameters
        ----------
        name : str
            The name of the constant.
        value : int | float | bool | list
            The value of the constant.

        Returns
        -------
        None

        Raises
        ------
        TypeError
            If the constant name is not a string.
        TypeError
            If the constant value is not an int, float, bool, or list.
        ValueError
            If the constant is already defined.
        """
        if not isinstance(name, str):
            raise TypeError(
                f"Constant name must be a string, got {type(name).__name__}"
            )
        elif not isinstance(value, self.valid_types):
            raise TypeError(
                f"{name} has invalid type {type(value)}. Valid types are "
                f"{self.valid_types}"
            )
        elif name in self.constants:
            raise ValueError(f"Constant {name} is already defined")

        self.constants[name] = value

    def collect_initial_constants(self, initial_scope: Tuple[str, Dict]):
        """Collect constants from the INITIAL section scope.

        Parameters
        ----------
        initial_scope : Tuple[str, Dict]
            A tuple containing the scope of the INITIAL section.

        Returns
        -------
        None
        """
        for const_name, const_value in initial_scope[1].items():
            self.set_constant(const_name, const_value)

    def collect(self, tree: ast.AST):
        """Collect constants from the AST of a section using ConstantCollector.

        Parameters
        ----------
        tree : ast.AST
            The AST of the section.
        """
        constant_collector = ConstantCollector()
        constant_collector.visit(tree)
        for const_name, const_value in constant_collector.found_constant_calls:
            self.set_constant(const_name, const_value)

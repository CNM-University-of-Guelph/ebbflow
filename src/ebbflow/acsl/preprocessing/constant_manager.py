import ast
from typing import Dict, Tuple

from ebbflow.acsl.visitors.constant_collector import ConstantCollector

class ConstantManager:
    def __init__(self, initial_scope: Tuple[str, Dict]):
        self.constants = {}
        self.valid_types = (int, float, bool)
        self.collect_initial_constants(initial_scope)

    def set_constant(self, name, value):
        if not isinstance(name, str):
            raise TypeError(
                f"Constant name must be a string, got {type(name).__name__}"
            )
        elif not isinstance(value, self.valid_types):
            raise TypeError(
                f"{name} has invalid type {type(value)}. Valid types are int, float, and bool"
            )
        elif name in self.constants.keys():
            raise ValueError(f"Constant {name} is already defined")

        self.constants[name] = value

    def collect_initial_constants(self, initial_scope: Tuple[str, Dict]):
        for const_name, const_value in initial_scope[1].items():
            self.set_constant(const_name, const_value)

    def collect(self, section_name: str, tree: ast.AST):
        constant_collector = ConstantCollector()
        constant_collector.visit(tree)
        for const_name, const_value in constant_collector.found_constant_calls:
            self.set_constant(const_name, const_value)

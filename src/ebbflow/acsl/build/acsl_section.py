"""Wrapper for a section of an ACSL model"""
import ast
from typing import Dict

from ebbflow.acsl.visitors.signature_modifier import SignatureModifier
from ebbflow.acsl.visitors.decorator_remover import DecoratorRemover
from ebbflow.acsl.visitors.call_remover import CallRemover
from ebbflow.acsl.acsl_lib import AcslLib
from ebbflow.acsl.integration.integration_manager import IntegrationManager

class AcslSection(AcslLib):
    def __init__(
            self,
            name: str,
            tree: ast.AST,
            integration_manager: IntegrationManager
        ):
        super().__init__(integration_manager=integration_manager)
        self.section_name = name
        self.tree = tree
        self.executable_func = None
        self.methods_to_remove = {"constant"}

    def __repr__(self):
        return f"AcslSection(name={self.section_name})"

    def modify_signature(self, constants: Dict, statevars: Dict):
        # NOTE: assumes that constants and statevars are provided to all sections
        modifier = SignatureModifier(constants, statevars)
        modifier.visit(self.tree)
        ast.fix_missing_locations(modifier.new_tree)
        self.tree = modifier.new_tree

    def remove_decorators(self):
        remover = DecoratorRemover()
        remover.visit(self.tree)
        ast.fix_missing_locations(remover.new_tree)
        self.tree = remover.new_tree

    def remove_self_calls(self):
        remover = CallRemover(self.methods_to_remove)
        remover.visit(self.tree)
        ast.fix_missing_locations(remover.new_tree)
        self.tree = remover.new_tree

    def create_executable(self):
        module = ast.Module(body=[self.tree], type_ignores=[])
        ast.fix_missing_locations(module)
        compiled = compile(module, f"<{self.section_name}>", "exec")
        namespace = {}
        exec(compiled, namespace)

        func_name = self.tree.name if isinstance(
            self.tree, ast.FunctionDef
        ) else module.body[0].name

        self.executable_func = namespace[func_name]

    def save(self, filename: str):
        code = ast.unparse(self.tree)
        with open(filename, 'w') as f:
            f.write(f"# Code for section {self.section_name}\n")
            f.write(f"# Generated automatically by AcslSection\n\n")
            f.write(code)

    def call(self, arguments: Dict):
        if self.executable_func is None:
            raise RuntimeError(
                f"Section {self.section_name} has no executable. Call create_executable() first."
            )
        return self.executable_func(self, **arguments)

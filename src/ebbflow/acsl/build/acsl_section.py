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
        self.procedural_functions = []
        self.tree = self._extract_procedural_functions(tree)
        self.executable_func = None
        self.methods_to_remove = {"constant"}

    def __repr__(self):
        return f"AcslSection(name={self.section_name})"

    def _extract_procedural_functions(self, tree: ast.Module):
        main_func = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                is_procedural = any(
                    isinstance(decorator, ast.Name) and decorator.id == "PROCEDURAL"
                    for decorator in node.decorator_list
                )
                if is_procedural:
                    remover = DecoratorRemover()
                    remover.visit(node)
                    self.procedural_functions.append(remover.new_tree)
                else:
                    main_func = node
        if main_func is None:
            raise ValueError("No main function found in module")
        return main_func

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
        module_body = self.procedural_functions + [self.tree]
        module = ast.Module(body=module_body, type_ignores=[])
        ast.fix_missing_locations(module)
        compiled = compile(module, f"<{self.section_name}>", "exec")
        namespace = {}
        exec(compiled, namespace)

        func_name = self.tree.name if isinstance(
            self.tree, ast.FunctionDef
        ) else module.body[-1].name

        self.executable_func = namespace[func_name]

    def save(self, filename: str):
        module_body = self.procedural_functions + [self.tree]
        module = ast.Module(body=module_body, type_ignores=[])
        code = ast.unparse(module)
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

"""Wrapper for a section of an ACSL model."""
import ast
from typing import Dict

from ebbflow.acsl.build.section.signature_modifier import SignatureModifier
from ebbflow.acsl.build.section.decorator_remover import DecoratorRemover
from ebbflow.acsl.build.section.call_remover import CallRemover

class AcslSection:
    """Wrapper for a section of an ACSL model.

    Process the section by removing decorators, self-calls, and modifying the
    signature to include constants and state variables. Create an executable
    function from the section.

    Parameters
    ----------
    name : str
        The name of the section.
    tree : ast.AST
        The AST of the section.

    Attributes
    ----------
    section_name : str
        The name of the section.
    procedural_functions : List[ast.FunctionDef]
        The procedural functions in the section.
    tree : ast.AST
        The AST of the section.
    executable_func : Callable
        The executable function for the section.
    methods_to_remove : Set[str]
        The methods to remove from the section.
    """
    def __init__(
            self,
            name: str,
            tree: ast.AST,
        ):
        self.section_name = name
        self.procedural_functions = []
        self.tree = self._extract_procedural_functions(tree)
        self.executable_func = None
        self.methods_to_remove = {"constant"}

    def __repr__(self):
        """Return a string representation of the section."""
        return f"AcslSection(name={self.section_name})"

    def _extract_procedural_functions(self, tree: ast.Module):
        """Extract the procedural functions from the tree.

        Parameters
        ----------
        tree : ast.Module
            The AST of the section.

        Returns
        -------
        ast.FunctionDef
            The main function of the section.

        Raises
        ------
        ValueError
            If no main function is found in the module.
        """
        main_func = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                is_procedural = any(
                    (
                        isinstance(decorator, ast.Name) and
                        decorator.id == "PROCEDURAL"
                    )
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
        """Modify the fucntion signature to include constants and statevars.

        Parameters
        ----------
        constants : Dict
            A dictionary mapping constant names to their values.
        statevars : Dict
            A dictionary mapping state variable names to their values.

        Returns
        -------
        None
        """
        modifier = SignatureModifier(constants, statevars)
        modifier.visit(self.tree)
        ast.fix_missing_locations(modifier.new_tree)
        self.tree = modifier.new_tree

    def remove_decorators(self):
        """Remove the decorators from the section.

        Parameters
        ----------
        None
        """
        remover = DecoratorRemover()
        remover.visit(self.tree)
        ast.fix_missing_locations(remover.new_tree)
        self.tree = remover.new_tree

    def remove_self_calls(self):
        """Remove the self-calls for the methods in methods_to_remove.

        Parameters
        ----------
        None
        """
        remover = CallRemover(self.methods_to_remove)
        remover.visit(self.tree)
        ast.fix_missing_locations(remover.new_tree)
        self.tree = remover.new_tree

    def create_executable(self):
        """Create an executable function from the section.

        Parameters
        ----------
        None

        Note
        ----
        This function uses exec() to create a function from the AST. This does
        allow for arbitrary code to be executed on the user's machine and is
        considered a security risk. However, the AST comes from user-authored
        code that could be run directly regardless. Therefore, this is 
        considered safe in this context. If the ebbflow package ever supports 
        executing code on a remote machine, this function will need to be 
        updated to use a more secure method.
        """
        module_body = self.procedural_functions + [self.tree]
        module = ast.Module(body=module_body, type_ignores=[])
        ast.fix_missing_locations(module)
        compiled = compile(module, f"<{self.section_name}>", "exec")
        namespace = {}
        exec(compiled, namespace) # see the above note about security risks

        func_name = self.tree.name if isinstance(
            self.tree, ast.FunctionDef
        ) else module.body[-1].name

        self.executable_func = namespace[func_name]

    def save(self, filename: str):
        """Save the section to a file.

        Parameters
        ----------
        filename : str
            The name of the file to save the section to.
        """
        module_body = self.procedural_functions + [self.tree]
        module = ast.Module(body=module_body, type_ignores=[])
        code = ast.unparse(module)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Code for section {self.section_name}\n")
            f.write("# Generated automatically by AcslSection\n\n")
            f.write(code)

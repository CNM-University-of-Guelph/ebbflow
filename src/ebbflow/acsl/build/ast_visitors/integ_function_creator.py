"""AST visitor to create functions for the derivatives of the state variables.
"""

import ast
from typing import List, Tuple, Set, Dict, Callable

from ebbflow.acsl.build.sort.function_parser import FunctionParser

class IntegFunctionCreator(ast.NodeVisitor):
    """AST visitor to create functions for the derivatives of the state 
    variables.

    Parameters
    ----------
    constants : List[str]
        A list of the names of the constants.

    Attributes
    ----------
    constants : Set[str]
        A set of the names of the constants.
    is_constants : bool
        A boolean indicating if the constants are set. Raises an error if
        constants are not set before visiting the node.
    assignments : Dict[str, Tuple[ast.Assign, Set[str]]]
        A dictionary mapping variable names to their assignment nodes and 
        dependencies.
    dependencies : Dict[str, Dict[str, str]]
        A dictionary mapping state variable names to their dependencies.

    Returns
    -------
    None
    """
    def __init__(self, constants: List[str] = None):
        if constants:
            self.is_constants = True
            self.constants = set(constants)
        else:
            self.is_constants = False
            self.constants = set()
        self.assignments = {}
        self.dependencies = {}

    def set_constants(self, constants: List[str]):
        """Set the constants for the visitor.

        Parameters
        ----------
        constants : List[str]
            A list of the names of the constants.

        Returns
        -------
        None
        """
        self.constants = set(constants)
        self.is_constants = True

    def visit(self, node: ast.Module) -> Dict[str, Tuple[Callable, List[str]]]:
        """Visit the AST and create functions for the derivatives of the state 
        variables.

        Parameters
        ----------
        node : ast.Module
            The AST of the section.

        Returns
        -------
        Dict[str, Tuple[Callable, List[str]]]
            A dictionary mapping derivative variable names to their functions 
            and a list of arguments.

        Raises
        ------
        ValueError
            If constants are not set before visiting the node.
        ValueError
            If no function definition is found in the node.
        """
        deriv_functions = {}

        if not self.is_constants:
            raise ValueError(
                "Constants are not set. Call set_constants() before visiting "
                "the node."
            )

        # Reset state
        self.assignments = {}
        self.dependencies = {}

        for func_node in node.body:
            if isinstance(func_node, ast.FunctionDef):
                for decorator in func_node.decorator_list:
                    if decorator.id == "PROCEDURAL":
                        continue
                    else:
                        break
            else:
                raise ValueError("No function definition found in the node")

        # 1. Detect self.integ calls
        state_vars = self._detect_integ_calls(func_node)
        if not state_vars:
            return {}
        # Include initial state variables in constants
        self.constants.update({state_var for _, state_var in state_vars})

        # 2. Extract assignment expressions
        parser = FunctionParser(self.constants)
        parser.collect_variables(
            ast.Module(body=[func_node], type_ignores=[]),
            include_constants=True
        )
        self.assignments = dict(parser.variable_map)

        # 3. Extract dependencies to caclulate derivatives
        for deriv, state_var in state_vars:
            self._create_dependency_map(deriv, state_var)

        # 4. Create function for derivatives
        for deriv_var, dependencies in self.dependencies.items():
            func_ast, args = self._create_derivative_function(
                deriv_var, dependencies
            )

            # NOTE DEBUGGING
            # module_body = func_ast.body
            # module = ast.Module(body=module_body, type_ignores=[])
            # code = ast.unparse(module)
            # with open(f"./dev/derivative_funcs/{deriv_var}.py", "w", encoding="utf-8") as f:
            #     f.write(f"# Code for section {deriv_var}\n")
            #     f.write("# Generated automatically by IntegFunctionCreator\n\n")
            #     f.write(code)

            deriv_functions[f"{deriv_var}"] = (
                self._create_executable(func_ast, f"calculate_{deriv_var}"),
                args
            )
        return deriv_functions

    def _detect_integ_calls(
        self,
        func_node: ast.FunctionDef
    ) -> List[Tuple[str, str]]:
        """Check for self.integ calls and extract differential variable names.

        Parameters
        ----------
        func_node : ast.FunctionDef
            The function node to check.

        Returns
        -------
        List[Tuple[str, str]]
            A list of tuples containing the differential variable names and 
            target variable names.
        """
        integ_vars = []

        for stmt in func_node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if (
                    isinstance(target, ast.Name) and
                    isinstance(stmt.value, ast.Call)
                ):
                    call = stmt.value
                    if (
                        isinstance(call.func, ast.Attribute) and
                        isinstance(call.func.value, ast.Name) and
                        call.func.value.id == "self" and
                        call.func.attr == "integ" and
                        len(call.args) >= 1
                    ):
                        if isinstance(call.args[0], ast.Name):
                            diff_var = call.args[0].id
                            target_var = target.id
                            integ_vars.append((diff_var, target_var))
        return integ_vars

    def _create_dependency_map(
        self,
        diff_var: str,
        state_var: str
    ) -> List[str]:
        """Map the state variable to its dependencies. All constants are provided
        as input to the function.

        Parameters
        ----------
        diff_var : str
            The differential variable name.
        state_var : str
            The state variable name.

        Returns
        -------
        None
        """
        calc_order = 1
        dependencies = {}
        calculated_vars = {state_var} | self.constants
        var_to_calc = diff_var

        while var_to_calc:
            # Handle constants and state variables
            if var_to_calc in self.constants:
                dependencies.update({
                    var_to_calc: "constant"
                })
                calculated_vars.add(var_to_calc)
                var_to_calc = self._get_next_var_to_calc(
                    dependencies, calculated_vars
                )
                continue

            # Add dependences for calculation
            if var_to_calc in self.assignments:
                var_dependencies = self.assignments[var_to_calc]["dependencies"]
                for var in var_dependencies:
                    if var not in self.constants and var not in dependencies:
                        dependencies[var] = f"calc_{calc_order}"
                        calc_order += 1
                    elif var in self.constants and var not in dependencies:
                        dependencies[var] = "constant"

                calculated_vars.add(var_to_calc)
                var_to_calc = self._get_next_var_to_calc(
                    dependencies, calculated_vars
                )

        dependencies[state_var] = "state_var"
        self.dependencies[diff_var] = dependencies

    def _get_next_var_to_calc(
        self,
        depenedencies: Dict[str, str],
        calculated_vars: Set[str]
    ) -> str:
        """Get the next variable to calculate in the derivative function.

        Parameters
        ----------
        depenedencies : Dict[str, str]
            Dict mapping variable names to their dependencies.
        calculated_vars : Set[str]
            Set of variables that have been calculated.

        Returns
        -------
        str
            The next variable to calculate.
        """
        remaining_dependencies = depenedencies.keys() - calculated_vars
        if remaining_dependencies:
            return remaining_dependencies.pop()
        else:
            return None

    def _create_derivative_function(
        self,
        deriv_var: str,
        dependencies: Dict[str, str]
    ) -> Tuple[ast.Module, List[str]]:
        """Create a function for the given variable.

        Parameters
        ----------
        deriv_var : str
            The derivative variable name.
        dependencies : Dict[str, str]
            Dict mapping variable names to their dependencies.
        Returns
        -------
        Tuple[ast.Module, List[str]]
            A tuple containing the AST of the function and a list of arguments.

        Raises
        ------
        ValueError
            If no state variable is found for the derivative.
        """
        state_var = None
        constants = []
        calc_vars_with_order = []

        for var_name, var_type in dependencies.items():
            if var_type == "state_var":
                state_var = var_name
            elif var_type == "constant":
                constants.append(var_name)
            elif var_type.startswith("calc_"):
                order_num = int(var_type.split("_")[1])
                calc_vars_with_order.append((var_name, order_num))

        if not state_var:
            raise ValueError(
                f"No state variable found for derivative {deriv_var}"
            )

        calc_vars_with_order.sort(key=lambda x: x[1], reverse=True)
        calc_vars = [var for var, _ in calc_vars_with_order]

        # Always include time as a constant
        if "t" not in constants:
            constants.append("t")

        func_ast = self._create_function_ast(
            deriv_var, state_var, constants, calc_vars
        )
        return (func_ast, constants + [state_var])

    def _create_function_ast(
        self,
        deriv_var: str,
        state_var: str,
        constants: List[str],
        calc_vars: List[str]
    ) -> ast.Module:
        """Create an AST Module node for the derivative calculation.

        Parameters
        ----------
        deriv_var : str
            The derivative variable name.
        state_var : str
            The state variable name.
        constants : List[str]
            A list of constant names.
        calc_vars : List[str]
            A list of variable names to calculate.

        Returns
        -------
        ast.Module
            The AST of the derivative function.
        """
        body = []
        for var in calc_vars:
            if var in self.assignments:
                stmt = self.assignments[var]["stmt"]
                body.append(stmt)

        # Add assignment for the derivative variable if it exists
        if deriv_var in self.assignments:
            stmt = self.assignments[deriv_var]["stmt"]
            body.append(stmt)

        # Add return statement for the derivative variable
        return_stmt = ast.Return(value=ast.Name(id=deriv_var, ctx=ast.Load()))
        body.append(return_stmt)

        # Create keyword arguments for state variable and constants
        kwonlyargs = [ast.arg(arg=state_var, annotation=None)]
        kwonlyargs.extend(
            [ast.arg(arg=const, annotation=None) for const in constants]
        )
        kw_defaults = [None] * len(kwonlyargs)

        # Create function definition
        func_def = ast.FunctionDef(
            name=f"calculate_{deriv_var}",
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                vararg=None,
                kwonlyargs=kwonlyargs,
                kw_defaults=kw_defaults,
                defaults=[]
            ),
            body=body,
            decorator_list=[],
            returns=None
        )

        # Create module
        module = ast.Module(body=[func_def], type_ignores=[])
        ast.fix_missing_locations(module)
        return module

    def _create_executable(
        self,
        func_ast: ast.Module,
        func_name: str
    ) -> Callable:
        """Create an executable function from an AST Module node.

        Parameters
        ----------
        func_ast : ast.Module
            The AST of the function.
        func_name : str
            The name of the function.

        Returns
        -------
        Callable
            The executable function.

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
        compiled = compile(func_ast, f"<{func_name}>", "exec")
        namespace = {}
        exec(compiled, namespace) # see the above note about security risks
        return namespace[func_name]

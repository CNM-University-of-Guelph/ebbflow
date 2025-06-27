import ast
from typing import List, Tuple, Set, Dict, Callable

class IntegFunctionCreator(ast.NodeVisitor):
    def __init__(self, constants: List[str] = []):
        if constants:
            self.is_constants = True
            self.constants = set(constants)
        else:
            self.is_constants = False
            self.constants = set()
        self.assignments = {} # Map variable names to assignment nodes and dependencies
        self.dependencies = {} # Dict mapping state variable names to their dependencies

    def set_constants(self, constants: List[str]):
        self.constants = set(constants)
        self.is_constants = True

    def visit(self, tree: ast.Module) -> Dict[str, Tuple[Callable, List[str]]]:
        deriv_functions = {}

        if not self.is_constants:
            raise ValueError("Constants are not set. Call set_constants() before visiting the tree.")

        # Reset state
        self.assignments = {}
        self.dependencies = {}

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_node = node
                break
            else:
                raise ValueError("No function definition found in the tree")

        # 1. Detect self.integ calls
        state_vars = self._detect_integ_calls(func_node)
        if not state_vars:
            return {}
        self.constants.update({state_var for _, state_var in state_vars})

        # 2. Extract assignments expressions
        self._extract_assignments(func_node)

        # 3. Extract dependencies to caclulate derivatives
        for deriv, state_var in state_vars:
            self._create_dependency_map(deriv, state_var)

        # 4. Create function for derivatives
        for deriv_var, dependencies in self.dependencies.items():
            func_ast, args = self._create_derivative_function(deriv_var, dependencies)
            deriv_functions[f"{deriv_var}"] = (
                self._create_executable(func_ast, f"calculate_{deriv_var}"),
                args
            )
        return deriv_functions

    def _detect_integ_calls(self, func_node: ast.FunctionDef) -> List[Tuple[str, str]]:
        """
        Step 1: Check for self.integ calls and extract differential variable names
        Returns list of (differential_var, target_var) tuples
        """
        integ_vars = []
        
        for stmt in func_node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                    call = stmt.value
                    if (isinstance(call.func, ast.Attribute) and
                        isinstance(call.func.value, ast.Name) and
                        call.func.value.id == 'self' and
                        call.func.attr == 'integ' and
                        len(call.args) >= 1):
                        
                        if isinstance(call.args[0], ast.Name):
                            diff_var = call.args[0].id
                            target_var = target.id
                            integ_vars.append((diff_var, target_var))        
        return integ_vars

    def _extract_assignments(self, func_node: ast.FunctionDef):
        """
        Step 2: Create dict of assignment nodes for each variable
        """
        for stmt in func_node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name):
                    var_name = target.id
                    dependencies = self._extract_names_from_binop(stmt.value)
                    self.assignments[var_name] = (stmt, dependencies)
                else:
                    raise ValueError(f"Unsupported assignment target: {target}")

    def _extract_names_from_binop(self, expr: ast.BinOp) -> Set[str]:
        """
        Extract variable names from a binary operation
        """
        variables = set()
        if isinstance(expr, ast.BinOp):
            for node in ast.walk(expr):
                if isinstance(node, ast.Name):
                    variables.add(node.id)
        return variables

    def _create_dependency_map(self, diff_var: str, state_var: str) -> List[str]:
        """
        Map the state variable to it's dependencies
        """
        calc_order = 1
        dependencies = {}
        calculated_vars = set(state_var)
        var_to_calc = diff_var

        while var_to_calc:
            # Handle constants and other state variables
            if var_to_calc in self.constants:
                dependencies.update({
                    var_to_calc: "constant"
                })
                calculated_vars.add(var_to_calc)
                var_to_calc = self._get_next_var_to_calc(dependencies, calculated_vars)
                continue

            # Add dependences for calculation
            if var_to_calc in self.assignments:
                var_dependencies = self.assignments[var_to_calc][1]
                for var in var_dependencies:
                    if var not in self.constants and var not in dependencies:
                        dependencies[var] = f"calc_{calc_order}"
                        calc_order += 1
                    elif var in self.constants and var not in dependencies:
                        dependencies[var] = "constant"

                calculated_vars.add(var_to_calc)
                var_to_calc = self._get_next_var_to_calc(dependencies, calculated_vars)

        dependencies[state_var] = "state_var"
        self.dependencies[diff_var] = dependencies

    def _get_next_var_to_calc(self, depenedencies: Dict[str, str], calculated_vars: Set[str]) -> str:
        remaining_dependencies = depenedencies.keys() - calculated_vars
        if remaining_dependencies:
            return remaining_dependencies.pop()
        else:
            return None

    def _create_derivative_function(self, deriv_var: str, dependencies: Dict[str, str]):
        """
        Create a function for the given variable
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
            raise ValueError(f"No state variable found for derivative {deriv_var}")

        calc_vars_with_order.sort(key=lambda x: x[1], reverse=True)
        calc_vars = [var for var, _ in calc_vars_with_order]

        func_ast = self._create_function_ast(deriv_var, state_var, constants, calc_vars)
        return (func_ast, constants + [state_var])

    def _create_function_ast(self, deriv_var: str, state_var: str, constants: List[str], calc_vars: List[str]) -> ast.Module:
        """
        Create an AST function for the derivative calculation
        """
        body = []
        for var in calc_vars:
            if var in self.assignments:
                stmt, _ = self.assignments[var]
                body.append(stmt)
        
        # Add assignment for the derivative variable if it exists
        if deriv_var in self.assignments:
            stmt, _ = self.assignments[deriv_var]
            body.append(stmt)
        
        # Add return statement for the derivative variable
        return_stmt = ast.Return(value=ast.Name(id=deriv_var, ctx=ast.Load()))
        body.append(return_stmt)
        
        # Create keyword arguments for state variable and constants
        kwonlyargs = [ast.arg(arg=state_var, annotation=None)]
        kwonlyargs.extend([ast.arg(arg=const, annotation=None) for const in constants])
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

    def _create_executable(self, func_ast: ast.Module, func_name: str):
        compiled = compile(func_ast, f"<{func_name}>", "exec")
        namespace = {}
        exec(compiled, namespace)
        return namespace[func_name]

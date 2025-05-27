# Only sort one section at a time, passed in as a function
# Return the sorted function callable
# State variables are not flagged
# NOTE How do state variables get set?
    # Dynamic or user defined?
#
# Sort Algorithm
# --- First Pass ---
# - Examine each statement
#   - Set the output variable as calculated
#   - Create a list of the input variables associated with output variable
#   - Set the calculated flag as False for output
#  
#   NOTE: Setting flag False means that varaible not calculated
#   - All constants can be set to True
#
# --- Second Pass ---
# - For each statement in list (from first pass)
#   - If none of input are False add statement to output function
#       - Set flag for output to True
#   - When a statement is added to output function reevaluate the list
#   - 


# TODO:
# - Filter out set_constant() calls when handling EXPR nodes
# - Need to keep self.end() as final call
# - Return an executable function
#     - Need to collect code associated with each line and create new function
#     - This is what sort returns
# Implement the sorting algorithm when selecting the nodes to keep

import ast
from collections import defaultdict, OrderedDict

class FunctionParser:
    def __init__(self, constant_names: list[str]):
        self.variable_map = defaultdict(lambda: {
            "stmt": None,
            "dependencies": [],
            "type": None
        })
        self.expr_map = defaultdict(lambda: {
            "stmt": None,
            "dependencies": [],
            "type": None
        })
        self.constant_names = list(constant_names)
        self.state_variables = []

    def collect_variables(self, function_tree: ast.Module):
        """Collect the calcualted variables and their dependencies."""
        for node in ast.walk(function_tree):
            if isinstance(node, ast.Assign):
                self._collect_assign(node)
            elif isinstance(node, ast.AnnAssign):
                self._collect_annassign(node)
            elif isinstance(node, ast.Expr):
                self._collect_expr(node)
        self.filter_variable_map()

    def filter_variable_map(self):
        """Remove constants and state variables from the variable map."""
        initial_values = self.state_variables + self.constant_names

        for var_name, info in self.variable_map.items():
            info["dependencies"] = [
                dep for dep in info["dependencies"] 
                if dep not in initial_values
            ]
            self.variable_map[var_name] = info

    def _collect_assign(self, node):
        """Collect the variables and dependencies for an ast.Assign node."""
        is_state_var = False
        if (
            isinstance(node.targets[0], ast.Tuple) or 
            isinstance(node.targets[0], ast.List)
        ):
            raise ValueError(
                f"Multiple targets in assignment is not allowed: {node.targets}"
            )

        if isinstance(node.value, ast.BinOp):
            parameters = self._collect_binop(node.value)
        elif isinstance(node.value, ast.Call):
            parameters, is_state_var = self._collect_call(node.value)
        else:
            raise TypeError(f"No method for handling {type(node.value)}")

        for target in node.targets:
            if (
                isinstance(target, ast.Name) and 
                isinstance(target.ctx, ast.Store)
            ):
                self.variable_map[target.id] = {
                    "stmt": node,
                    "dependencies": parameters,
                    "type": "assign"
                }
                if is_state_var:
                    self.state_variables.append(target.id)

    def _collect_annassign(self, node):
        """Collect the variables and dependencies for an ast.AnnAssign node."""
        is_state_var = False

        if isinstance(node.value, ast.BinOp):
            parameters = self._collect_binop(node.value)
        elif isinstance(node.value, ast.Call):
            parameters, is_state_var = self._collect_call(node.value)
        else:
            raise TypeError(f"No method for handling {type(node.value)}")

        if (
            isinstance(node.target, ast.Name) and 
            isinstance(node.target.ctx, ast.Store)
        ):
            self.variable_map[node.target.id] = {
                "stmt": node,
                "dependencies": parameters,
                "type": "annassign"
            }
            if is_state_var:
                self.state_variables.append(node.target.id)

    def _collect_binop(self, binop):
        """Collect the dependencies for an ast.BinOp node."""
        variables = []
        if isinstance(binop.left, ast.Name):
            variables.append(binop.left.id)
        elif isinstance(binop.left, ast.BinOp):
            variables.extend(self._collect_binop(binop.left))

        if isinstance(binop.right, ast.Name):
            variables.append(binop.right.id)
        elif isinstance(binop.right, ast.BinOp):
            variables.extend(self._collect_binop(binop.right))

        return variables

    def _collect_call(self, node):
        """Collect the dependencies for an ast.Call node."""
        variables = []
        is_state_var = False
        if isinstance(node.args, list):
            variables.extend([
                arg.id for arg in node.args if isinstance(arg, ast.Name)
            ])
       # NOTE: Collecting keywords this way gives the keyword name, not the value
       #       Likely need to enforce rule that variables are not passed as keywords
        if isinstance(node.keywords, list):
            variables.extend([
                keyword.arg for keyword in node.keywords
                if isinstance(keyword, ast.keyword)
            ])
        if isinstance(node.func, ast.Name):
            if node.func.id == "integ":
                is_state_var = True
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr == "integ":
                is_state_var = True
        return variables, is_state_var

    def _collect_expr(self, node):
        """Create a dict of ast.Expr nodes to include in the output function."""
        if isinstance(node.value.func, ast.Name):
            func_name = node.value.func.id
        elif isinstance(node.value.func, ast.Attribute):
            func_name = node.value.func.attr

        if func_name == "set_constant":
            return
        elif func_name == "end":
            self.expr_map[func_name] = {
                "stmt": node,
                "dependencies": [],
                "type": "ACSL.end"
            }
        else:
            raise ValueError(f"Unknown function: {func_name}")


class AcslSort:
    @classmethod
    def sort(
        cls,
        function_tree: ast.Module,
        constant_names: list[str],
        save_function: bool = False
    ):
        """Implement ACSL Sorting Algorithm"""
        parser = FunctionParser(constant_names)
        parser.collect_variables(function_tree)

        variables_to_sort = set(parser.variable_map.keys())
        calculation_order = OrderedDict()

        while variables_to_sort:
            next_var = cls._pick_next_variable(
                variables_to_sort, list(calculation_order.keys()), parser.variable_map
            )
            variables_to_sort.remove(next_var)
            calculation_order[next_var] = parser.variable_map[next_var]

        sorted_function = cls._create_executable_function(
            function_tree, calculation_order, parser.expr_map
        )
        if save_function:
            cls.save_sorted_function(
                function_tree, calculation_order, parser.expr_map,
                f"sorted_{function_tree.body[0].name}.py"
            )

        # return (
        #     parser.variable_map, 
        #     parser.state_variables, 
        #     parser.expr_map, 
        #     calculation_order,
        #     sorted_function
        # )
        return sorted_function

    @classmethod
    def _pick_next_variable(cls, variables_to_sort, calculated_variables, variable_map):
        """Pick the next variable to calculate."""
        for var in variables_to_sort:
            if not variable_map[var]["dependencies"]:
                return var

            elif all(
                dep in calculated_variables
                for dep in variable_map[var]["dependencies"]
            ):
                return var

            continue

        raise ValueError(
            "Not possible to calculate any of the remaining variables"
        )

    @classmethod
    def _build_sorted_ast(cls, function_tree: ast.Module, calculation_order: OrderedDict, expr_map: dict):
        """Build the AST for the sorted function."""
        # Get the original function definition
        original_func = function_tree.body[0]
        
        # Create new function with sorted statements
        new_func = ast.FunctionDef(
            name=original_func.name,
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg='self', annotation=None)],  # Keep self parameter
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=ast.arg(arg='kwargs', annotation=None),  # Add **kwargs
                defaults=[]
            ),
            body=[],
            decorator_list=[],
            returns=None
        )
        
        # Add sorted assignment statements
        for var_name, info in calculation_order.items():
            new_func.body.append(info["stmt"])
        
        # Add expr statements (like self.end())
        for expr_name, info in expr_map.items():
            new_func.body.append(info["stmt"])
        
        # Create new module with the sorted function
        new_module = ast.Module(body=[new_func], type_ignores=[])

        ast.fix_missing_locations(new_module)
        return new_module

    @classmethod
    def _create_executable_function(cls, function_tree: ast.Module, calculation_order: OrderedDict, expr_map: dict):
        """Create an executable function from the sorted calculation order."""
        new_module = cls._build_sorted_ast(function_tree, calculation_order, expr_map)
        
        # Compile and return executable function
        # TODO give a meaningful name for error codes, not <sorted_acsl>
        compiled = compile(new_module, '<sorted_acsl>', 'exec')
        namespace = {}
        exec(compiled, namespace)
        
        # Get the function name from the original function
        original_func = function_tree.body[0]
        return namespace[original_func.name]

    @classmethod
    def save_sorted_function(cls, function_tree: ast.Module, calculation_order: OrderedDict, 
                           expr_map: dict, filename: str):
        """Save the sorted function code to a file."""
        # Reuse the AST building logic
        new_module = cls._build_sorted_ast(function_tree, calculation_order, expr_map)
        
        # Convert to source code and save
        sorted_code = ast.unparse(new_module)
        
        with open(filename, 'w') as f:
            f.write("# Sorted ACSL function\n")
            f.write("# Generated automatically by AcslSort\n\n")
            f.write(sorted_code)
        
        print(f"Sorted function saved to {filename}")
        return sorted_code

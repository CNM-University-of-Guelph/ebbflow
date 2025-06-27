import ast
from collections import defaultdict

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
        main_function = function_tree.body[0]

        for node in main_function.body:
            if isinstance(node, ast.FunctionDef):
                decorators = [decorator.id for decorator in node.decorator_list]
                if "PROCEDURAL" in decorators:
                    self._collect_procedural(node)
            elif isinstance(node, ast.Assign):
                self._collect_assign(node)
            elif isinstance(node, ast.AnnAssign):
                self._collect_annassign(node)
            elif isinstance(node, ast.Expr):
                self._collect_expr(node)

        self.filter_variable_map()

    def filter_variable_map(self):
        """Remove constants and state variables from the variable map."""
        initial_values = self.state_variables + self.constant_names + ["t"]

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
        elif isinstance(node.value, ast.UnaryOp):
            parameters = self._collect_unaryop(node.value)
        elif isinstance(node.value, ast.Name):
            parameters = [node.value.id]
        elif isinstance(node.value, ast.Subscript):
            parameters = self._collect_subscript(node.value)
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
        elif isinstance(binop.left, ast.Subscript):
            variables.extend(self._collect_subscript(binop.left))

        if isinstance(binop.right, ast.Name):
            variables.append(binop.right.id)
        elif isinstance(binop.right, ast.BinOp):
            variables.extend(self._collect_binop(binop.right))
        elif isinstance(binop.right, ast.Subscript):
            variables.extend(self._collect_subscript(binop.right))

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

        if func_name == "constant":
            return
        elif func_name == "end":
            self.expr_map[func_name] = {
                "stmt": node,
                "dependencies": [],
                "type": "ACSL.end"
            }
        else:
            raise ValueError(f"Unknown function: {func_name}")

    def _collect_unaryop(self, node):
        variables = []
        if isinstance(node.operand, ast.Name):
            variables.append(node.operand.id)
        elif isinstance(node.operand, ast.BinOp):
            variables.extend(self._collect_binop(node.operand))
        elif isinstance(node.operand, ast.UnaryOp):
            variables.extend(self._collect_unaryop(node.operand))
        else:
            raise TypeError(
                f"No method for handling {type(node.operand)} in a unaryop"
            )
        return variables

    def _collect_procedural(self, node):
        """Collect the variables and dependencies for a procedural function."""
        dependencies = [arg.arg for arg in node.args.args]

        return_values = []
        for child_node in ast.walk(node):
            if isinstance(child_node, ast.Return):
                if isinstance(child_node.value, ast.Name):
                    return_values.append(child_node.value.id)
                elif isinstance(child_node.value, ast.Constant):
                    return_values.append(child_node.value.value)
    
        if len(return_values) > 1:
            raise ValueError(
                f"Procedural function {node.name} returns multiple values: {return_values}. Only one return statement is allowed."
                )

        self.variable_map[return_values[0]] = {
            "stmt": node,
            "dependencies": dependencies,
            "type": "procedural"
        }

    def _collect_subscript(self, node):
        """Collect the dependencies for an ast.Subscript node."""
        variables = []
        if isinstance(node.value, ast.Name):
            variables.append(node.value.id)
        elif isinstance(node.value, ast.BinOp):
            variables.extend(self._collect_binop(node.value))
        elif isinstance(node.value, ast.Subscript):
            variables.extend(self._collect_subscript(node.value))
        else:
            raise TypeError(f"No method for handling {type(node.value)} in a subscript")

        if isinstance(node.slice, ast.Name):
            variables.append(node.slice.id)
        elif isinstance(node.slice, ast.BinOp):
            variables.extend(self._collect_binop(node.slice))
        elif isinstance(node.slice, ast.Subscript):
            variables.extend(self._collect_subscript(node.slice))
        else:
            raise TypeError(f"No method for handling {type(node.slice)} in a subscript")
        return variables
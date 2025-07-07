"""Parse the function tree to collect the variables and their dependencies."""

import ast
from collections import defaultdict
from typing import List, Tuple

class FunctionParser:
    """Parse the function tree to collect the variables and their dependencies.

    Parameters
    ----------
    constant_names : list[str]
        A list of constant names.

    Attributes
    ----------
    variable_map : dict[str, dict]
        A dictionary mapping variable names to their dependencies.
    expr_map : dict[str, dict]
        A dictionary mapping a function name to the ast.Expr node that
        represents the function call.
    constant_names : list[str]
        A list of constant names.
    state_variables : list[str]
        A list of state variable names.
    """
    def __init__(self, constant_names: List[str]):
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

    def collect_variables(self, function_tree: ast.Module, include_constants: bool = False) -> None:
        """Collect the calcualted variables and their dependencies.

        Parameters
        ----------
        function_tree : ast.Module
            The AST of the function.
        include_constants : bool
            Whether to include constants in the dependencies.

        Returns
        -------
        None
        """
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

        if not include_constants:
            self.filter_variable_map()

    def filter_variable_map(self) -> None:
        """Remove constants and state variables from the variable map.

        Parameters
        ----------
        None
        """
        initial_values = self.state_variables + self.constant_names + ["t"]

        for var_name, info in self.variable_map.items():
            info["dependencies"] = [
                dep for dep in info["dependencies"]
                if dep not in initial_values
            ]
            self.variable_map[var_name] = info

    def _collect_assign(self, node: ast.Assign) -> None:
        """Collect the variables and dependencies for an ast.Assign node.

        Parameters
        ----------
        node : ast.Assign
            The AST of the assignment.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the assignment has multiple targets.
        TypeError
            If the assignment value is not a supported node type.
        """
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

    def _collect_annassign(self, node: ast.AnnAssign) -> None:
        """Collect the variables and dependencies for an ast.AnnAssign node.

        Parameters
        ----------
        node : ast.AnnAssign
            The AST of the annotation assignment.

        Returns
        -------
        None

        Raises
        ------
        TypeError
            If the assignment value is not a supported node type.
        """
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

    def _collect_binop(self, binop: ast.BinOp) -> List[str]:
        """Collect the dependencies for an ast.BinOp node.

        Parameters
        ----------
        binop : ast.BinOp
            The AST of the binary operation.
        """
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

    def _collect_call(self, node: ast.Call) -> Tuple[List[str], bool]:
        """Collect the dependencies for an ast.Call node.

        Parameters
        ----------
        node : ast.Call
            The AST of the call.

        Returns
        -------
        tuple[list[str], bool]
            A tuple containing a list of variables and a boolean indicating
            whether the target is a state variable.
        """
        variables = []
        is_state_var = False
        if isinstance(node.args, list):
            variables.extend([
                arg.id for arg in node.args if isinstance(arg, ast.Name)
            ])
        # NOTE: Collecting keywords this way gives the keyword name, not the
        # value. Likely need to enforce rule that variables are not passed as
        # keywords.
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

    def _collect_expr(self, node: ast.Expr) -> None:
        """Create a dict of ast.Expr nodes to include in the output function.

        Parameters
        ----------
        node : ast.Expr
            The AST of the expression.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the function is not one of the supported function names.
        ValueError
            If the function name cannot be determined.
        """
        if isinstance(node.value.func, ast.Name):
            func_name = node.value.func.id
        elif isinstance(node.value.func, ast.Attribute):
            func_name = node.value.func.attr
        else:
            raise ValueError("Unable to determine function name")

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

    def _collect_unaryop(self, node: ast.UnaryOp) -> List[str]:
        """Collect the dependencies for an ast.UnaryOp node.

        Parameters
        ----------
        node : ast.UnaryOp
            The AST of the unary operation.

        Returns
        -------
        list[str]
            A list of variable names.

        Raises
        ------
        TypeError
            If the operand is not a supported node type.
        """
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

    def _collect_procedural(self, node: ast.FunctionDef) -> None:
        """Collect the variables and dependencies for a procedural function.

        Parameters
        ----------
        node : ast.FunctionDef
            The AST of the function.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the function has multiple return statements.
        """
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
                f"Procedural function {node.name} returns multiple values: "
                f"{return_values}. Only one return statement is allowed."
            )

        self.variable_map[return_values[0]] = {
            "stmt": node,
            "dependencies": dependencies,
            "type": "procedural"
        }

    def _collect_subscript(self, node: ast.Subscript) -> List[str]:
        """Collect the dependencies for an ast.Subscript node.

        Parameters
        ----------
        node : ast.Subscript
            The AST of the subscript.

        Returns
        -------
        list[str]
            A list of variable names.

        Raises
        ------
        TypeError
            If the subscript is not a supported node type.
        """
        variables = []
        if isinstance(node.value, ast.Name):
            variables.append(node.value.id)
        elif isinstance(node.value, ast.BinOp):
            variables.extend(self._collect_binop(node.value))
        elif isinstance(node.value, ast.Subscript):
            variables.extend(self._collect_subscript(node.value))
        else:
            raise TypeError(
                f"No method for handling {type(node.value)} in a subscript"
            )

        if isinstance(node.slice, ast.Name):
            variables.append(node.slice.id)
        elif isinstance(node.slice, ast.BinOp):
            variables.extend(self._collect_binop(node.slice))
        elif isinstance(node.slice, ast.Subscript):
            variables.extend(self._collect_subscript(node.slice))
        else:
            raise TypeError(
                f"No method for handling {type(node.slice)} in a subscript"
            )
        return variables

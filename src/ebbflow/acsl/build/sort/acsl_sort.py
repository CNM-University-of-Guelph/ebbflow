"""Implement ACSL sorting algorithm."""

import ast
import hashlib
from collections import OrderedDict
from typing import List, Dict

from ebbflow.acsl.build.sort.function_parser import FunctionParser

class AcslSort:
    """Implement ACSL sorting algorithm.

    Parameters
    ----------
    function_tree : ast.Module
        The AST of the function.
    constant_names : list[str]
        A list of constant names.

    Attributes
    ----------
    calculation_order : OrderedDict
        A dictionary mapping variable names to their calculation order.

    Returns
    -------
    None
    """
    @classmethod
    def sort(
        cls,
        function_tree: ast.Module,
        constant_names: List[str],
    ) -> ast.Module:
        """Sort the function tree so all variables can be calculated.

        Parameters
        ----------
        function_tree : ast.Module
            The AST of the function.
        constant_names : list[str]
            A list of constant names.

        Returns
        -------
        ast.Module
            The sorted AST.
        """
        parser = FunctionParser(constant_names)
        parser.collect_variables(function_tree)

        variables_to_sort = set(parser.variable_map.keys())
        cls.calculation_order = OrderedDict()

        while variables_to_sort:
            next_var = cls._pick_next_variable(
                variables_to_sort,
                list(cls.calculation_order.keys()),
                parser.variable_map
            )
            variables_to_sort.remove(next_var)
            cls.calculation_order[next_var] = parser.variable_map[next_var]
        sorted_tree = cls._build_sorted_ast(
            function_tree, parser.expr_map
        )
        return sorted_tree

    @classmethod
    def _pick_next_variable(
        cls,
        variables_to_sort: List[str],
        calculated_variables: List[str],
        variable_map: Dict[str, Dict]
    ) -> str:
        """Pick the next variable to calculate.

        Parameters
        ----------
        variables_to_sort : list[str]
            A list of variable names to sort.
        calculated_variables : list[str]
            A list of variable names that have been calculated.
        variable_map : dict[str, dict]
            A dictionary mapping variable names to their dependencies.

        Returns
        -------
        str
            The name of the next variable to calculate.
        """
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
    def _build_sorted_ast(
        cls,
        function_tree: ast.Module,
        expr_map: Dict[str, Dict]
    ) -> ast.Module:
        """Build the AST for the sorted function.

        Parameters
        ----------
        function_tree : ast.Module
            The AST of the function.
        expr_map : dict[str, dict]
            A dictionary mapping a function name to the ast.Expr node that
            represents the function call.

        Returns
        -------
        ast.Module
            The sorted AST.
        """
        original_func = function_tree.body[0]
        new_func = ast.FunctionDef(
            name=original_func.name,
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="self", annotation=None)],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            ),
            body=[],
            decorator_list=[],
            returns=None
        )
        procedural_functions = []

        for var_name, info in cls.calculation_order.items():
            if info["type"] == "assign":
                new_func.body.append(info["stmt"])
            elif info["type"] == "procedural":
                procedural_functions.append(info["stmt"])
                new_func.body.append(
                    cls._create_procedural_call(var_name, info["stmt"])
                )
            elif info["type"] == "delay":
                new_func.body.append(
                    cls._create_delay_call(var_name, info["stmt"])
                )
            else:
                raise ValueError(f"Unknown type: {info["type"]}")

        for _, info in expr_map.items():
            new_func.body.append(info["stmt"])

        module_body = procedural_functions + [new_func]
        new_module = ast.Module(body=module_body, type_ignores=[])
        ast.fix_missing_locations(new_module)
        return new_module

    @classmethod
    def _create_procedural_call(
        cls,
        var_name: str,
        stmt: ast.Call
    ) -> ast.Assign:
        """Create a call to a procedural function.

        Parameters
        ----------
        var_name : str
            The name of the variable to assign the result to.
        stmt : ast.Call
            The ast.Call node that represents the function call.

        Returns
        -------
        ast.Assign
            The ast.Assign node that represents the assignment.
        """
        args = [ast.Name(id=arg.arg, ctx=ast.Load()) for arg in stmt.args.args]
        function_call = ast.Call(
            func=ast.Name(id=stmt.name, ctx=ast.Load()),
            args=args,
            keywords=[]
        )
        return ast.Assign(
            targets=[ast.Name(id=var_name, ctx=ast.Store())],
            value=function_call
        )

    @classmethod
    def _create_delay_call(
        cls,
        var_name: str,
        stmt: ast.Assign
    ) -> ast.Assign:
        """Add delay_id to the delay call.

        Parameters
        ----------
        var_name : str
            The name of the variable to assign the result to.
        stmt : ast.Assign
            The ast.Assign node that represents the assignment.

        Returns
        -------
        ast.Assign
            The ast.Assign node that represents the assignment.
        """
        args = stmt.value.args
        delay_id = hashlib.md5(str(args + [var_name]).encode()).hexdigest()
        new_assign = ast.Assign(
            targets=[ast.Name(id=var_name, ctx=ast.Store())],
            value=stmt.value
        )
        new_assign.value.args.append(ast.Constant(value=delay_id))
        return new_assign

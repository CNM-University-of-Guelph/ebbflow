import ast
from collections import OrderedDict

from ebbflow.acsl.build.sort.function_parser import FunctionParser

class AcslSort:
    @classmethod
    def sort(
        cls,
        function_tree: ast.Module,
        constant_names: list[str],
    ):
        """Implement ACSL Sorting Algorithm"""
        parser = FunctionParser(constant_names)
        parser.collect_variables(function_tree)

        variables_to_sort = set(parser.variable_map.keys())
        cls.calculation_order = OrderedDict()

        while variables_to_sort:
            next_var = cls._pick_next_variable(
                variables_to_sort, list(cls.calculation_order.keys()), parser.variable_map
            )
            variables_to_sort.remove(next_var)
            cls.calculation_order[next_var] = parser.variable_map[next_var]
        sorted_tree = cls._build_sorted_ast(
            function_tree, parser.expr_map
        )
        return sorted_tree

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
    def _build_sorted_ast(cls, function_tree: ast.Module, expr_map: dict):
        """Build the AST for the sorted function."""
        original_func = function_tree.body[0]
        new_func = ast.FunctionDef(
            name=original_func.name,
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg='self', annotation=None)],
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
                new_func.body.append(cls._create_procedural_call(var_name, info["stmt"]))
            else:
                raise ValueError(f"Unknown type: {info['type']}")

        for expr_name, info in expr_map.items():
            new_func.body.append(info["stmt"])

        module_body = procedural_functions + [new_func]
        new_module = ast.Module(body=module_body, type_ignores=[])
        ast.fix_missing_locations(new_module)
        return new_module

    @classmethod
    def _create_procedural_call(cls, var_name, stmt):
        """Create a call to a procedural function."""
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

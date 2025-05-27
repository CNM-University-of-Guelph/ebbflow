import ast
import inspect
import textwrap
from types import MethodType
from typing import Callable, Union

from ebbflow.acsl.state_managers.constant_manager import ConstantManager
from ebbflow.acsl.visitors.constant_collector import ConstantCollector
from ebbflow.acsl.visitors.statevar_collector import StatevarCollector
from ebbflow.acsl.sorting.sort import AcslSort

class ACSL():
    """Implements the main program loop for ACSL"""
    def __init__(self):
        self.stop_flag = False
        self._section_mapping = {}
        self.state_vars = {}
        self._previous_section_scope = ()
        self._constant_manager = ConstantManager()
        self._validate_sections()
        self._create_section_mapping()
        self._sections_to_sort = self._find_sections_to_sort()

    def _validate_sections(self):
        """
        Validate:
        1. Each section appears at most once
        2. DERIVATIVE and DISCRETE sections require a DYNAMIC section
        """
        found_sections = set()
        for _, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "_acsl_section"):
                section_type = method._acsl_section

                if section_type in found_sections:
                    raise ValueError(f"Duplicate section: {section_type}")
                found_sections.add(section_type)

        has_dynamic = "DYNAMIC" in found_sections
        has_derivative = "DERIVATIVE" in found_sections
        has_discrete = "DISCRETE" in found_sections

        if (has_derivative or has_discrete) and not has_dynamic:
            if has_derivative:
                raise ValueError("DERIVATIVE section requires DYNAMIC section")
            else:
                raise ValueError("DISCRETE section requires DYNAMIC section")

    def _create_section_mapping(self):
        """
        Create a mapping of section names to their corresponding functions.
        This allows for easy access to section methods by name.
        """        
        for _, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "_acsl_section"):
                self._section_mapping[method._acsl_section] = method

    def _find_sections_to_sort(self):
        sections_to_sort = []
        for section, method in self._section_mapping.items():
            if method._sort:
                sections_to_sort.append(section)
        return sections_to_sort

    def _collect_constants(self):
        """
        Parse each section to collect constants defined with set_constants.
        """
        try:
            self._constant_manager._set_collection_mode(True)
            for section_name, method in self._section_mapping.items():
                try:
                    source = inspect.getsource(method)
                    source_dedent = textwrap.dedent(source)
                    tree = ast.parse(source_dedent)
                    collector = ConstantCollector(self._constant_manager)
                    collector.visit(tree)

                    for const_name, const_value in collector.found_constant_calls:
                        self.set_constant(const_name, const_value)

                except Exception as e:
                    print(
                        f"Warning: Error collecting constants from {section_name} section: {e}"
                    )
        finally:
            self._constant_manager._set_collection_mode(False)

        if "INITIAL" in self._section_mapping:
            self._section_mapping["INITIAL"]()
            self._constant_manager._set_collection_mode(True)
            self._constant_manager.collect_initial_constants(
                self._previous_section_scope
            )
            self._constant_manager._set_collection_mode(False)

    def _collect_statevars(self):
        """
        Parse each section to collect state variables defined with set_statevars.
        """
        # NOTE self.integ can only be used in sorted sections
        for section in self._sections_to_sort:
            try:
                source = inspect.getsource(self._section_mapping[section])
                source_dedent = textwrap.dedent(source)
                tree = ast.parse(source_dedent)
                collector = StatevarCollector()
                collector.visit(tree)

            except Exception as e:
                print(
                    f"Warning: Error collecting state variables from {section} section: {e}"
                )
        return collector.found_integ_calls

    def set_constant(self, name: str, value: Union[int, float, bool]):
        self._constant_manager.set_constant(name, value)

    def integ(self, deriv, ic):
        """Implement integration here"""
        return ic

    def sort(self, func: Callable):
        """Sort the function so that variables are in calculation order."""
        try:
            source = inspect.getsource(func)
            source_dedent = textwrap.dedent(source)
            tree = ast.parse(source_dedent)
            # variable_map, state_variables, expr_map, calculation_order, sorted_func = AcslSort.sort(
            sorted_func = AcslSort.sort(
                tree, self._constant_manager.constants.keys()
            )
            bound_sorted_func = MethodType(sorted_func, self)
            self._section_mapping[func._acsl_section] = bound_sorted_func
            # print("Variable map:")
            # for key, value in variable_map.items():
            #     print(f"{key}: {value}")
            # print(f"\nState variables: {state_variables}")
            # print(f"\nExpr map:")
            # for key, value in expr_map.items():
            #     print(f"{key}: {value}")
            # print(f"\nCalculation order:")
            # for key, value in calculation_order.items():
            #     print(f"{key}: {value}")

        except Exception as e:
            print(f"Warning: Error sorting function: {e}")

    def end(self):
        """
        Capture the local scope of the calling section. 

        This is required at the end of each section method.
        """
        frame = inspect.currentframe().f_back

        try:
            func_name = frame.f_code.co_name
            section_name = None
            for name, method in self._section_mapping.items():
                if method.__name__ == func_name:
                    section_name = name
                    break
            
            if section_name:
                local_vars = frame.f_locals.copy()
                filtered_vars = {
                    name: value for name, value in local_vars.items()
                    if not name.startswith('_') and
                    not callable(value) and
                    name != "self"
                }

                self._previous_section_scope = (section_name, filtered_vars)
                # print(f"DEBUG: Ending {section_name} section")
                # print(f"DEBUG: Captured scope: {self._previous_section_scope}")
                                
        finally:
            del frame

    def run(self):
        self._collect_constants()
        self.state_vars = self._collect_statevars()
        for section in self._sections_to_sort:
            self.sort(self._section_mapping[section])
        
        
        # if "INITIAL" in self._section_mapping:
        #     # self._section_mapping["INITIAL"]()
        #     pass
        
        # if "DERIVATIVE" in self._section_mapping:
        #     self.sort(self._section_mapping["DERIVATIVE"])
            # TODO for initial time step need to provide the state variables w/ initial value
            # constants = self._constant_manager.constants
            # self._section_mapping["DERIVATIVE"](**constants)
        
        # if "DYNAMIC" in self._section_mapping:
        #     pass

        print(f"Finished running {self.__class__.__name__}")

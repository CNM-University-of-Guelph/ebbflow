import ast
import inspect
import textwrap
from typing import Callable, Union

from ebbflow.acsl.constant_manager import ConstantManager
from ebbflow.acsl.constant_collector import ConstantCollector

class ACSL():
    """Implements the main program loop for ACSL"""
    def __init__(self):
        self.stop_flag = False
        self._section_mapping = {}
        self._constant_manager = ConstantManager()
        self._validate_sections()
        self._create_section_mapping()

    @staticmethod
    def INITIAL(func: Callable) -> Callable:
        func._acsl_section = 'INITIAL'
        return func

    @staticmethod
    def DYNAMIC(func: Callable) -> Callable:
        func._acsl_section = 'DYNAMIC'
        return func

    @staticmethod
    def DERIVATIVE(func: Callable) -> Callable:
        func._acsl_section = 'DERIVATIVE'
        return func

    @staticmethod
    def DISCRETE(func: Callable) -> Callable:
        func._acsl_section = 'DISCRETE'
        return func

    @staticmethod
    def TERMINAL(func: Callable) -> Callable:
        func._acsl_section = 'TERMINAL'
        return func

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

    def set_constant(self, name: str, value: Union[int, float, bool]):
        self._constant_manager.set_constant(name, value)

    def run(self):
        self._collect_constants()

        if "INITIAL" in self._section_mapping:
            self._section_mapping["INITIAL"]()
            # pass
        if "DYNAMIC" in self._section_mapping:
            pass


        print(f"Finished running {self.__class__.__name__}")

"""Take the user defined ACSL model and build an executable model.
"""
import ast
from typing import Dict, Tuple

from ebbflow.acsl.preprocessing.constant_manager import ConstantManager
from ebbflow.acsl.visitors.statevar_collector import StatevarCollector
from ebbflow.acsl.preprocessing.acsl_sort import AcslSort
from ebbflow.acsl.build.acsl_section import AcslSection
from ebbflow.acsl.build.acsl_run import AcslRun
from ebbflow.acsl.visitors.integration_settings_collector import IntegrationSettingsCollector
from ebbflow.acsl.visitors.integ_function_creator import IntegFunctionCreator
from ebbflow.acsl.integration.integration_manager import IntegrationManager

class AcslBuild:
    """Build the AcslSection objects and configure AcslRun instance.
    """
    def __init__(
            self,
            section_trees: Dict[str, Tuple[ast.AST, Dict]],
            initial_scope: Tuple[str, Dict],
            TSTP: float,
            CINT: int = None,
            report: list = None
        ):
        self.section_trees = section_trees
        self.constants = {}
        self.statevars = {}
        self.acsl_sections = {}
        self.integration_settings = {
            "IALG": None,
            "NSTP": None,
            "MAXT": None,
        }
        self.CINT = CINT # NOTE: Passed in from Acsl.run() method
        self.TSTP = TSTP
        self.constant_manager = ConstantManager(initial_scope)
        self.statevar_collector = StatevarCollector()
        self.sorter = AcslSort()
        self.integration_settings_collector = IntegrationSettingsCollector()
        self.integ_function_creator = IntegFunctionCreator()
        self.variables_to_report = report

    def build(self):
        # Collect constants
        for section_name, tree, _ in self._iterate("_collect_constants"):
            self.constant_manager.collect(section_name, tree)
        self.constants = self.constant_manager.constants

        # Collect statevars
        for section_name, tree, _ in self._iterate("_collect_statevars"):
            self.statevar_collector.visit(tree)
        self.statevars = self.statevar_collector.integ_calls

        # Sort sections
        for section_name, tree, metadata in self._iterate("_sort"):
            self.section_trees[section_name] = (self.sorter.sort(
                tree, self.constants.keys()
            ), metadata)

        # Collect integration settings from DYNAMIC section
        self.integration_settings_collector.visit(self.section_trees.get("DYNAMIC")[0])
        self.integration_settings = self.integration_settings_collector.settings
        
        # Set CINT from constants
        self.CINT = self.constants.get("CINT", self.CINT)
        if self.CINT is None:
            self.CINT = self.integration_settings.get("CINT", None)
        if self.CINT is None or not isinstance(self.CINT, int):
            self.CINT = 1  # NOTE: set default for cases where CINT is defined in Dynamic
                           # Need to be able to initalize the integration routine which means IntegrationManager
                           # needs to be initialized with a value

        # Create executables for integration manager
        derivative_functions = {}
        self.integ_function_creator.set_constants(list(self.constants.keys()))
        for section_name, tree, metadata in self._iterate("_sort"):
            if metadata.get("_sort", False):
                integ_funcs = self.integ_function_creator.visit(tree)
                derivative_functions.update(integ_funcs)

        integ_manager = IntegrationManager(
            self.integration_settings["IALG"],
            self.integration_settings["MAXT"],
            self.integration_settings["NSTP"],
            self.CINT,
            derivative_functions
        )

        # Process sections to executable functions
        for section_name, tree, _ in self._iterate("_acsl_section"):
            self.acsl_sections[section_name] = AcslSection(
                section_name, tree, integ_manager
            )
            self.acsl_sections[section_name].modify_signature(
                self.constants, self.statevars
            )
            self.acsl_sections[section_name].remove_decorators()
            self.acsl_sections[section_name].remove_self_calls()
            self.acsl_sections[section_name].create_executable()

        return AcslRun(
            TSTP=self.TSTP,
            CINT=self.CINT,
            variables_to_report=self.variables_to_report,
            constants=self.constants,
            statevars=self.statevars,
            dynamic=self.acsl_sections.get("DYNAMIC"),
            derivative=self.acsl_sections.get("DERIVATIVE"),
            discrete=self.acsl_sections.get("DISCRETE"),
            terminal=self.acsl_sections.get("TERMINAL"),
        )

    def _iterate(self, filter: str):
        """
        Iterate over the section trees and yield the section name, tree, and metadata
        if the section name matches the filter.
        """
        for section_name, (tree, metadata) in self.section_trees.items():
            if metadata.get(filter):
                yield section_name, tree, metadata

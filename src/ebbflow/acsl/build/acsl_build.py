"""Build an executable AcslRun instance from the user-defined sections of an 
ACSL model.
"""
import ast
from typing import Dict, Tuple, Optional, List

from ebbflow.acsl.build.ast_visitors.constant_manager import ConstantManager
from ebbflow.acsl.build.ast_visitors.statevar_collector import StatevarCollector
from ebbflow.acsl.build.sort.acsl_sort import AcslSort
from ebbflow.acsl.build.section.acsl_section import AcslSection
from ebbflow.acsl.run.acsl_run import AcslRun
from ebbflow.acsl.build.ast_visitors.integration_settings_collector import IntegrationSettingsCollector
from ebbflow.acsl.build.ast_visitors.integ_function_creator import IntegFunctionCreator
from ebbflow.acsl.integration.integration_manager import IntegrationManager

class AcslBuild:
    """Create an executable AcslRun instance from the user-defined sections of 
    an ACSL model. An ACSL model inherits from the Acsl class and is defined by
    a set of user-defined functions.
    
    Parameters
    ----------
    section_trees : Dict[str, Tuple[ast.AST, Dict]]
        A dictionary of section name, AST tree and metadata.
    initial_scope : Tuple[str, Dict]
        A tuple containing the scope of the INITIAL section.
    TSTP : float | int
        The stop time.
    CINT : int, optional
        The communication interval used for reporting. This is also used
        to determine the integration step size.
    report : list, optional
        A list of variable names to include in the ouput.
    """
    def __init__(
            self,
            section_trees: Dict[str, Tuple[ast.AST, Dict]],
            initial_scope: Tuple[str, Dict],
            TSTP: float | int, # pylint: disable=invalid-name
            CINT: Optional[float | int] = None, # pylint: disable=invalid-name
            report: Optional[List[str]] = None
        ):
        self.section_trees = section_trees
        self.constants = {}
        self.statevars = {}
        self.integration_settings = {
            "IALG": None,
            "NSTP": None,
            "MAXT": None,
        }
        self.CINT = CINT # pylint: disable=invalid-name
        self.TSTP = TSTP # pylint: disable=invalid-name
        self.constant_manager = ConstantManager(initial_scope)
        self.statevar_collector = StatevarCollector()
        self.sorter = AcslSort()
        self.integration_settings_collector = IntegrationSettingsCollector()
        self.integ_function_creator = IntegFunctionCreator()
        self.variables_to_report = report

    def build(self):
        """Build the executable AcslRun instance.
        
        This method will collect the constants, statevars, integration settings
        and create the executables for the sections. Calls to procedural blocks
        are added to the respective executable. Functions are created for the 
        differential equation of each state variable to be used by the 
        integration routine.

        Returns
        -------
        AcslRun
            An AcslRun instance that will exercise the model.
        """
        # Collect constants
        for section_name, tree, _ in self._iterate("collect_constants"):
            self.constant_manager.collect(tree)
        self.constants = self.constant_manager.constants

        # Collect statevars
        for section_name, tree, _ in self._iterate("collect_statevars"):
            self.statevar_collector.visit(tree)
        self.statevars = self.statevar_collector.integ_calls

        # Sort sections
        for section_name, tree, metadata in self._iterate("sort"):
            self.section_trees[section_name] = (self.sorter.sort(
                tree, self.constants.keys()
            ), metadata)

        # Collect integration settings from DYNAMIC section
        self.integration_settings_collector.visit(
            self.section_trees.get("DYNAMIC")[0]
        )
        self.integration_settings = self.integration_settings_collector.settings

        # Set CINT from constants
        self.CINT = self.constants.get("CINT", self.CINT)
        if self.CINT is None:
            self.CINT = self.integration_settings.get("CINT", None)
        if self.CINT is None or not isinstance(self.CINT, int):
            self.CINT = 1
            # NOTE: set default for cases where CINT is defined in Dynamic
            # Need to be able to initalize the integration routine which means
            # IntegrationManager needs to be initialized with a value

        # Create executables for integration manager
        derivative_functions = {}
        self.integ_function_creator.set_constants(list(self.constants.keys()))
        for section_name, tree, metadata in self._iterate("sort"):
            if metadata.get("sort", False):
                integ_funcs = self.integ_function_creator.visit(tree)
                derivative_functions.update(integ_funcs)

        integ_manager = IntegrationManager(
            self.integration_settings["IALG"],
            self.integration_settings["MAXT"],
            self.integration_settings["NSTP"],
            self.CINT
        )

        # Process sections to executable functions
        section_functions = {}
        for section_name, tree, _ in self._iterate("acsl_section"):
            section_functions[section_name] = AcslSection(
                section_name, tree
            )
            section_functions[section_name].modify_signature(
                self.constants, self.statevars
            )
            section_functions[section_name].remove_decorators()
            section_functions[section_name].remove_self_calls()
            section_functions[section_name].create_executable()

        dynamic_func = (
            section_functions.get("DYNAMIC").executable_func
            if section_functions.get("DYNAMIC")
            else None
        )
        derivative_func = (
            section_functions.get("DERIVATIVE").executable_func
            if section_functions.get("DERIVATIVE")
            else None
        )
        discrete_func = (
            section_functions.get("DISCRETE").executable_func
            if section_functions.get("DISCRETE")
            else None
        )
        terminal_func = (
            section_functions.get("TERMINAL").executable_func
            if section_functions.get("TERMINAL")
            else None
        )

        return AcslRun(
            TSTP=self.TSTP,
            CINT=self.CINT,
            variables_to_report=self.variables_to_report,
            constants=self.constants,
            statevars=self.statevars,
            integration_manager=integ_manager,
            dynamic=dynamic_func,
            derivative=derivative_func,
            discrete=discrete_func,
            terminal=terminal_func,
            derivative_functions=derivative_functions
        )

    def _iterate(self, attribute: str):
        """Iterate over the section trees and yield the section name, tree, and
        metadata if the section name matches the attribute name.

        Parameters
        ----------
        attribute : str
            The attribute name to filter by.

        Yields
        ------
        section_name : str
            The name of the section.
        tree : ast.AST
            The AST tree of the section.
        metadata : Dict
            The metadata of the section with instruction for how to process the
            section tree.
        """
        for section_name, (tree, metadata) in self.section_trees.items():
            if metadata.get(attribute):
                yield section_name, tree, metadata

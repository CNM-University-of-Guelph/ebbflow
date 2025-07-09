"""Implements the main loop of the ACSL software."""
from typing import Dict, Optional, Callable, List

import pandas as pd
import numpy as np

from ebbflow.acsl.build.section.acsl_section import AcslSection
from ebbflow.acsl.acsl_lib import AcslLib
from ebbflow.acsl.integration.integration_manager import IntegrationManager

class AcslRun(AcslLib):
    """Run the ACSL model.
    
    Parameters
    ----------
    TSTP : float
        The stop time for the simulation.
    CINT : float
        The communication interval.
    variables_to_report : list
        The variables to include in the results DataFrame.
    constants : dict
        The constants used in the model.
    statevars : dict
        The state variables used in the model.
    integration_manager : IntegrationManager
        The integration manager implementing the integration routine.
    dynamic : AcslSection
        The dynamic section of the model.
    derivative : AcslSection
        The derivative section of the model.
    discrete : AcslSection
        The discrete section of the model.
    terminal : AcslSection
        The terminal section of the model.

    Attributes
    ----------
    integration_manager : IntegrationManager
        The integration manager implementing the integration routine.
    stop_flag : bool
        Whether to stop the simulation.
    TSTP : float
        The stop time for the simulation.
    CINT : float
        The communication interval.
    t : float
        The current time.
    constants : dict
        The constants used in the model.
    statevars : dict
        The state variables used in the model.
    _current_section : str
        The section currently being executed.
    dynamic : AcslSection
        The dynamic section of the model.
    derivative : AcslSection
        The derivative section of the model.
    discrete : AcslSection
        The discrete section of the model.
    terminal : AcslSection
        The terminal section of the model.
    step_size : float
        The step size for the integration.
    variables_to_report : list
        The variables to include in the results DataFrame.
    results : pd.DataFrame
        The results of the simulation.
    """
    def __init__(
        self,
        TSTP: float,
        CINT: float,
        variables_to_report: list,
        constants: Dict,
        statevars: Dict,
        integration_manager: IntegrationManager,
        dynamic: Optional[AcslSection]=None,
        derivative: Optional[AcslSection]=None,
        discrete: Optional[AcslSection]=None,
        terminal: Optional[AcslSection]=None,
        derivative_functions: Optional[Dict[str, Callable]]=None
    ):
        super().__init__(integration_manager=integration_manager)
        self.stop_flag = False
        self.TSTP = TSTP # pylint: disable=invalid-name
        self.CINT = CINT # pylint: disable=invalid-name
        self.t = 0
        self.constants = constants
        self.statevars = statevars
        self._current_section = None

        self.dynamic = self.bind_section_function(dynamic, "DYNAMIC")
        self.derivative = self.bind_section_function(derivative, "DERIVATIVE")
        self.discrete = self.bind_section_function(discrete, "DISCRETE")
        self.terminal = self.bind_section_function(terminal, "TERMINAL")
        self.derivative_functions = {}
        for deriv_name, (deriv_func, arg_names) in derivative_functions.items():
            self.derivative_functions[deriv_name] = (
                self.bind_derivative_function(deriv_func, arg_names),
                arg_names
            )

        self.step_size = self.integration_manager.step_size
        self.variables_to_report = set(
            variables_to_report + list(self.statevars.keys())
        )
        self.results = pd.DataFrame(columns=["t"] + list(self.variables_to_report))

    def run(self):
        """The main loop of the ACSL software."""
        self._initialize_integration_routine()

        if self.t == 0:
            # self.dynamic(**self._get_initial_arguments())
            # self._store_results(self.previous_section_scope)
            self.derivative(**self._get_initial_arguments())
            self._store_results(self.previous_section_scope)
            self.t += self.step_size

        while self.t <= self.TSTP:
            # self.dynamic(**self._get_arguments())
            # self._store_results(self.previous_section_scope)
            self.derivative(**self._get_arguments())
            self._store_results(self.previous_section_scope)
            self.t += self.step_size

        return self._get_final_results()

    def bind_section_function(
        self,
        func: Callable,
        section_name: str
    ) -> Callable:
        """Bind a section function to the class.

        Parameters
        ----------
        func : Callable
            The function to bind.
        section_name : str
            The name of the section to bind.

        Returns
        -------
        Callable
            The bound function.
        """
        if func is None:
            # Default method that does not affect state
            def default_section(self, **arguments): # pylint: disable=unused-argument
                self.end()
            return default_section

        def bound_method(**arguments):
            # Set section context if provided
            old_section = getattr(self, "_current_section", None)
            if section_name:
                self._current_section = section_name

            try:
                # Call the original function with self as first argument
                return func(self, **arguments)
            finally:
                # Restore previous section context
                if section_name:
                    self._current_section = old_section

        return bound_method
    
    def bind_derivative_function(self, func: Callable, arg_names: List[str]) -> Callable:
        """Bind a derivative function to the class.
        
        Parameters
        ----------
        func : Callable
            The function to bind.
        arg_names : List[str]
            The names of the arguments to the function.
        Returns
        -------
        Callable
            The bound function.
        """
        def bound_method(**arguments):
            return func(self, **arguments)
        return bound_method

    def _initialize_integration_routine(self) -> None:
        """Initialize the integration routine."""
        try:
            self.derivative(**self._get_initial_arguments())
        except (ValueError, KeyError):
            raise ValueError(
                "DERIVATIVE section failed to run. "
                "Check that all variables are defined."
            )
        try:
            self.dynamic(**self._get_initial_arguments())
        except (ValueError, KeyError):
            raise ValueError(
                "DYNAMIC section failed to run. "
                "Check that all variables are defined."
            )

    def _get_initial_arguments(self) -> Dict[str, float]:
        """Get the initial arguments for the simulation.

        Returns
        -------
        dict
            The initial arguments for the simulation.
        """
        initial_statevars = {
            key: self.constants[value] if isinstance(value, str) else value
            for key, value in self.statevars.items()
        }
        initial_statevars["t"] = self.t
        return {
            **self.constants,
            **initial_statevars
        }

    def _get_arguments(self) -> Dict[str, float]:
        """Get the arguments for the simulation using values from the previous 
        time step.

        Returns
        -------
        dict
            The arguments for the simulation.
        """
        new_statevars = {
            key: self.previous_section_scope[1][value]
            if isinstance(value, str)
            else value
            for key, value in self.statevars.items()
        }
        for statevar, init_value in self.statevars.items():
            if isinstance(init_value, str):
                new_statevars[init_value] = self.previous_section_scope[1][statevar]
        return {
            "t": self.t,
            **self.constants,
            **new_statevars
        }

    def _store_results(self, previous_section_scope: Dict) -> None:
        """Store the results of the simulation.

        Parameters
        ----------
        previous_section_scope : dict
            The local scope of the previously executed section.
        """
        results = {
            var_name: previous_section_scope[1][var_name]
            for var_name in self.variables_to_report
        }
        self.results.loc[self.t] = [self.t] + list(results.values())

    def _get_final_results(self) -> pd.DataFrame:
        """Extract results at communication interval (CINT) by finding the
        closest time points in the results DataFrame.

        Returns
        -------
        pd.DataFrame
            The final results of the simulation.
        """
        cint_times = np.arange(0, self.TSTP + self.CINT, self.CINT)
        final_results = pd.DataFrame(columns=self.results.columns)

        for target_time in cint_times:
            if target_time > self.TSTP:
                break

            time_diffs = np.abs(self.results["t"] - target_time)
            close_idx = time_diffs.idxmin()
            final_results.loc[len(final_results)] = self.results.loc[close_idx]

        return final_results

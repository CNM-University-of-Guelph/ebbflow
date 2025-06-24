"""Implements the main loop of the ACSL software."""

# NOTE: Need to determine how this class will be implemented. One option is to 
# rebuild the model class from the AcslBuild instance. Then Inherit AcslLib to get
# the ACSL function library and have this class override the run method.
# The modified run method will implement the main loop of the ACSL software.
# At this point all of the sections will be executable and all the variables needed
# will have been collected. The end() method will push results the dynamically generated
# class. From there this class would need to handle saving the results over time.

from ebbflow.acsl.build.acsl_section import AcslSection
from typing import Dict

import pandas as pd
import numpy as np

class AcslRun:
    def __init__(
        self,
        TSTP: float,
        CINT: float,
        variables_to_report: list,
        constants: Dict,
        statevars: Dict,
        dynamic: AcslSection=None,
        derivative: AcslSection=None,
        discrete: AcslSection=None,
        terminal: AcslSection=None,
    ):
        self.stop_flag = False
        self.TSTP = TSTP
        self.CINT = CINT
        self.t = 0
        self.constants = constants
        self.statevars = statevars
        self.dynamic = dynamic
        self.derivative = derivative
        self.discrete = discrete
        self.terminal = terminal

        self.step_size = self.derivative.integration_manager.step_size # Is this the best way to handle this?
        self.variables_to_report = variables_to_report + list(self.statevars.keys())
        self.results = pd.DataFrame(columns=["t"] + self.variables_to_report)

    def run(self):
        # Main loop
        if self.t == 0:
            self.derivative.call(arguments=self._get_initial_arguments())
            self._store_results(self.derivative.previous_section_scope)
            self.t += self.step_size
    
        while self.t <= self.TSTP:
            self.derivative.call(arguments=self._get_arguments())
            self._store_results(self.derivative.previous_section_scope)
            self.t += self.step_size
        
        return self._get_final_results()

    def _get_initial_arguments(self):
        initial_statevars = {
            key: self.constants[value] for key, value in self.statevars.items()
        }
        return {
            **self.constants,
            **initial_statevars
        }

    def _get_arguments(self):
        new_statevars = {
            key: self.derivative.previous_section_scope[1][value] for key, value in self.statevars.items()
        }
        for statevar, initial_value in self.statevars.items():
            new_statevars[initial_value] = self.derivative.previous_section_scope[1][statevar]
        return {
            **self.constants,
            **new_statevars
        }

    def _store_results(self, previous_section_scope: Dict):

        results = {
            var_name: previous_section_scope[1][var_name] for var_name in self.variables_to_report
        }
        self.results.loc[self.t] = [self.t] + list(results.values())

    def _get_final_results(self):
        """
        Extract results at communication interval (CINT) by finding the closest 
        time points in the results DataFrame.
        """
        cint_times = np.arange(0, self.TSTP + self.CINT, self.CINT)
        
        final_results = pd.DataFrame(columns=self.results.columns)
        
        for target_time in cint_times:
            if target_time > self.TSTP:
                break
                
            time_diffs = np.abs(self.results['t'] - target_time)
            closest_idx = time_diffs.idxmin()
            
            final_results.loc[len(final_results)] = self.results.loc[closest_idx]
        
        return final_results

import abc
import sys
from functools import wraps
import inspect
import re
from typing import List

import pandas as pd

class BaseMechanisticModel(abc.ABC):
    def __init__(self):
        self.intermediates = {}
        self.validate_model_method()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        original_init = cls.__init__

        def wrapped_init(self, *args, **kwargs):
            BaseMechanisticModel.__init__(self)
            original_init(self, *args, **kwargs)

        cls.__init__ = wrapped_init # Replace subclass __init__ with wrapped_init
        
    # def trace_func(self, frame, event, arg):
    #     """Tracing function to capture local variables at return from the model."""
    #     if event == "return" and frame.f_code.co_name == "model":
    #         self.intermediates = frame.f_locals.copy()
    #     return self.trace_func

    # def start_tracing(self):
    #     """Enable tracing for the model method."""
    #     sys.settrace(self.trace_func)

    # def stop_tracing(self):
    #     """Disable tracing."""
    #     sys.settrace(None)

    def save(self):
        """Store the local scope of the calling function."""
        current_frame = inspect.currentframe()        
        caller_frame = current_frame.f_back
        local_vars = caller_frame.f_locals
        self.intermediates = local_vars.copy()

    def validate_model_method(self):
        """Checks if `self.save()` is called in the `model` method and raises an error if commented out or missing."""
        save_called = False
        commented_out = False
       
        try:
            source_code = inspect.getsource(self.model)
        except TypeError:
            raise TypeError(
                "Model method is not defined or cannot retrieve source."
                )        
        lines = source_code.split('\n')
        pattern = re.compile(r'\bself\.save\(\)')
        for line in lines:
            if pattern.search(line):
                if line.strip().startswith('#'):
                    commented_out = True
                else:
                    save_called = True
                break

        if commented_out:
            raise ValueError(
                "The method `self.save()` is commented out in the `model` method."
                )
        if not save_called:
            raise ValueError(
                "The method `self.save()` is not called in the `model` method."
                )

    def __filter_intermediates(self):
        """Private method to filter captured locals based on outputs."""
        return {var: self.intermediates.get(var) for var in self.outputs if var in self.intermediates}

    @abc.abstractmethod
    def model(self, state_vars: list, t) -> List:
        """
        User-defined model function.

        This method must return a list of differentials corresponding to the state variables.

        Instructions for users:
        - You are expected to implement the mechanistic model dynamics inside this method.
        - Before the return statement, you must call `self.save()` to capture the intermediate variables.
        - The returned list must contain the differential equations representing the rate of change for each state variable.

        Args:
            state_vars (list): The list of current state variables.
            t (float): The current time point.

        Returns:
            list: A list of differentials representing the rate of change of the state variables.
        """
        pass

    def run_model(
        self, 
        equation: str, 
        t_span, 
        y0, 
        t_eval, 
        integ_interval, 
        prev_output=None
    ):

        if equation in []:
            pass # Run solve_ivp

        elif equation == "RK4":
            # self.start_tracing()
            results = self.runge_kutta_4th_order(
                t_span=t_span,
                y0=y0,
                t_eval=t_eval,
                integ_interval=integ_interval,
                prev_output=prev_output
            )
    
        # self.stop_tracing()
        return results

    def runge_kutta_4th_order(
        self, 
        t_span, 
        y0, 
        t_eval, 
        integ_interval, 
        prev_output = None
    ):
        """Main function that runs the Runge-Kutta algorithm."""
        
        def interval_generator():
            """Generator function to dynamically yield intervals."""
            start_time, stop_time = t_span
            run_time = stop_time - start_time
            last_interval_number = int(run_time / integ_interval)
            intervals_to_communicate = int(t_eval / integ_interval)
            
            # Set initial t
            if start_time == 0:
                t = 0.0
            elif start_time != 0:
                if not isinstance(prev_output, pd.DataFrame):
                    raise TypeError(
                        "The variable prev_output must be a dataframe if start_time != 0"
                        )
                t = prev_output["t"].iloc[-1]

            # Yield time intervals
            for interval_number in range(last_interval_number):
                remainder = (interval_number + 1) / intervals_to_communicate - int((interval_number + 1) / intervals_to_communicate)
                append_results = (remainder == 0) if t != 0.0 else True
                yield t, append_results
                t += integ_interval


        def runge_kutta_step(state_vars, t):
            """Runge-Kutta step that computes new state variables."""
            slopes = []  # To store the slopes for the RK4 method
            start = []  # Stores initial values for the RK4 integration
            
            half_interval = integ_interval / 2
            sixth_interval = integ_interval / 6

            for n in range(4):
                differential_return = self.model(state_vars=state_vars, t=t)                  
                slopes.append(differential_return)

                for svno in range(len(state_vars)):
                    if n == 0:
                        start.append(state_vars[svno])
                        newStateVar = start[svno] + half_interval * slopes[n][svno]
                    elif n == 1:
                        newStateVar = start[svno] + half_interval * slopes[n][svno]
                    elif n == 2:
                        newStateVar = start[svno] + integ_interval * slopes[n][svno]
                    else:
                        newStateVar = (start[svno] + sixth_interval *
                                    (slopes[0][svno] + 2 * slopes[1][svno] +
                                        2 * slopes[2][svno] + slopes[3][svno]))

                    state_vars[svno] = newStateVar

            return state_vars

        ### Main Function ###
        model_results = []
        state_vars = y0.copy()
        interval_gen = interval_generator()

        print("Running Model...")

        # Iterate over the generated intervals and apply the Runge-Kutta steps
        for t, append_result in interval_gen:
            state_vars = runge_kutta_step(state_vars, t)            
            if append_result:
                model_results.append(self.__filter_intermediates())
    
        return model_results
    
    # TODO Need to standardize the output from run model 
    # TODO Add methods to work with standardized output
     

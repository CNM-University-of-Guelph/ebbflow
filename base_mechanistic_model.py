import abc
import sys
from functools import wraps

import pandas as pd

class BaseMechanisticModel(abc.ABC):
    def __init__(self):
        self.intermediates = {}
   
    def trace_func(self, frame, event, arg):
        """Tracing function to capture local variables at return from the model."""
        if event == "return" and frame.f_code.co_name == "model":
            self.intermediates = frame.f_locals.copy()
        return self.trace_func

    def start_tracing(self):
        """Enable tracing for the model method."""
        sys.settrace(self.trace_func)

    def stop_tracing(self):
        """Disable tracing."""
        sys.settrace(None)

    def __filter_intermediates(self):
        """Private method to filter captured locals based on outputs."""
        return {var: self.intermediates.get(var) for var in self.outputs if var in self.intermediates}

    @abc.abstractmethod
    def model(self, state_vars, t):
        """User-defined model function. Must return only differentials."""
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
            self.start_tracing()
            results = self.runge_kutta_4th_order(
                t_span=t_span,
                y0=y0,
                t_eval=t_eval,
                integ_interval=integ_interval,
                prev_output=prev_output
            )
    
        self.stop_tracing()
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
     

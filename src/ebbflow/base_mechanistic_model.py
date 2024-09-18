import abc
import ast
import datetime
import inspect
import re
import textwrap
from typing import List, Type, Dict, Any, Tuple, Optional, Generator

import numpy as np
import pandas as pd
import scipy.integrate as integrate

class BaseMechanisticModel(abc.ABC):
    def __init__(self):
        self.current_intermediates = {}
        self.closest_time_point = {}
        self.model_results = {}
        self.result_count = 0
        self.constant_names = []
        self.__validate_model_method()

    def __init_subclass__(cls: Type["BaseMechanisticModel"], **kwargs) -> None:
        """
        Wraps the __init__ method of subclasses to ensure BaseMechanisticModel 
        is properly initialized and collects constant names.
        """
        super().__init_subclass__(**kwargs)
        original_init = cls.__init__

        def wrapped_init(self, *args, **kwargs):
            BaseMechanisticModel.__init__(self)
            init_signature = inspect.signature(original_init)
            self.constant_names = [
                param.name for param in init_signature.parameters.values()
                if param.name != "self"
            ]
            original_init(self, *args, **kwargs)

        cls.__init__ = wrapped_init # Replace subclass __init__ with wrapped_init
        
    @abc.abstractmethod
    def model(self, t: float, state_vars: List[float]) -> List[float]:
        """
        User-defined model function.

        This method must return a list of differentials corresponding to the state variables.

        Instructions for users:
        - You are expected to implement the mechanistic model dynamics inside this method.
        - Before the return statement, you must call `self.save()` to capture the intermediate variables.
        - The returned list must contain the differential equations representing the rate of change for each state variable.

        Args:
            t (float): The current time point.
            state_vars (list): The list of current state variables.

        Returns:
            list: A list of differentials representing the rate of change of the state variables.
        """
        pass

    # Private Methods
    def __validate_model_method(self) -> None:
        """Checks if `self.save()` is called in the `model` method."""
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

    def __filter_intermediates(self) -> Dict[str, Any]:
        """Filters captured locals based on outputs.

        This is used by runge_kutta_4th_order.

        Returns:
            dict: A dictionary of filtered intermediate values.
        """
        return {var: self.current_intermediates.get(var) for var in self.outputs 
                if var in self.current_intermediates}

    def __runge_kutta_4th_order(
        self, 
        t_span: Tuple[int, int], 
        y0: List[float], 
        t_eval: np.ndarray, 
        integ_interval: float, 
        prev_output: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, float]]:
        """
        Run the 4th-order Runge-Kutta algorithm.

        Args:
            t_span (tuple): A tuple (start_time, stop_time) defining the time span of the integration.
            y0 (list): Initial values of the state variables.
            t_eval (np.ndarray): Time points to evaluate the solution.
            integ_interval (float): The integration interval for Runge-Kutta.
            prev_output (pd.DataFrame, optional): A DataFrame containing previous output to resume the integration.

        Returns:
            list: The model results, including computed state variables at desired time points.
        """
        
        def interval_generator() -> Generator[tuple[float, bool], None, None]:
            """
            Generator function to dynamically yield time intervals and whether to append results.

            Yields:
                tuple[float, bool]: A tuple containing the current time (float) and a boolean indicating whether to append results.
            """
            start_time, stop_time = t_span
            run_time = stop_time - start_time
            last_interval_number = int(run_time / integ_interval)
            step_size = t_eval[1] - t_eval[0]
            intervals_to_communicate = int(step_size / integ_interval)
                        
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
                remainder = ((interval_number + 1) / intervals_to_communicate - 
                             int((interval_number + 1) / intervals_to_communicate))
                append_results = (remainder == 0) if t != 0.0 else True
                yield t, append_results
                t += integ_interval


        def runge_kutta_step(state_vars: List[float], t: float) -> List[float]:
            """
            Performs one step of the Runge-Kutta integration.

            Args:
                state_vars (list): Current values of the state variables.
                t (float): The current time.

            Returns:
                list: Updated state variables after the Runge-Kutta step.
            """
            slopes = []  # To store the slopes for the RK4 method
            start = []  # Stores initial values for the RK4 integration
            
            half_interval = integ_interval / 2
            sixth_interval = integ_interval / 6

            for n in range(4):
                differential_return = self.model(t=t, state_vars=state_vars)                  
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

    def __precompute_time_points(self) -> List[int]:
        """
        Precomputes the expected time points for saving data.

        Returns:
            list: A list of expected time points based on t_eval.
        """
        start_time, end_time = self.t_span
        expected_times = []
        t = start_time
        step_size = int(self.t_eval[1] - self.t_eval[0])
        while t <= end_time:
            expected_times.append(t)
            t += step_size
        return expected_times

    def __extract_return_names(self) -> List[str]:
        """
        Extracts variable names from the return statement of the model function.

        Returns:
            list: A list of variable names, with 'd' and 'dt' stripped from the names.
        """
        source = inspect.getsource(self.model)
        source = textwrap.dedent(source)
        tree = ast.parse(source)
        
        # Find the return statement and extract the names, strip d*dt from name
        for node in ast.walk(tree):
            if isinstance(node, ast.Return):
                if isinstance(node.value, ast.List):
                    return [
                        elt.id[1:-2] for elt in node.value.elts
                        if isinstance(elt, ast.Name)
                        ]
                elif isinstance(node.value, ast.Name):
                    return [node.value.id[1:-2]]
        return []

    # Public Methods
    def save(self) -> None:
        """Store the local scope of the calling function and handle time-point capture."""
        # Get local variables from self.model()
        current_frame = inspect.currentframe()        
        caller_frame = current_frame.f_back
        local_vars = caller_frame.f_locals
        for var in ["self", "state_vars"]:
            if var in local_vars:
                del local_vars[var]

        # Always keep the most recent time-point stored 
        self.current_intermediates = local_vars.copy()

        # Use t_eval and t_span to determine what time-points should be kept
        t = local_vars["t"]
        if not hasattr(self, "expected_times"):            
            self.current_expected_idx = 0
            self.closest_time_point = None
            self.expected_times = self.__precompute_time_points()
            # self.expected_times = list(self.t_eval)   
            # NOTE For some reason it is faster to call precompute_time_points 
            # than it is to use the t_eval array???

        final_index = len(self.expected_times) - 1

        # Determine if the current time-point should be saved
        if self.current_expected_idx < final_index:
            expected_t = self.expected_times[self.current_expected_idx]

            if self.closest_time_point is None:
                self.closest_time_point = local_vars.copy()

            if abs(t - expected_t) < abs(self.closest_time_point["t"] - expected_t):
                self.closest_time_point = local_vars.copy()

            if t > expected_t:
                self.saved_intermediates.append(self.closest_time_point)
                self.current_expected_idx += 1
                self.closest_time_point = None

        if self.current_expected_idx == final_index:
            if len(self.saved_intermediates) == final_index:
                self.saved_intermediates.append(local_vars.copy())
            else:
                self.saved_intermediates[-1] = local_vars.copy()

    def run_model(
        self, 
        equation: str, 
        t_span: Tuple[int, int], 
        y0: List[float], 
        t_eval: np.ndarray, 
        integ_interval: Optional[float] = None, 
        prev_output: Optional[pd.DataFrame] = None,
        name: Optional[str] = None
    ) -> None:
        """
        Run the model using the specified integration method.

        Args:
            equation (str): The solver to use ('RK4' or 'solve_ivp').
            t_span (tuple): The time span for the integration.
            y0 (list): Initial state variables.
            t_eval (np.ndarray): Time points at which to store the solution.
            integ_interval (float, optional): Integration interval for RK4. Defaults to None.
            prev_output (pd.DataFrame, optional): Previous model output for restarting integration. Defaults to None.
            name (str, optional): The name of the result. Defaults to None.
        """
        self.t_eval = t_eval
        self.t_span = t_span
        self.saved_intermediates = []   # Reset every model run
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if equation == "solve_ivp":
            solver_output = integrate.solve_ivp(
                self.model,
                t_span=t_span,
                y0=y0,
                t_eval=t_eval
            )

        elif equation == "RK4":
            solver_output = self.__runge_kutta_4th_order(
                t_span=t_span,
                y0=y0,
                t_eval=t_eval,
                integ_interval=integ_interval,
                prev_output=prev_output
            )

        else:
            raise ValueError("equation must be one of 'RK4' or 'solve_ivp'")
    
        if name is None:
            self.result_count += 1
            name = f"result_{self.result_count}"

        result_entry = {
            "name": name,
            "solver_output": solver_output,
            "intermediates": pd.DataFrame(self.saved_intermediates),
            "timestamp": timestamp,
            "solver_id": equation
        }
        self.model_results[name] = result_entry     

        # Delete self.expected_times after the run is complete
        if hasattr(self, 'expected_times'):
            del self.expected_times

    def to_dataframe(self, name: Optional[str] = None):
        """Exports the model results as a pandas DataFrame.

        Args:
            name (str, optional): The name of the result to export. If None, the most recent result is used. Defaults to None.

        Returns:
            pd.DataFrame: A DataFrame containing the results.
        """
        if name is None:
            last_key = list(self.model_results.keys())[-1]
            result = self.model_results[last_key]
        else:
            result = self.model_results[name]

        if result["solver_id"] == "RK4":
            return pd.DataFrame(result["solver_output"])
        elif result["solver_id"] == "solve_ivp":
            df = pd.DataFrame({
                "t": result["solver_output"].t
            })

            column_names = self.__extract_return_names()

            for i, col_name in enumerate(column_names):
                df[col_name] = result["solver_output"].y[i]
            return df
    
    def change_constants(self, new_constants: Dict[str, float]) -> None:
        """Change the values of constants defined in the subclass __init__."""
        for key, value in new_constants.items():
            if key in self.constant_names:
                setattr(self, key, value)
                print(f"{key} updated to {value}")
            else:
                raise ValueError(
                    f"{key} is not a valid constant. "
                    f"Valid constants are {self.constant_names}"
                )
        
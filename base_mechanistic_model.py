import abc

import pandas as pd

class BaseMechanisticModel():
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
            results = self.runge_kutta_4th_order(
                t_span=t_span,
                y0=y0,
                t_eval=t_eval,
                integ_interval=integ_interval,
                prev_output=prev_output
            )
            return results

# TODO deal with variable_returns
    def runge_kutta_4th_order(
        self, 
        t_span, 
        y0, 
        t_eval, 
        integ_interval, 
        prev_output = None
    ):
        """Main function that runs the refactored Runge-Kutta algorithm with a generator."""
        
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

            for n in range(4):
                differential_return, variable_returns = self.model(
                    state_vars=state_vars, t=t
                )
                slopes.append(differential_return)

                for svno in range(len(state_vars)):
                    match n:
                        case 0:
                            start.append(state_vars[svno])
                            newStateVar = start[svno] + integ_interval * slopes[n][svno] / 2
                        case 1:
                            newStateVar = start[svno] + integ_interval * slopes[n][svno] / 2
                        case 2:
                            newStateVar = start[svno] + integ_interval * slopes[n][svno]
                        case 3:
                            newStateVar = (start[svno] + integ_interval / 6 *
                                        (slopes[0][svno] + 2 * slopes[1][svno] +
                                            2 * slopes[2][svno] + slopes[3][svno]))

                    state_vars[svno] = newStateVar

            return state_vars, variable_returns

        ### Main Function ###
        model_results = []
        state_vars = y0.copy()
        interval_gen = interval_generator()

        print("Running Model...")

        # Iterate over the generated intervals and apply the Runge-Kutta steps
        for t, append_result in interval_gen:
            state_vars, variable_returns = runge_kutta_step(state_vars, t)            
            if append_result:
                model_results.append(variable_returns.copy())
    
        return model_results


    # TODO Need to standardize the output from run model 
    # TODO Add methods to work with standardized output
     
    @abc.abstractmethod
    def model(self):
        """User defined model function."""
        pass

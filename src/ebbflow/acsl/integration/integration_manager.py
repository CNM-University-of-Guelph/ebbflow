"""The IntegrationManager class is responsible for performing integration using the correct method"""

from typing import Dict, Callable, List

class IntegrationManager:
    """The IntegrationManager class is responsible for performing integration using the correct method
    
    1 = Adams-Moulton
    2 = Gear's stiff
    3 = Runge-Kutta (Euler)
    4 = Runge-Kutta (second order)
    5 = Runge-Kutta (fourth order)
    6 = none
    7 = user-supplied subroutine
    8 = Runge-Kutta-Fehlberg (second order)
    9 = Runge-Kutta-Fehlberg (fifth order)
    10 = Differential algebraic system solver
    """

    def __init__(
            self,
            IALG: int,
            MAXT: float,
            NSTP: int,
            CINT: int,
            derivative_functions: Dict[str, Callable]
        ):
        self.integ_methods = {
            1: self.adams_moulton,
            2: self.gear_stiff,
            3: self.runge_kutta_euler,
            4: self.runge_kutta_second_order,
            5: self.runge_kutta_fourth_order,
            6: None,
            7: self.user_supplied_subroutine,
            8: self.runge_kutta_fehlberg_second_order,
            9: self.runge_kutta_fehlberg_fifth_order,
            10: self.differential_algebraic_system_solver,
        }
        self.derivative_functions = derivative_functions
        self.IALG = IALG
        self.MAXT = MAXT
        self.NSTP = NSTP
        self.CINT = CINT
        if self.IALG not in self.integ_methods.keys():
            raise ValueError(f"IALG must be between 1 and 10, got {IALG}")
        self.step_size = self.set_step_size()
        # if self.IALG in [3, 4, 5]: # fixed step size algorithms

    def set_step_size(self):
        h = min(self.MAXT, self.CINT / self.NSTP)
        # h = min(h, time_to_next_step) # NOTE don't understand how time_to_next_step is calculated
        return h

    def _get_kwargs(self, arg_names: List[str], state_var: str, time_state: Dict):
        kwargs = {}
        kwargs[state_var] = time_state[state_var]
        for arg_name in arg_names:
            if arg_name == state_var:
                continue
            kwargs[arg_name] = time_state[arg_name]
        return kwargs

    def integrate(self, deriv_name: str, ic: float, time_state: Dict):
        return self.integ_methods[self.IALG](deriv_name, ic, time_state)

    def adams_moulton(self):
        raise NotImplementedError("Adams-Moulton integration is not implemented")

    def gear_stiff(self):
        raise NotImplementedError("Gear's stiff integration is not implemented")

    def runge_kutta_euler(self):
        raise NotImplementedError("Runge-Kutta (Euler) integration is not implemented")

    def runge_kutta_second_order(self):
        raise NotImplementedError("Runge-Kutta (second order) integration is not implemented")

    def runge_kutta_fourth_order(self, deriv_name: str, ic: float, time_state: Dict):
        deriv_function, arg_names = self.derivative_functions[deriv_name]
        state_var = arg_names[-1]
        
        kwargs = self._get_kwargs(arg_names, state_var, time_state)
        kwargs[state_var] = ic
        k1 = deriv_function(**kwargs)

        kwargs[state_var] = ic + (self.step_size * k1) / 2
        k2 = deriv_function(**kwargs)

        kwargs[state_var] = ic + self.step_size * k2
        k3 = deriv_function(**kwargs)

        kwargs[state_var] = ic + self.step_size * k3
        k4 = deriv_function(**kwargs)

        return ic + (self.step_size / 6) * (k1 + 2 * k2 + 2 * k3 + k4)

    def user_supplied_subroutine(self):
        raise NotImplementedError("User-supplied subroutine integration is not implemented")

    def runge_kutta_fehlberg_second_order(self):
        raise NotImplementedError("Runge-Kutta-Fehlberg (second order) integration is not implemented")

    def runge_kutta_fehlberg_fifth_order(self):
        raise NotImplementedError("Runge-Kutta-Fehlberg (fifth order) integration is not implemented")

    def differential_algebraic_system_solver(self):
        raise NotImplementedError("Differential algebraic system solver integration is not implemented")

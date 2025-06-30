"""Implement the Acsl integration routine."""

from typing import Dict, Callable, List

class IntegrationManager:
    """Perform integration using the correct method.

    The integration methods are:
        - 1 = Adams-Moulton
        - 2 = Gear's stiff
        - 3 = Runge-Kutta (Euler)
        - 4 = Runge-Kutta (second order)
        - 5 = Runge-Kutta (fourth order)
        - 6 = none
        - 7 = user-supplied subroutine
        - 8 = Runge-Kutta-Fehlberg (second order)
        - 9 = Runge-Kutta-Fehlberg (fifth order)
        - 10 = Differential algebraic system solver

    Parameters
    ----------
    IALG : int
        The integration method to use.
    MAXT : float
        The maximum step size.
    NSTP : int
        The number of steps to take.
    CINT : int
        The communication interval.
    derivative_functions : dict[str, Callable]
        A dictionary mapping derivative function names to their functions.

    Attributes
    ----------
    integ_methods : dict[int, Callable]
        A dictionary mapping integration method numbers to their functions.
    derivative_functions : dict[str, Callable]
        A dictionary mapping derivative function names to their functions.
    IALG : int
        The integration method to use.
    MAXT : float
        The maximum step size.
    NSTP : int
        The number of steps to take.
    CINT : int
        The communication interval.
    step_size : float
        The step size for fixed step size algorithms.

    Raises
    ------
    ValueError
        If IALG is not between 1 and 10.
    """
    def __init__(
        self,
        IALG: int, # pylint: disable=invalid-name
        MAXT: float, # pylint: disable=invalid-name
        NSTP: int, # pylint: disable=invalid-name
        CINT: int, # pylint: disable=invalid-name
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
        self.IALG = IALG # pylint: disable=invalid-name
        self.MAXT = MAXT # pylint: disable=invalid-name
        self.NSTP = NSTP # pylint: disable=invalid-name
        self.CINT = CINT # pylint: disable=invalid-name
        if self.IALG not in self.integ_methods:
            raise ValueError(f"IALG must be between 1 and 10, got {IALG}")
        self.step_size = self.set_step_size()
        # if self.IALG in [3, 4, 5]: # fixed step size algorithms

    def set_step_size(self) -> float:
        """Set the step size for the integration.

        Returns
        -------
        float
            The step size.
        """
        h = min(self.MAXT, self.CINT / self.NSTP)
        # h = min(h, time_to_next_step)
        # NOTE: don't understand how time_to_next_step is calculated
        return h

    def _get_kwargs(
        self,
        arg_names: List[str],
        state_var: str,
        time_state: Dict
    ) -> Dict[str, float]:
        """Get the keyword arguments for the integration.

        Parameters
        ----------
        arg_names : list[str]
            The names of the arguments to the derivative function.
        state_var : str
            The name of the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        dict[str, float]
            The keyword arguments for the integration using values from the
            previous time step.
        """
        kwargs = {}
        kwargs[state_var] = time_state[state_var]
        for arg_name in arg_names:
            if arg_name == state_var:
                continue
            kwargs[arg_name] = time_state[arg_name]
        return kwargs

    def integrate(self, deriv_name: str, ic: float, time_state: Dict) -> float:
        """Call the selected integration method.

        Parameters
        ----------
        deriv_name : str
            The name of the derivative function.
        ic : float
            The initial condition for the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        float
            The value of the state variable at the next time step.
        """
        return self.integ_methods[self.IALG](deriv_name, ic, time_state)

    def adams_moulton(
        self,
        deriv_name: str,
        ic: float,
        time_state: Dict
    ) -> float:
        """Perform Adams-Moulton integration.

        Parameters
        ----------
        deriv_name : str
            The name of the derivative function.
        ic : float
            The initial condition for the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        float
            The value of the state variable at the next time step.

        Raises
        ------
        NotImplementedError
            Adams-Moulton integration is not implemented.
        """
        raise NotImplementedError(
            "Adams-Moulton integration is not implemented"
        )

    def gear_stiff(self, deriv_name: str, ic: float, time_state: Dict) -> float:
        """Perform Gear's stiff integration.

        Parameters
        ----------
        deriv_name : str
            The name of the derivative function.
        ic : float
            The initial condition for the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        float
            The value of the state variable at the next time step.

        Raises
        ------
        NotImplementedError
            Gear's stiff integration is not implemented.
        """
        raise NotImplementedError("Gear's stiff integration is not implemented")

    def runge_kutta_euler(
        self,
        deriv_name: str,
        ic: float,
        time_state: Dict
    ) -> float:
        """Perform Runge-Kutta (Euler) integration.

        Parameters
        ----------
        deriv_name : str
            The name of the derivative function.
        ic : float
            The initial condition for the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        float
            The value of the state variable at the next time step.

        Raises
        ------
        NotImplementedError
            Runge-Kutta (Euler) integration is not implemented.
        """
        raise NotImplementedError(
            "Runge-Kutta (Euler) integration is not implemented"
        )

    def runge_kutta_second_order(
        self,
        deriv_name: str,
        ic: float,
        time_state: Dict
    ) -> float:
        """Perform Runge-Kutta (second order) integration.

        Parameters
        ----------
        deriv_name : str
            The name of the derivative function.
        ic : float
            The initial condition for the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        float
            The value of the state variable at the next time step.

        Raises
        ------
        NotImplementedError
            Runge-Kutta (second order) integration is not implemented.
        """
        raise NotImplementedError(
            "Runge-Kutta (second order) integration is not implemented"
        )

    def runge_kutta_fourth_order(
        self,
        deriv_name: str,
        ic: float,
        time_state: Dict
    ) -> float:
        """Perform Runge-Kutta (fourth order) integration.

        Parameters
        ----------
        deriv_name : str
            The name of the derivative function.
        ic : float
            The initial condition for the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        float
            The value of the state variable at the next time step.
        """
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

    def user_supplied_subroutine(
        self,
        deriv_name: str,
        ic: float,
        time_state: Dict
    ) -> float:
        """Perform user-supplied subroutine integration.

        Parameters
        ----------
        deriv_name : str
            The name of the derivative function.
        ic : float
            The initial condition for the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        float
            The value of the state variable at the next time step.

        Raises
        ------
        NotImplementedError
            User-supplied subroutine integration is not implemented.
        """
        raise NotImplementedError(
            "User-supplied subroutine integration is not implemented"
        )

    def runge_kutta_fehlberg_second_order(
        self,
        deriv_name: str,
        ic: float,
        time_state: Dict
    ) -> float:
        """Perform Runge-Kutta-Fehlberg (second order) integration.

        Parameters
        ----------
        deriv_name : str
            The name of the derivative function.
        ic : float
            The initial condition for the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        float
            The value of the state variable at the next time step.

        Raises
        ------
        NotImplementedError
            Runge-Kutta-Fehlberg (second order) integration is not implemented.
        """
        raise NotImplementedError(
            "Runge-Kutta-Fehlberg (second order) integration is not implemented"
        )

    def runge_kutta_fehlberg_fifth_order(
        self,
        deriv_name: str,
        ic: float,
        time_state: Dict
    ) -> float:
        """Perform Runge-Kutta-Fehlberg (fifth order) integration.

        Parameters
        ----------
        deriv_name : str
            The name of the derivative function.
        ic : float
            The initial condition for the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        float
            The value of the state variable at the next time step.

        Raises
        ------
        NotImplementedError
            Runge-Kutta-Fehlberg (fifth order) integration is not implemented.
        """
        raise NotImplementedError(
            "Runge-Kutta-Fehlberg (fifth order) integration is not implemented"
        )

    def differential_algebraic_system_solver(
        self,
        deriv_name: str,
        ic: float,
        time_state: Dict
    ) -> float:
        """Perform differential algebraic system solver integration.

        Parameters
        ----------
        deriv_name : str
            The name of the derivative function.
        ic : float
            The initial condition for the state variable.
        time_state : dict[str, float]
            The values of the variables at the previous time step.

        Returns
        -------
        float
            The value of the state variable at the next time step.

        Raises
        ------
        NotImplementedError
            Differential algebraic system solver is not implemented.
        """

        raise NotImplementedError(
            "Differential algebraic system solver is not implemented"
            )

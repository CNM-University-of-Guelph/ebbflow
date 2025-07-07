"""AcslLib is the base class for all ACSL models providing the Acsl statements.
"""
import inspect
from typing import Union

from ebbflow.acsl.integration.integration_manager import IntegrationManager

class AcslLib:
    """A library of methods that can be called within an ACSL model.
    
    All Acsl statements are defined in this class. This class is inherited by
    the Acsl class to provide type hints for the Acsl statements. When an Acsl
    model is run the AcslRun class will inherit from this class and provide the
    integration manager.

    Parameters
    ----------
    integration_manager : IntegrationManager, optional
        The integration manager to use. AcslBuild will provide the integration
        manager to the AcslRun class. When used in the Acsl class, the 
        integration manager is not provided.

    Attributes
    ----------
    previous_section_scope : tuple
        The previous section scope. This is used to store the previous section
        scope.
    section_name : str
        The name of the section.
    integration_manager : IntegrationManager
        The integration manager to use when self.integ() is called.
    IALG : int
        The integration algorithm to use. 5 (4th order Runge-Kutta) by default.
    """
    def __init__(
            self,
            integration_manager: IntegrationManager = None
        ):
        self.previous_section_scope = ()
        self.section_name = "AcslLib"
        self.integration_manager = integration_manager
        self.IALG = integration_manager.IALG if integration_manager else 5 # pylint: disable=C0103

    def constant(self, name: str, value: Union[int, float, bool, list]):
        """
        Define a constant. Constants are available to all sections.

        Parameters
        ----------
        name : str
            The name of the constant.
        value : int, float, bool, list
            The value of the constant.

        Raises
        ------
        ValueError
            If the name is not a string or the value is not an int, float, bool,
            or list.
        """
        if not isinstance(name, str):
            raise ValueError(
                f"Constant name must be a string, got {type(name).__name__}"
            )
        if not isinstance(value, (int, float, bool, list)):
            raise ValueError(
                f"Constant value must be an int, float, bool, or list, "
                f"got {type(value).__name__}"
            )

    def delay(self, x, ic, tdl, nmx, delmin):
        """Placeholder for the delay function. Currently returns the input x.
        """
        # NOTE: Placeholder for delay function
        return x

    def end(self):
        """
        Capture the local scope of the calling function.

        This is required at the end of each section method so the local scope
        can be captured and stored for the next section to use.
        """
        frame = inspect.currentframe().f_back
        try:
            local_vars = frame.f_locals.copy()
            filtered_vars = {
                name: value for name, value in local_vars.items()
                if not name.startswith("_") and
                not callable(value) and
                name != "self"
            }
            section_name = getattr(self, "_current_section", "unknown")
            self.previous_section_scope = (section_name, filtered_vars)
        finally:
            del frame

    def integ(self, deriv: float | int, ic: float | int):
        """
        Integrate a state variable over a time step.

        Parameters
        ----------
        deriv : float | int
            The value of the derivative to integrate.
        ic : float | int
            The initial value of the state variable.

        Returns
        -------
        float
            The value of the state variable after integration.
        """
        # Find the name of the deriv variable in the local scope
        frame = inspect.currentframe().f_back
        try:
            deriv_name = None
            for var_name, var_value in frame.f_locals.items():
                if var_value is deriv:
                    deriv_name = var_name
                    break
            if deriv_name is None:
                raise ValueError(f"Derivative {deriv} not found in local scope")

            # Get values of constants and statevars at the start of the section
            local_vars = frame.f_locals.copy()
            time_state = {
                name: value for name, value in local_vars.items()
                if not name.startswith("_") and
                not callable(value) and
                name != "self"
            }
            return self.integration_manager.integrate(
                deriv_name, ic, time_state
            )

        finally:
            del frame

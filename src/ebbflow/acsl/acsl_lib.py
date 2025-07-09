"""AcslLib is the base class for all ACSL models providing the Acsl statements.
"""
import inspect
from typing import Union

from ebbflow.acsl.integration.integration_manager import IntegrationManager
from ebbflow.acsl.acsl_lib_helpers.delay_buffer import DelayBuffer

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
        self._delay_buffers = {}

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

    def delay(self, x, ic, tdl, nmx, delmin, delay_id=None):
        """Delay a variable in time to model the effect of transport.

        Parameters
        ----------
        x : float | int
            The value of the variable to delay.
        ic : float | int
            The initial value of the variable until the variable has advanced by
            the delay.
        tdl : float | int
            The delay time from input to output. Greater than 0.
        nmx : int
            The maximum number of data points to represent the delay.
        delmin : float | int
            The minimum interval between saving of data points in delay buffer.
        id : str
            The unique identifier for the delay buffer.

        Returns
        -------
        float | int
            The value of the variable after the delay.
        """
        if tdl <= 0:
            raise ValueError("Delay time (tdl) must be greater than 0")
        if nmx < 1:
            raise ValueError("Maximum data points (nmx) must be at least 1")
        if delmin <= 0:
            raise ValueError("Minimum interval (delmin) must be greater than 0")
        if delay_id is None:
            raise ValueError("Delay buffer identifier (id) must be provided")

        if delay_id not in self._delay_buffers:
            buffer_info = {
                "buffer": DelayBuffer(nmx, ic, getattr(self, "t", 0.0)),
                "last_updated_time": float("-inf") # Force first update
            }
            self._delay_buffers[delay_id] = buffer_info
        else:
            buffer_info = self._delay_buffers[delay_id]

        current_time = getattr(self, 't', 0.0)
        time_since_last = current_time - buffer_info["last_updated_time"]
        min_interval = max(delmin, self.step_size)

        if time_since_last >= min_interval:
            buffer_info["buffer"].add(current_time, x)
            buffer_info["last_update_time"] = current_time

        delayed_value = buffer_info["buffer"].get_delayed_value(current_time, tdl)
        return delayed_value
 
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

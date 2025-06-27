"""The ACSL library is a collection of methods that can be called within an ACSL model.
"""
import inspect
from typing import Union

from ebbflow.acsl.integration.integration_manager import IntegrationManager

class AcslLib:
    """A library of methods that can be called within an ACSL model.
    
    This class is used to define an ACSL model. It provides all the methods that
    can be called within an ACSL model. It will check the defined model is valid
    when initialized. The run() method can be used to translate and run the model.
    """
    def __init__(
            self,
            integration_manager: IntegrationManager = None
        ):
        self.previous_section_scope = ()
        self.section_name = "AcslLib"
        self.integration_manager = integration_manager
        self.IALG = integration_manager.IALG if integration_manager else 5

    def constant(self, name: str, value: Union[int, float, bool, list]):
        if not isinstance(name, str):
            raise ValueError(
                f"Constant name must be a string, got {type(name).__name__}"
            )
        if not isinstance(value, (int, float, bool, list)):
            raise ValueError(
                f"Constant value must be an int, float, bool, or list, got {type(value).__name__}"
            )

    def delay(self, x, ic, tdl, nmx, delmin):
        # NOTE: Placeholder for delay function
        return x

    def end(self):
        """
        Capture the local scope of the calling section. 

        This is required at the end of each section method.
        """
        frame = inspect.currentframe().f_back
        try:
            local_vars = frame.f_locals.copy()
            filtered_vars = {
                name: value for name, value in local_vars.items()
                if not name.startswith('_') and
                not callable(value) and
                name != "self"
            }
            section_name = getattr(self, '_current_section', 'unknown')
            self.previous_section_scope = (section_name, filtered_vars)
        finally:
            del frame

    def integ(self, deriv, ic):
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
                if not name.startswith('_') and
                not callable(value) and
                name != "self"
            }
            return self.integration_manager.integrate(deriv_name, ic, time_state)

        finally:
            del frame

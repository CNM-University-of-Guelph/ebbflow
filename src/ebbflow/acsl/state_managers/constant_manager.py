import inspect
from typing import Callable

class ConstantManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConstantManager, cls).__new__(cls)
            cls._instance.constants = {}
            cls._instance.collecting_constants = False
            cls._instance.valid_types = (int, float, bool)
        return cls._instance
    
    def set_constant(self, name, value):
        if self.collecting_constants:
            if not isinstance(name, str):
                raise TypeError(
                    f"Constant name must be a string, got {type(name).__name__}"
                )
            elif not isinstance(value, self.valid_types):
                raise TypeError(
                    f"{name} has invalid type {type(value)}. Valid types are int, float, and bool"
                )
            elif name in self.constants.keys():
                raise ValueError(f"Constant {name} is already defined")
            
            self.constants[name] = value
        
        else:
            print(f"DEBUG: Ignoring attempt to set constant '{name}' outside of collection phase")

    def collect_initial_constants(self, initial_scope: tuple):
        """
        Collect constants that are defined in the initial section.
        """
        variables = initial_scope[1]
        for captured_name in self.constants.keys():
            variables.pop(captured_name, None)

        for name, value in variables.items():
            self.set_constant(name, value)
            # print(f"DEBUG: Auto-collected constant from INITIAL: {name} = {value}")

    def get_constant(self, name):
        if name not in self.constants:
            raise KeyError(f"Constant '{name}' not found.")
        return self.constants[name]
    
    def _set_collection_mode(self, mode: bool):
        if not isinstance(mode, bool):
            raise ValueError(
                f"Mode must be a boolean, got {type(mode).__name__}"
            )
        self.collecting_constants = mode

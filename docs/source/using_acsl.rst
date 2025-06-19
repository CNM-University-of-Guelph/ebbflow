Using ACSL
===========

Rules for INITIAL section
-------------------------

- using `self.set_constant()` to set constants is optional
- all variables in the INITIAL section are automatically collected as constants
- this is the only section where constants can be set dynamically
- `self.set_constant()` enforces that constants are set to valid types (int, float, bool)
- multiple assignments in a single line are not allowed
- INTEG can only be used in sorted section, therefore only check for state variables in sorted sections
- All configuration values are expected to be in the DYNAMIC section
- Arguments provided to run() will overide configuration values set as constants
    - Ex. CINT
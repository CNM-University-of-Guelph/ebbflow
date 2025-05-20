Using ACSL
===========

Rules for INITIAL section
-------------------------

- using `self.set_constant()` to set constants is optional
- all variables in the INITIAL section are automatically collected as constants
- this is the only section where constants can be set dynamically
- `self.set_constant()` enforces that constants are set to valid types (int, float, bool)

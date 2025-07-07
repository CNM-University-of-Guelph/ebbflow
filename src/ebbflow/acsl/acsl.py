"""Acsl is the base class for all ACSL models. It provides the methods to 
validate the model structure, trigger the build process and run the model.
"""
import ast
import inspect
import textwrap
from typing import Optional, List

from ebbflow.acsl.acsl_lib import AcslLib
from ebbflow.acsl.build.acsl_build import AcslBuild

class Acsl(AcslLib):
    """Subclass of AcslLib that initiates the build process with run().

    When defining a new ACSL model, this class must be inherited to provide
    the Acsl statements. The run() method will trigger the build process and
    then run the model.
    """
    def __init__(self):
        super().__init__()
        self.section_mapping = {}
        self._validate_sections()
        self._create_section_mapping()

    def _validate_sections(self):
        """Check the user-defined model has a valid structure.

        Checks there are no duplicate sections. If a DERIVATIVE or DISCRETE
        section is found, the model must also contain a DYNAMIC section.
        
        Raises
        ------
        ValueError
            If the model has duplicate sections or if a DERIVATIVE or DISCRETE
            section is found without a DYNAMIC section.
        """
        found_sections = set()
        for _, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "acsl_section"):
                section_type = method.acsl_section

                if section_type in found_sections:
                    raise ValueError(f"Duplicate section: {section_type}")
                found_sections.add(section_type)

        has_dynamic = "DYNAMIC" in found_sections
        has_derivative = "DERIVATIVE" in found_sections
        has_discrete = "DISCRETE" in found_sections

        if (has_derivative or has_discrete) and not has_dynamic:
            if has_derivative:
                raise ValueError("DERIVATIVE section requires DYNAMIC section")
            else:
                raise ValueError("DISCRETE section requires DYNAMIC section")

    def _create_section_mapping(self):
        """Map the user-defined functions to their corresponding section names.

        This is done by checking for the presence of the acsl_section attribute
        on the user-defined functions. This attribute is set by using the
        the section decorators.
        """
        for _, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "acsl_section"):
                self.section_mapping[method.acsl_section] = method

    def run(
        self,
        TSTP: float | int, # pylint: disable=invalid-name
        CINT: Optional[float | int] = None, # pylint: disable=invalid-name
        report: Optional[List[str]] = None,
    ):
        """Build and run the ACSL model.

        Parameters
        ----------
        TSTP : float | int
            The stop time.
        CINT : float | int, optional
            The communication interval used for reporting. This is also used
            to determine the integration step size.
        report : list, optional
            A list of variable names to include in the ouput.

        Returns
        -------
        results : DataFrame
            A pandas DataFrame containing the results of the model run.
        """
        if report is None:
            report = []

        def _collect_metadata(section_method: str):
            """Collect the metadata for the section.

            This is done by checking for the presence of the acsl_section,
            collect_constants, collect_statevars and sort attributes set by
            the section decorators.
            """
            metadata = {
                "acsl_section": getattr(
                    section_method, "acsl_section", None
                ),
                "collect_constants": getattr(
                    section_method, "collect_constants", False
                ),
                "collect_statevars": getattr(
                    section_method, "collect_statevars", False
                ),
                "sort": getattr(section_method, "sort", False),
            }
            return metadata


        initial_scope = (None, {})
        section_trees = {}

        # Collect metadata and AST tree for each section
        for section_name, section_method in self.section_mapping.items():
            metadata = _collect_metadata(section_method)
            source = inspect.getsource(section_method)
            source_dedent = textwrap.dedent(source)
            tree = ast.parse(source_dedent)
            section_trees[section_name] = (tree, metadata)

        # Collect constants defined without self.constant in INITIAL section
        if "INITIAL" in self.section_mapping:
            self.section_mapping["INITIAL"]()
            initial_scope = self.previous_section_scope

        acsl_build = AcslBuild(section_trees, initial_scope, TSTP, CINT, report)
        acsl_run = acsl_build.build()
        results = acsl_run.run()
        return results

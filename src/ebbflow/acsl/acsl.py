"""Subclass of AcslLib that initiates the build process with by overriding the run() method"""
import ast
import inspect
import textwrap

from ebbflow.acsl.acsl_lib import AcslLib
from ebbflow.acsl.build.acsl_build import AcslBuild

class Acsl(AcslLib):
    """Subclass of AcslLib that initiates the build process with by overriding the run() method"""
    def __init__(self):
        super().__init__()
        self.section_mapping = {}
        self._validate_sections()
        self._create_section_mapping()

    def _validate_sections(self):
        """
        Validate:
        1. Each section appears at most once
        2. DERIVATIVE and DISCRETE sections require a DYNAMIC section
        """
        found_sections = set()
        for _, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "_acsl_section"):
                section_type = method._acsl_section

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
        """
        Create a mapping of section names to their corresponding functions.
        This allows for easy access to section methods by name.
        """        
        for _, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "_acsl_section"):
                self.section_mapping[method._acsl_section] = method

    def run(self, TSTP, CINT=None):
        def _collect_metadata(section_method):
            metadata = {
                '_acsl_section': getattr(
                    section_method, '_acsl_section', None
                ),
                '_collect_constants': getattr(
                    section_method, '_collect_constants', False
                ),
                '_collect_statevars': getattr(
                    section_method, '_collect_statevars', False
                ),
                '_sort': getattr(section_method, '_sort', False),
            }
            return metadata
        initial_scope = (None, {})
        section_trees = {}

        for section_name, section_method in self.section_mapping.items():
            metadata = _collect_metadata(section_method)
            source = inspect.getsource(section_method)
            source_dedent = textwrap.dedent(source)
            tree = ast.parse(source_dedent)
            section_trees[section_name] = (tree, metadata)

        if "INITIAL" in self.section_mapping:
            self.section_mapping["INITIAL"]()
            initial_scope = self.previous_section_scope

        acsl_build = AcslBuild(section_trees, initial_scope, TSTP, CINT)
        acsl_run = acsl_build.build()
        return acsl_build, acsl_run # NOTE: for debugging
        # 4. Take output of AcslBuild.build() (AcslRun instance) and exercise it
        # 5. Return the output to the user

"""Analisis matricial de armaduras planas en 2D."""

from analisis_armadura.data import create_default_model
from analisis_armadura.diagnostics import (
    ModelDofCounts,
    StructuralDiagnostics,
    StructuralDiagnosticWarning,
    diagnose_model,
)
from analisis_armadura.interactive import (
    build_scaled_default_model,
    build_triangular_roof_truss,
    build_warren_truss,
    run_interactive,
)
from analisis_armadura.models import (
    Direction,
    Element,
    NodalLoad,
    Node,
    PrescribedDisplacement,
    SupportType,
    TrussModel,
)
from analisis_armadura.presentation import (
    DISPLACEMENT_UNIT,
    FORCE_UNIT,
    format_detailed_report,
    format_diagnostics_report,
    format_displacements,
    format_executive_summary,
    format_internal_forces,
    format_reactions,
)
from analisis_armadura.solver import (
    AnalysisResult,
    MatrixTrussAnalyzer,
    TrussAnalysisError,
    TrussValidationError,
)

__all__ = [
    "AnalysisResult",
    "DISPLACEMENT_UNIT",
    "build_scaled_default_model",
    "build_triangular_roof_truss",
    "build_warren_truss",
    "Direction",
    "Element",
    "FORCE_UNIT",
    "MatrixTrussAnalyzer",
    "ModelDofCounts",
    "NodalLoad",
    "Node",
    "PrescribedDisplacement",
    "StructuralDiagnostics",
    "StructuralDiagnosticWarning",
    "SupportType",
    "TrussAnalysisError",
    "TrussModel",
    "TrussValidationError",
    "create_default_model",
    "format_detailed_report",
    "format_diagnostics_report",
    "format_displacements",
    "format_executive_summary",
    "format_internal_forces",
    "format_reactions",
    "diagnose_model",
    "run_interactive",
]

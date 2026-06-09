"""Formato estandarizado para presentar resultados estructurales."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analisis_armadura.diagnostics import StructuralDiagnostics
    from analisis_armadura.solver import AnalysisResult, DegreeOfFreedom

DISPLACEMENT_UNIT = "cm"
DISPLACEMENT_TO_DISPLAY_FACTOR = 100.0
FORCE_UNIT = "kgf"


@dataclass(frozen=True)
class ExecutiveSummary:
    """Resumen ejecutivo del analisis para salida de consola."""

    node_count: int
    element_count: int
    maximum_displacement_cm: float
    reaction_count: int


def displacement_to_centimeters(displacement_m: float) -> float:
    """Convierte desplazamientos internos en metros a centimetros."""
    return displacement_m * DISPLACEMENT_TO_DISPLAY_FACTOR


def build_executive_summary(result: AnalysisResult) -> ExecutiveSummary:
    """Construye metricas breves para presentar el resultado del analisis."""
    node_count = len({node_name for node_name, _ in result.dof_order})
    maximum_displacement_cm = max(
        (
            abs(displacement_to_centimeters(float(value)))
            for value in result.global_displacements
        ),
        default=0.0,
    )
    return ExecutiveSummary(
        node_count=node_count,
        element_count=len(result.member_names),
        maximum_displacement_cm=maximum_displacement_cm,
        reaction_count=len(result.reactions),
    )


def format_executive_summary(summary: ExecutiveSummary) -> str:
    """Formatea el resumen ejecutivo para terminal."""
    return "\n".join(
        (
            "Analisis completado correctamente",
            f"Numero de nodos: {summary.node_count}",
            f"Numero de elementos: {summary.element_count}",
            f"Desplazamiento maximo: {summary.maximum_displacement_cm:.3f} "
            f"{DISPLACEMENT_UNIT}",
            f"Numero de reacciones calculadas: {summary.reaction_count}",
        )
    )


def format_displacements(result: AnalysisResult) -> str:
    """Formatea todos los desplazamientos globales en centimetros."""
    lines = ["Desplazamientos [cm]:"]
    lines.extend(
        f"D{index} = {displacement_to_centimeters(float(value)):.3f} "
        f"{DISPLACEMENT_UNIT}"
        for index, value in enumerate(result.global_displacements, start=1)
    )
    return "\n".join(lines)


def format_reactions(result: AnalysisResult) -> str:
    """Formatea reacciones con grado de libertad y unidad interna."""
    lines = [f"Reacciones [{FORCE_UNIT}]:"]
    lines.extend(
        f"{_format_dof(dof)} = {float(value):.2f} {FORCE_UNIT}"
        for dof, value in zip(result.constrained_dofs, result.reactions, strict=True)
    )
    return "\n".join(lines)


def format_internal_forces(result: AnalysisResult) -> str:
    """Formatea fuerzas internas por elemento con sentido axial."""
    lines = [f"Fuerzas internas de elementos [{FORCE_UNIT}]:"]
    lines.extend(
        f"{name} ({_force_state(float(value))}) = {float(value):.2f} {FORCE_UNIT}"
        for name, value in zip(result.member_names, result.internal_forces, strict=True)
    )
    return "\n".join(lines)


def format_detailed_report(result: AnalysisResult) -> str:
    """Genera un reporte compacto sin matrices ni arrays crudos."""
    return "\n\n".join(
        (
            format_executive_summary(build_executive_summary(result)),
            format_displacements(result),
            format_reactions(result),
            format_internal_forces(result),
        )
    )


def format_diagnostics_report(diagnostics: StructuralDiagnostics) -> str:
    """Formatea diagnosticos estructurales previos al analisis."""
    counts = diagnostics.counts
    lines = [
        "Diagnostico estructural previo:",
        f"Nodos: {counts.node_count}",
        f"Elementos: {counts.element_count}",
        f"Grados de libertad totales: {counts.total_dof_count}",
        f"Grados de libertad libres: {counts.free_dof_count}",
        f"Grados de libertad restringidos: {counts.constrained_dof_count}",
    ]

    if diagnostics.has_warnings:
        lines.append("Advertencias:")
        lines.extend(
            f"- [{warning.code}] {warning.message}" for warning in diagnostics.warnings
        )
    else:
        lines.append("Advertencias: no se detectaron problemas previos.")

    return "\n".join(lines)


def _format_dof(dof: DegreeOfFreedom) -> str:
    """Formatea un grado de libertad como ``Nodo Direccion``."""
    node, direction = dof
    return f"{node} {direction.value}"


def _force_state(value: float) -> str:
    """Clasifica una fuerza axial como tension, compresion o neutra."""
    if value > 0.0:
        return "Tension"
    if value < 0.0:
        return "Compresion"
    return "Neutro"

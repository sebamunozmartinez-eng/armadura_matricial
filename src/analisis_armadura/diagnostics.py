"""Diagnosticos estructurales previos al analisis matricial."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

import numpy as np

from analisis_armadura.models import Direction, TrussModel


@dataclass(frozen=True)
class ModelDofCounts:
    """Conteos basicos del modelo y sus grados de libertad."""

    node_count: int
    element_count: int
    total_dof_count: int
    free_dof_count: int
    constrained_dof_count: int


@dataclass(frozen=True)
class StructuralDiagnosticWarning:
    """Advertencia detectada antes de resolver el sistema."""

    code: str
    message: str


@dataclass(frozen=True)
class StructuralDiagnostics:
    """Resultado de diagnosticos estructurales previos al analisis."""

    counts: ModelDofCounts
    warnings: tuple[StructuralDiagnosticWarning, ...]

    @property
    def has_warnings(self) -> bool:
        """Indica si el diagnostico encontro advertencias."""
        return bool(self.warnings)

    def warning_messages(self) -> tuple[str, ...]:
        """Devuelve solo los mensajes de advertencia."""
        return tuple(warning.message for warning in self.warnings)


def diagnose_model(model: TrussModel) -> StructuralDiagnostics:
    """Evalua advertencias estructurales simples antes de resolver.

    Los diagnosticos no reemplazan las validaciones del solver ni garantizan
    estabilidad completa. Su objetivo es detectar problemas frecuentes de
    modelado y entregar informacion clara antes de resolver el sistema.
    """
    counts = count_model_dofs(model)
    warnings: list[StructuralDiagnosticWarning] = []

    warnings.extend(_find_missing_element_nodes(model))
    warnings.extend(_find_zero_length_elements(model))
    warnings.extend(_find_isolated_nodes(model))
    warnings.extend(_find_insufficient_supports(model))

    return StructuralDiagnostics(counts=counts, warnings=tuple(warnings))


def count_model_dofs(model: TrussModel) -> ModelDofCounts:
    """Cuenta nodos, elementos y grados de libertad del modelo."""
    total_dof_count = 2 * len(model.nodes)
    constrained_dof_count = sum(
        len(node.support.constrained_directions()) for node in model.nodes
    )
    return ModelDofCounts(
        node_count=len(model.nodes),
        element_count=len(model.elements),
        total_dof_count=total_dof_count,
        free_dof_count=total_dof_count - constrained_dof_count,
        constrained_dof_count=constrained_dof_count,
    )


def _find_missing_element_nodes(
    model: TrussModel,
) -> tuple[StructuralDiagnosticWarning, ...]:
    """Detecta elementos que referencian nodos inexistentes."""
    node_names = {node.name for node in model.nodes}
    warnings: list[StructuralDiagnosticWarning] = []

    for element in model.elements:
        missing_nodes = [
            node_name
            for node_name in (element.start_node, element.end_node)
            if node_name not in node_names
        ]
        if missing_nodes:
            warnings.append(
                StructuralDiagnosticWarning(
                    code="MISSING_ELEMENT_NODE",
                    message=(
                        f"El elemento {element.name!r} referencia nodos "
                        f"inexistentes: {', '.join(missing_nodes)}."
                    ),
                )
            )

    return tuple(warnings)


def _find_zero_length_elements(
    model: TrussModel,
) -> tuple[StructuralDiagnosticWarning, ...]:
    """Detecta barras cuya longitud geometrica es cero."""
    nodes_by_name = {node.name: node for node in model.nodes}
    warnings: list[StructuralDiagnosticWarning] = []

    for element in model.elements:
        start = nodes_by_name.get(element.start_node)
        end = nodes_by_name.get(element.end_node)
        if start is None or end is None:
            continue
        if hypot(end.x - start.x, end.y - start.y) <= 0.0:
            warnings.append(
                StructuralDiagnosticWarning(
                    code="ZERO_LENGTH_ELEMENT",
                    message=(
                        f"El elemento {element.name!r} tiene longitud cero "
                        f"entre {element.start_node!r} y {element.end_node!r}."
                    ),
                )
            )

    return tuple(warnings)


def _find_isolated_nodes(model: TrussModel) -> tuple[StructuralDiagnosticWarning, ...]:
    """Detecta nodos sin elementos conectados."""
    node_names = {node.name for node in model.nodes}
    connected_nodes = {
        node_name
        for element in model.elements
        for node_name in (element.start_node, element.end_node)
        if node_name in node_names
    }
    isolated_nodes = sorted(node_names - connected_nodes)

    if not isolated_nodes:
        return ()

    return (
        StructuralDiagnosticWarning(
            code="ISOLATED_NODES",
            message=(f"Nodos sin elementos conectados: {', '.join(isolated_nodes)}."),
        ),
    )


def _find_insufficient_supports(
    model: TrussModel,
) -> tuple[StructuralDiagnosticWarning, ...]:
    """Detecta apoyos que no restringen los modos rigidos planos."""
    if not model.nodes:
        return ()

    support_rank = _support_constraint_rank(model)
    if support_rank >= 3:
        return ()

    return (
        StructuralDiagnosticWarning(
            code="INSUFFICIENT_SUPPORTS",
            message=(
                "Los apoyos restringen "
                f"{support_rank} de 3 movimientos rigidos planos. "
                "Revise restricciones independientes en DX y DY antes de resolver."
            ),
        ),
    )


def _support_constraint_rank(model: TrussModel) -> int:
    """Calcula el rango de restricciones contra traslaciones y rotacion rigida."""
    rows: list[list[float]] = []

    for node in model.nodes:
        for direction in node.support.constrained_directions():
            if direction is Direction.X:
                rows.append([1.0, 0.0, -node.y])
            elif direction is Direction.Y:
                rows.append([0.0, 1.0, node.x])

    if not rows:
        return 0

    return int(np.linalg.matrix_rank(np.asarray(rows, dtype=float)))

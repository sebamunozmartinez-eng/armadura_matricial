"""Visualizacion 2D de armaduras planas y resultados."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from analisis_armadura.models import Direction, SupportType, TrussModel

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from analisis_armadura.solver import AnalysisResult

DEFAULT_DEFORMATION_SCALE = 100.0
TENSION_COLOR = "#1f77b4"
COMPRESSION_COLOR = "#d62728"
NEUTRAL_COLOR = "#6f6f6f"
ORIGINAL_COLOR = "#9aa0a6"
LOAD_COLOR = "#2f2f2f"
SUPPORT_COLOR = "#111111"


def plot_truss(
    model: TrussModel,
    result: AnalysisResult | None = None,
    *,
    deformation_scale: float = DEFAULT_DEFORMATION_SCALE,
    show_node_labels: bool = True,
    show_element_labels: bool = True,
    show_loads: bool = True,
    show_supports: bool = True,
    output_path: str | Path | None = None,
) -> Figure:
    """Dibuja la armadura original y, opcionalmente, su deformada.

    Args:
        model: Modelo estructural con nodos, elementos, cargas y apoyos.
        result: Resultado del analisis matricial. Si se entrega, se dibuja la
            deformada y se colorean elementos segun fuerza axial.
        deformation_scale: Factor visual aplicado solo a los desplazamientos
            dibujados. No modifica los desplazamientos reales del resultado.
        show_node_labels: Activa etiquetas de nodos.
        show_element_labels: Activa etiquetas de elementos.
        show_loads: Activa flechas de cargas nodales.
        show_supports: Activa simbolos simples de apoyos.
        output_path: Ruta opcional para guardar la figura.

    Returns:
        Figura de Matplotlib creada.
    """
    import matplotlib.pyplot as plt

    node_coordinates = _node_coordinates(model)
    deformed_coordinates = _deformed_coordinates(
        node_coordinates,
        result,
        deformation_scale,
    )

    fig, ax = plt.subplots(figsize=(10, 7))
    _plot_original_geometry(ax, model, node_coordinates)

    if result is not None:
        _plot_deformed_geometry(ax, model, result, deformed_coordinates)
    else:
        _plot_plain_elements(ax, model, node_coordinates)

    _plot_nodes(ax, node_coordinates)

    if show_node_labels:
        _label_nodes(ax, node_coordinates)
    if show_element_labels:
        _label_elements(ax, model, node_coordinates)
    if show_supports:
        _plot_supports(ax, model, node_coordinates)
    if show_loads:
        _plot_loads(ax, model, node_coordinates)

    _configure_axes(
        ax,
        model,
        node_coordinates,
        deformed_coordinates,
        deformation_scale,
        result,
    )
    _add_legend(ax, result)

    if output_path is not None:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=180, bbox_inches="tight")

    return fig


def _node_coordinates(model: TrussModel) -> dict[str, tuple[float, float]]:
    """Devuelve coordenadas nodales por nombre."""
    return {node.name: (node.x, node.y) for node in model.nodes}


def _deformed_coordinates(
    node_coordinates: dict[str, tuple[float, float]],
    result: AnalysisResult | None,
    deformation_scale: float,
) -> dict[str, tuple[float, float]]:
    """Calcula coordenadas deformadas solo para visualizacion."""
    if result is None:
        return dict(node_coordinates)

    displacement_by_dof = {
        dof: float(value)
        for dof, value in zip(
            result.dof_order,
            result.global_displacements,
            strict=True,
        )
    }
    deformed: dict[str, tuple[float, float]] = {}
    for node_name, (x_coord, y_coord) in node_coordinates.items():
        dx = displacement_by_dof.get((node_name, Direction.X), 0.0)
        dy = displacement_by_dof.get((node_name, Direction.Y), 0.0)
        deformed[node_name] = (
            x_coord + deformation_scale * dx,
            y_coord + deformation_scale * dy,
        )
    return deformed


def _plot_original_geometry(
    ax: Axes,
    model: TrussModel,
    node_coordinates: dict[str, tuple[float, float]],
) -> None:
    """Dibuja la geometria original como referencia."""
    for element in model.elements:
        start = node_coordinates[element.start_node]
        end = node_coordinates[element.end_node]
        ax.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            color=ORIGINAL_COLOR,
            linewidth=1.2,
            linestyle="--",
            zorder=1,
        )


def _plot_plain_elements(
    ax: Axes,
    model: TrussModel,
    node_coordinates: dict[str, tuple[float, float]],
) -> None:
    """Dibuja elementos sin resultados de analisis."""
    for element in model.elements:
        start = node_coordinates[element.start_node]
        end = node_coordinates[element.end_node]
        ax.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            color=NEUTRAL_COLOR,
            linewidth=2.0,
            zorder=2,
        )


def _plot_deformed_geometry(
    ax: Axes,
    model: TrussModel,
    result: AnalysisResult,
    deformed_coordinates: dict[str, tuple[float, float]],
) -> None:
    """Dibuja elementos deformados coloreados por fuerza axial."""
    force_by_element = {
        name: float(force)
        for name, force in zip(result.member_names, result.internal_forces, strict=True)
    }
    max_force = max((abs(force) for force in force_by_element.values()), default=0.0)

    for element in model.elements:
        start = deformed_coordinates[element.start_node]
        end = deformed_coordinates[element.end_node]
        force = force_by_element.get(element.name, 0.0)
        ax.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            color=_force_color(force),
            linewidth=_force_linewidth(force, max_force),
            zorder=3,
        )


def _plot_nodes(
    ax: Axes,
    node_coordinates: dict[str, tuple[float, float]],
) -> None:
    """Dibuja nodos del modelo."""
    x_values = [coordinates[0] for coordinates in node_coordinates.values()]
    y_values = [coordinates[1] for coordinates in node_coordinates.values()]
    ax.scatter(
        x_values,
        y_values,
        s=38,
        color="#ffffff",
        edgecolor="#202124",
        linewidth=1.1,
        zorder=4,
    )


def _label_nodes(
    ax: Axes,
    node_coordinates: dict[str, tuple[float, float]],
) -> None:
    """Etiqueta nodos."""
    span = _plot_span(node_coordinates)
    offset = 0.018 * span
    for name, (x_coord, y_coord) in node_coordinates.items():
        ax.text(
            x_coord + offset,
            y_coord + offset,
            name,
            fontsize=8,
            color="#202124",
            zorder=5,
        )


def _label_elements(
    ax: Axes,
    model: TrussModel,
    node_coordinates: dict[str, tuple[float, float]],
) -> None:
    """Etiqueta elementos en su posicion media original."""
    for element in model.elements:
        start = node_coordinates[element.start_node]
        end = node_coordinates[element.end_node]
        ax.text(
            (start[0] + end[0]) / 2.0,
            (start[1] + end[1]) / 2.0,
            element.name,
            fontsize=7,
            color="#4a4a4a",
            ha="center",
            va="center",
            zorder=5,
        )


def _plot_supports(
    ax: Axes,
    model: TrussModel,
    node_coordinates: dict[str, tuple[float, float]],
) -> None:
    """Representa apoyos con simbolos simples."""
    span = _plot_span(node_coordinates)
    offset = 0.028 * span
    for node in model.nodes:
        if node.support is SupportType.FREE:
            continue
        x_coord, y_coord = node_coordinates[node.name]
        if node.support is SupportType.FIXED:
            ax.scatter(
                [x_coord],
                [y_coord - offset],
                marker="^",
                s=110,
                color=SUPPORT_COLOR,
                zorder=4,
            )
        elif node.support is SupportType.FIXED_X:
            ax.scatter(
                [x_coord - offset],
                [y_coord],
                marker=">",
                s=95,
                color=SUPPORT_COLOR,
                zorder=4,
            )
        elif node.support is SupportType.FIXED_Y:
            ax.scatter(
                [x_coord],
                [y_coord - offset],
                marker="^",
                s=95,
                facecolor="#ffffff",
                edgecolor=SUPPORT_COLOR,
                linewidth=1.4,
                zorder=4,
            )


def _plot_loads(
    ax: Axes,
    model: TrussModel,
    node_coordinates: dict[str, tuple[float, float]],
) -> None:
    """Dibuja flechas de cargas nodales."""
    if not model.loads:
        return

    max_load = max(abs(load.magnitude) for load in model.loads)
    if max_load <= 0.0:
        return

    arrow_base = 0.11 * _plot_span(node_coordinates)
    for load in model.loads:
        x_coord, y_coord = node_coordinates[load.node]
        magnitude_ratio = abs(load.magnitude) / max_load
        arrow_length = arrow_base * magnitude_ratio
        sign = float(np.sign(load.magnitude))
        dx = arrow_length * sign if load.direction is Direction.X else 0.0
        dy = arrow_length * sign if load.direction is Direction.Y else 0.0

        ax.annotate(
            "",
            xy=(x_coord + dx, y_coord + dy),
            xytext=(x_coord, y_coord),
            arrowprops={
                "arrowstyle": "->",
                "color": LOAD_COLOR,
                "linewidth": 1.6,
                "shrinkA": 4,
                "shrinkB": 0,
            },
            zorder=6,
        )


def _configure_axes(
    ax: Axes,
    model: TrussModel,
    node_coordinates: dict[str, tuple[float, float]],
    deformed_coordinates: dict[str, tuple[float, float]],
    deformation_scale: float,
    result: AnalysisResult | None,
) -> None:
    """Aplica configuracion visual general."""
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.grid(True, color="#e0e0e0", linewidth=0.8)

    title = "Armadura 2D"
    if result is not None:
        title += f" - deformada (factor visual x{deformation_scale:g})"
    ax.set_title(title)

    span = _plot_span(node_coordinates)
    padding = 0.12 * span
    visible_coordinates = list(node_coordinates.values())
    if result is not None:
        visible_coordinates.extend(deformed_coordinates.values())
    x_values = [coordinates[0] for coordinates in visible_coordinates]
    y_values = [coordinates[1] for coordinates in visible_coordinates]
    ax.set_xlim(min(x_values) - padding, max(x_values) + padding)
    ax.set_ylim(min(y_values) - padding, max(y_values) + padding)

    if not model.elements:
        ax.text(0.5, 0.5, "Modelo sin elementos", transform=ax.transAxes)


def _add_legend(ax: Axes, result: AnalysisResult | None) -> None:
    """Agrega una leyenda compacta."""
    from matplotlib.lines import Line2D

    legend_items = [
        Line2D([0], [0], color=ORIGINAL_COLOR, linestyle="--", label="Original"),
    ]
    if result is not None:
        legend_items.extend(
            [
                Line2D([0], [0], color=TENSION_COLOR, linewidth=2.5, label="Tension"),
                Line2D(
                    [0],
                    [0],
                    color=COMPRESSION_COLOR,
                    linewidth=2.5,
                    label="Compresion",
                ),
                Line2D([0], [0], color=NEUTRAL_COLOR, linewidth=2.5, label="Neutro"),
            ]
        )

    ax.legend(
        handles=legend_items,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0.0,
        frameon=True,
    )


def _force_color(force: float) -> str:
    """Devuelve color segun el signo de la fuerza axial."""
    if force > 0.0:
        return TENSION_COLOR
    if force < 0.0:
        return COMPRESSION_COLOR
    return NEUTRAL_COLOR


def _force_linewidth(force: float, max_force: float) -> float:
    """Escala visualmente el espesor segun magnitud relativa."""
    if max_force <= 0.0:
        return 2.0
    return 1.8 + 2.2 * abs(force) / max_force


def _plot_span(node_coordinates: dict[str, tuple[float, float]]) -> float:
    """Calcula una dimension representativa del grafico."""
    x_values = [coordinates[0] for coordinates in node_coordinates.values()]
    y_values = [coordinates[1] for coordinates in node_coordinates.values()]
    width = max(x_values) - min(x_values)
    height = max(y_values) - min(y_values)
    return max(width, height, 1.0)

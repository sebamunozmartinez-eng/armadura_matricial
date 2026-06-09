"""Pruebas para visualizacion de armaduras."""

from __future__ import annotations

import matplotlib
import numpy as np

matplotlib.use("Agg")

from matplotlib import pyplot as plt  # noqa: E402

from analisis_armadura import MatrixTrussAnalyzer, create_default_model, plot_truss


def test_plot_truss_creates_png_with_analysis_result(tmp_path) -> None:
    """La visualizacion con resultado genera un PNG no vacio."""
    model = create_default_model()
    result = MatrixTrussAnalyzer(model).solve()
    output_path = tmp_path / "caso_base.png"

    figure = plot_truss(
        model,
        result,
        deformation_scale=100.0,
        output_path=output_path,
    )
    plt.close(figure)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_truss_without_result_creates_geometry_png(tmp_path) -> None:
    """La visualizacion tambien funciona solo con geometria."""
    model = create_default_model()
    output_path = tmp_path / "geometria.png"

    figure = plot_truss(
        model,
        output_path=output_path,
        show_node_labels=False,
        show_element_labels=False,
    )
    plt.close(figure)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_deformation_scale_does_not_mutate_displacements(tmp_path) -> None:
    """El factor de deformada es solo visual y no altera resultados."""
    model = create_default_model()
    result = MatrixTrussAnalyzer(model).solve()
    original_displacements = result.global_displacements.copy()

    figure = plot_truss(
        model,
        result,
        deformation_scale=500.0,
        output_path=tmp_path / "deformada.png",
    )
    plt.close(figure)

    np.testing.assert_allclose(result.global_displacements, original_displacements)

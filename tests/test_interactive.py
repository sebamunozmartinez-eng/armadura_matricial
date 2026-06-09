"""Pruebas para los ejemplos interactivos de consola."""

from __future__ import annotations

import numpy as np

from analisis_armadura.interactive import (
    build_scaled_default_model,
    build_triangular_roof_truss,
    build_warren_truss,
    run_interactive,
)
from analisis_armadura.presentation import format_detailed_report
from analisis_armadura.solver import MatrixTrussAnalyzer


def test_scaled_default_model_preserves_linear_response() -> None:
    """Escalar cargas escala linealmente los desplazamientos del caso base."""
    base_result = MatrixTrussAnalyzer(build_scaled_default_model(1.0)).solve()
    scaled_result = MatrixTrussAnalyzer(build_scaled_default_model(2.0)).solve()

    np.testing.assert_allclose(
        scaled_result.unknown_displacements,
        base_result.unknown_displacements * 2.0,
        rtol=1e-7,
        atol=1e-10,
    )


def test_triangular_roof_case_solves_and_reports_units() -> None:
    """La armadura triangular predefinida se resuelve correctamente."""
    model = build_triangular_roof_truss(
        span_m=6.0,
        height_m=2.5,
        area_m2=0.000416,
        elastic_modulus_kgf_m2=200e6,
        top_load_kgf=10.0,
    )
    result = MatrixTrussAnalyzer(model).solve()
    report = format_detailed_report(result)

    assert len(result.member_names) == 3
    assert "Desplazamientos [cm]" in report
    assert "Reacciones [kgf]" in report
    assert "Fuerzas internas de elementos [kgf]" in report
    assert "array(" not in report


def test_warren_case_solves_and_reports_units() -> None:
    """La armadura Warren predefinida se resuelve correctamente."""
    model = build_warren_truss(
        span_m=8.0,
        height_m=2.0,
        area_m2=0.000416,
        elastic_modulus_kgf_m2=200e6,
        top_node_load_kgf=8.0,
    )
    result = MatrixTrussAnalyzer(model).solve()
    report = format_detailed_report(result)

    assert len(result.member_names) == 7
    assert "E1" in report
    assert "kgf" in report
    assert "cm" in report


def test_run_interactive_triangular_case_with_simulated_input() -> None:
    """El menu interactivo puede ejecutarse con entradas simuladas."""
    responses = iter(("2", "6", "2.5", "", "", "10"))
    output_lines: list[str] = []

    result = run_interactive(
        input_func=lambda _prompt: next(responses),
        output_func=output_lines.append,
    )

    assert result is not None
    assert len(result.member_names) == 3
    output = "\n".join(output_lines)
    assert "Analisis interactivo de armaduras" in output
    assert "Analisis completado correctamente" in output
    assert "Desplazamiento maximo:" in output

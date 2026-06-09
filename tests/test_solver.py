"""Pruebas de regresion para el analisis matricial de armaduras."""

from __future__ import annotations

import runpy
from pathlib import Path

import numpy as np
import pytest

from analisis_armadura import (
    Direction,
    Element,
    MatrixTrussAnalyzer,
    Node,
    SupportType,
    TrussModel,
    TrussValidationError,
    cli,
    create_default_model,
)
from analisis_armadura.presentation import (
    format_detailed_report,
    format_displacements,
    format_internal_forces,
    format_reactions,
)

EXPECTED_UNKNOWN_DISPLACEMENTS = np.array(
    [
        1.20475124e-02,
        1.03895340e-03,
        8.46139382e-03,
        1.14822357e-03,
        8.59472991e-03,
        -3.61139182e-03,
        1.62413467e-02,
        -3.20107676e-03,
        1.37665197e-03,
        -1.21204390e-03,
        1.14526361e-03,
        8.60330271e-05,
    ],
    dtype=float,
)

EXPECTED_REACTIONS = np.array(
    [-5.19299131, 22.0, -0.80700869, -2.0],
    dtype=float,
)

EXPECTED_INTERNAL_FORCES = [
    -11.66,
    -6.59,
    1.85,
    -6.56,
    0.15,
    7.36,
    -16.64,
    11.66,
    6.59,
    3.21,
    1.14,
    -7.34,
    1.19,
    -16.81,
    0.0,
]


def test_default_model_preserves_original_results() -> None:
    """El caso base conserva los resultados numericos del script original."""
    result = MatrixTrussAnalyzer(create_default_model()).solve()

    np.testing.assert_allclose(
        result.unknown_displacements,
        EXPECTED_UNKNOWN_DISPLACEMENTS,
        rtol=1e-7,
        atol=1e-10,
    )
    np.testing.assert_allclose(
        result.reactions,
        EXPECTED_REACTIONS,
        rtol=1e-7,
        atol=1e-8,
    )
    assert result.internal_forces_rounded() == EXPECTED_INTERNAL_FORCES


def test_internal_forces_are_one_dimensional_scalars() -> None:
    """La antigua TensionCompresion ya no genera arrays anidados."""
    result = MatrixTrussAnalyzer(create_default_model()).solve()

    assert result.internal_forces.ndim == 1
    assert result.internal_forces.shape == (15,)
    assert all(isinstance(value, float) for value in result.internal_forces.tolist())


def test_rejects_zero_length_elements() -> None:
    """El analizador reporta datos geometricos invalidos con claridad."""
    model = TrussModel(
        nodes=(
            Node("N1", 0.0, 0.0, SupportType.FREE),
            Node("N2", 0.0, 0.0, SupportType.FIXED),
        ),
        elements=(Element("E1", 1.0, 200.0, "N1", "N2"),),
    )

    with pytest.raises(TrussValidationError, match="longitud cero"):
        MatrixTrussAnalyzer(model)


def test_rejects_prescribed_displacement_on_free_dof() -> None:
    """Un desplazamiento prescrito debe pertenecer a un apoyo."""
    from analisis_armadura import PrescribedDisplacement

    model = TrussModel(
        nodes=(
            Node("N1", 0.0, 0.0, SupportType.FREE),
            Node("N2", 1.0, 0.0, SupportType.FIXED),
        ),
        elements=(Element("E1", 1.0, 200.0, "N1", "N2"),),
        prescribed_displacements=(PrescribedDisplacement(0.0, "N1", Direction.X),),
    )

    with pytest.raises(TrussValidationError, match="grados restringidos"):
        MatrixTrussAnalyzer(model)


def test_cli_main_prints_executive_summary(capsys: pytest.CaptureFixture[str]) -> None:
    """El CLI muestra un resumen breve y devuelve el resultado completo."""
    result = cli.main()

    captured = capsys.readouterr()
    assert "Analisis completado correctamente" in captured.out
    assert "Numero de nodos: 8" in captured.out
    assert "Numero de elementos: 15" in captured.out
    assert "Desplazamiento maximo: 1.624 cm" in captured.out
    assert "Numero de reacciones calculadas: 4" in captured.out
    assert "Matriz" not in captured.out
    assert "Vector" not in captured.out
    assert captured.err == ""
    np.testing.assert_allclose(
        result.unknown_displacements,
        EXPECTED_UNKNOWN_DISPLACEMENTS,
        rtol=1e-7,
        atol=1e-10,
    )


def test_launcher_import_has_no_side_effects(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Importar el launcher no ejecuta el analisis ni define resultados globales."""
    script_path = Path(__file__).resolve().parents[1] / "Analisis_Armadura.py"
    namespace = runpy.run_path(str(script_path))

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(namespace["main"])
    assert "resultado" not in namespace
    assert "desplazamientos" not in namespace
    assert "reacciones" not in namespace


def test_presentation_formats_units_consistently() -> None:
    """La capa de presentacion aplica unidades y etiquetas consistentes."""
    result = MatrixTrussAnalyzer(create_default_model()).solve()

    displacements = format_displacements(result)
    reactions = format_reactions(result)
    internal_forces = format_internal_forces(result)
    report = format_detailed_report(result)

    assert "D1 = 1.205 cm" in displacements
    assert "D16 = 0.000 cm" in displacements
    assert "N8 DX = -5.19 kgf" in reactions
    assert "N8 DY = 22.00 kgf" in reactions
    assert "E1 (Compresion) = -11.66 kgf" in internal_forces
    assert "E3 (Tension) = 1.85 kgf" in internal_forces
    assert "kgf" in report
    assert "cm" in report
    assert "array(" not in report
    assert "[[" not in report

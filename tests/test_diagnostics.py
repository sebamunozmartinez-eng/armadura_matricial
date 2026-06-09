"""Pruebas de diagnosticos estructurales previos al analisis."""

from __future__ import annotations

from analisis_armadura import (
    Element,
    Node,
    SupportType,
    TrussModel,
    create_default_model,
    diagnose_model,
)
from analisis_armadura.presentation import format_diagnostics_report


def test_default_model_diagnostics_report_counts_without_warnings() -> None:
    """El caso base tiene conteos esperados y no presenta advertencias."""
    diagnostics = diagnose_model(create_default_model())

    assert diagnostics.counts.node_count == 8
    assert diagnostics.counts.element_count == 15
    assert diagnostics.counts.total_dof_count == 16
    assert diagnostics.counts.free_dof_count == 12
    assert diagnostics.counts.constrained_dof_count == 4
    assert diagnostics.warnings == ()

    report = format_diagnostics_report(diagnostics)
    assert "Diagnostico estructural previo" in report
    assert "Grados de libertad libres: 12" in report
    assert "Advertencias: no se detectaron problemas previos." in report


def test_diagnostics_detect_isolated_nodes() -> None:
    """Un nodo sin barras conectadas queda reportado antes de resolver."""
    model = TrussModel(
        nodes=(
            Node("N1", 0.0, 0.0, SupportType.FIXED),
            Node("N2", 1.0, 0.0, SupportType.FIXED),
            Node("N3", 0.5, 1.0, SupportType.FREE),
        ),
        elements=(Element("E1", 1.0, 200.0, "N1", "N2"),),
    )

    diagnostics = diagnose_model(model)

    assert _warning_codes(diagnostics) == {"ISOLATED_NODES"}
    assert "N3" in diagnostics.warning_messages()[0]


def test_diagnostics_detect_zero_length_elements() -> None:
    """Una barra con nodos coincidentes queda reportada como longitud cero."""
    model = TrussModel(
        nodes=(
            Node("N1", 0.0, 0.0, SupportType.FIXED),
            Node("N2", 0.0, 0.0, SupportType.FIXED),
        ),
        elements=(Element("E1", 1.0, 200.0, "N1", "N2"),),
    )

    diagnostics = diagnose_model(model)

    assert "ZERO_LENGTH_ELEMENT" in _warning_codes(diagnostics)
    assert any("E1" in message for message in diagnostics.warning_messages())


def test_diagnostics_detect_insufficient_supports() -> None:
    """Apoyos que no bloquean modos rigidos se reportan con claridad."""
    model = TrussModel(
        nodes=(
            Node("N1", 0.0, 0.0, SupportType.FIXED),
            Node("N2", 1.0, 0.0, SupportType.FREE),
            Node("N3", 0.5, 1.0, SupportType.FREE),
        ),
        elements=(
            Element("E1", 1.0, 200.0, "N1", "N2"),
            Element("E2", 1.0, 200.0, "N2", "N3"),
            Element("E3", 1.0, 200.0, "N3", "N1"),
        ),
    )

    diagnostics = diagnose_model(model)

    assert "INSUFFICIENT_SUPPORTS" in _warning_codes(diagnostics)
    assert any(
        "3 movimientos rigidos" in message for message in diagnostics.warning_messages()
    )


def _warning_codes(diagnostics) -> set[str]:
    """Devuelve los codigos de advertencia para aserciones compactas."""
    return {warning.code for warning in diagnostics.warnings}

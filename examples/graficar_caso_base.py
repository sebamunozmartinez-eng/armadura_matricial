"""Genera una figura del caso base con deformada e internas."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from matplotlib import pyplot as plt  # noqa: E402

from analisis_armadura import (  # noqa: E402
    MatrixTrussAnalyzer,
    create_default_model,
    diagnose_model,
    plot_truss,
)
from analisis_armadura.presentation import format_diagnostics_report  # noqa: E402

OUTPUT_PATH = PROJECT_ROOT / "outputs" / "figures" / "caso_base_deformada.png"


def main() -> None:
    """Resuelve el caso base y guarda una visualizacion 2D."""
    model = create_default_model()
    diagnostics = diagnose_model(model)
    print(format_diagnostics_report(diagnostics))

    result = MatrixTrussAnalyzer(model).solve()
    figure = plot_truss(
        model,
        result,
        deformation_scale=100.0,
        show_node_labels=True,
        show_element_labels=True,
        output_path=OUTPUT_PATH,
    )
    plt.close(figure)
    print(f"Figura guardada en: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

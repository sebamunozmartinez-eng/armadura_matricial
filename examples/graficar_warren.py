"""Genera una figura de una armadura Warren con deformada."""

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
    build_warren_truss,
    diagnose_model,
    plot_truss,
)
from analisis_armadura.presentation import format_diagnostics_report  # noqa: E402

OUTPUT_PATH = PROJECT_ROOT / "outputs" / "figures" / "warren_deformada.png"


def main() -> None:
    """Resuelve una Warren de dos paneles y guarda una visualizacion 2D."""
    model = build_warren_truss(
        span_m=8.0,
        height_m=2.0,
        area_m2=0.000416,
        elastic_modulus_kgf_m2=200e6,
        top_node_load_kgf=8.0,
    )
    diagnostics = diagnose_model(model)
    print(format_diagnostics_report(diagnostics))

    result = MatrixTrussAnalyzer(model).solve()
    figure = plot_truss(
        model,
        result,
        deformation_scale=120.0,
        show_node_labels=True,
        show_element_labels=True,
        output_path=OUTPUT_PATH,
    )
    plt.close(figure)
    print(f"Figura guardada en: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

"""Ejemplo ejecutable del caso base de la armadura."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from analisis_armadura import MatrixTrussAnalyzer, create_default_model  # noqa: E402
from analisis_armadura.presentation import format_detailed_report  # noqa: E402


def main() -> None:
    """Ejecuta el modelo base y muestra los resultados principales."""
    model = create_default_model()
    result = MatrixTrussAnalyzer(model).solve()
    print(format_detailed_report(result))


if __name__ == "__main__":
    main()

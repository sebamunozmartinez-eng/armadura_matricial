"""Launcher de compatibilidad para ejecutar el analisis de armadura."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analisis_armadura.solver import AnalysisResult

PROJECT_DIR = Path(__file__).resolve().parent
SRC_PATHS = (
    PROJECT_DIR / "src",
    PROJECT_DIR / "armadura_matricial" / "src",
)


def configure_import_path() -> None:
    """Agrega la carpeta ``src`` al path cuando el paquete no esta instalado."""
    for src_path in SRC_PATHS:
        if src_path.exists() and str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
            break


def main() -> AnalysisResult:
    """Ejecuta el analisis base y devuelve el resultado completo."""
    configure_import_path()
    from analisis_armadura.cli import main as run_cli

    return run_cli()


if __name__ == "__main__":
    main()

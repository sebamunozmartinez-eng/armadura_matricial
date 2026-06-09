"""Ejecuta casos interactivos de armaduras desde consola."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from analisis_armadura.interactive import run_interactive  # noqa: E402


def main() -> int:
    """Ejecuta el menu interactivo y devuelve codigo de salida."""
    return 0 if run_interactive() is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())

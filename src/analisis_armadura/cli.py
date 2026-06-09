"""Interfaz de linea de comandos para el caso base de armadura."""

from analisis_armadura.data import create_default_model
from analisis_armadura.presentation import (
    build_executive_summary,
    format_executive_summary,
)
from analisis_armadura.solver import AnalysisResult, MatrixTrussAnalyzer


def run_default_analysis() -> AnalysisResult:
    """Resuelve el caso base incluido en el proyecto.

    Returns:
        Resultado completo del analisis matricial.
    """
    model = create_default_model()
    return MatrixTrussAnalyzer(model).solve()


def main() -> AnalysisResult:
    """Ejecuta el analisis base, imprime un resumen y devuelve resultados."""
    result = run_default_analysis()
    print(format_executive_summary(build_executive_summary(result)))
    return result

"""Datos de ejemplo para reproducir el analisis original."""

from analisis_armadura.models import (
    Direction,
    Element,
    NodalLoad,
    Node,
    PrescribedDisplacement,
    SupportType,
    TrussModel,
)

AREA_M2 = 0.000416
ELASTIC_MODULUS_KGF_M2 = 200 * 10**6


def create_default_model() -> TrussModel:
    """Crea el modelo de armadura usado por el script original.

    Returns:
        Modelo completo con nodos, elementos, cargas nodales y
        desplazamientos prescritos en los apoyos.
    """
    elements = (
        Element("E1", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N1", "N6"),
        Element("E2", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N1", "N2"),
        Element("E3", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N2", "N3"),
        Element("E4", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N2", "N5"),
        Element("E5", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N3", "N6"),
        Element("E6", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N2", "N6"),
        Element("E7", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N3", "N5"),
        Element("E8", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N3", "N4"),
        Element("E9", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N4", "N5"),
        Element("E10", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N6", "N5"),
        Element("E11", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N5", "N7"),
        Element("E12", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N6", "N8"),
        Element("E13", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N6", "N7"),
        Element("E14", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N5", "N8"),
        Element("E15", AREA_M2, ELASTIC_MODULUS_KGF_M2, "N7", "N8"),
    )

    nodes = (
        Node("N1", -1.0, 12.0, SupportType.FREE),
        Node("N2", 0.0, 18.0, SupportType.FREE),
        Node("N3", 6.0, 18.0, SupportType.FREE),
        Node("N4", 7.0, 12.0, SupportType.FREE),
        Node("N5", 6.0, 6.0, SupportType.FREE),
        Node("N6", 0.0, 6.0, SupportType.FREE),
        Node("N7", 0.0, 0.0, SupportType.FIXED),
        Node("N8", 6.0, 0.0, SupportType.FIXED),
    )

    loads = (
        NodalLoad(-5.0, "N1", Direction.Y),
        NodalLoad(3.0, "N1", Direction.X),
        NodalLoad(-5.0, "N2", Direction.Y),
        NodalLoad(-5.0, "N3", Direction.Y),
        NodalLoad(3.0, "N4", Direction.X),
        NodalLoad(-5.0, "N4", Direction.Y),
    )

    prescribed_displacements = (
        PrescribedDisplacement(0.0, "N7", Direction.X),
        PrescribedDisplacement(0.0, "N7", Direction.Y),
        PrescribedDisplacement(0.0, "N8", Direction.X),
        PrescribedDisplacement(0.0, "N8", Direction.Y),
    )

    return TrussModel(
        nodes=nodes,
        elements=elements,
        loads=loads,
        prescribed_displacements=prescribed_displacements,
    )

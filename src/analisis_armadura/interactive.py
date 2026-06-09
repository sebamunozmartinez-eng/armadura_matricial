"""Ejemplos interactivos para ejecutar analisis desde consola."""

from __future__ import annotations

from collections.abc import Callable

from analisis_armadura.data import (
    AREA_M2,
    ELASTIC_MODULUS_KGF_M2,
    create_default_model,
)
from analisis_armadura.models import (
    Direction,
    Element,
    NodalLoad,
    Node,
    PrescribedDisplacement,
    SupportType,
    TrussModel,
)
from analisis_armadura.presentation import FORCE_UNIT, format_detailed_report
from analisis_armadura.solver import (
    AnalysisResult,
    MatrixTrussAnalyzer,
    TrussAnalysisError,
    TrussValidationError,
)

InputReader = Callable[[str], str]
OutputWriter = Callable[[str], None]


def build_scaled_default_model(load_factor: float) -> TrussModel:
    """Crea el caso base escalando todas las cargas nodales."""
    base_model = create_default_model()
    loads = tuple(
        NodalLoad(
            magnitude=load.magnitude * load_factor,
            node=load.node,
            direction=load.direction,
        )
        for load in base_model.loads
    )
    return TrussModel(
        nodes=base_model.nodes,
        elements=base_model.elements,
        loads=loads,
        prescribed_displacements=base_model.prescribed_displacements,
    )


def build_triangular_roof_truss(
    span_m: float,
    height_m: float,
    area_m2: float,
    elastic_modulus_kgf_m2: float,
    top_load_kgf: float,
) -> TrussModel:
    """Crea una armadura triangular simple con carga vertical en cumbrera."""
    half_span = span_m / 2.0
    return TrussModel(
        nodes=(
            Node("N1", 0.0, 0.0, SupportType.FIXED),
            Node("N2", span_m, 0.0, SupportType.FIXED_Y),
            Node("N3", half_span, height_m, SupportType.FREE),
        ),
        elements=(
            Element("E1", area_m2, elastic_modulus_kgf_m2, "N1", "N2"),
            Element("E2", area_m2, elastic_modulus_kgf_m2, "N1", "N3"),
            Element("E3", area_m2, elastic_modulus_kgf_m2, "N2", "N3"),
        ),
        loads=(NodalLoad(-abs(top_load_kgf), "N3", Direction.Y),),
        prescribed_displacements=(
            PrescribedDisplacement(0.0, "N1", Direction.X),
            PrescribedDisplacement(0.0, "N1", Direction.Y),
            PrescribedDisplacement(0.0, "N2", Direction.Y),
        ),
    )


def build_warren_truss(
    span_m: float,
    height_m: float,
    area_m2: float,
    elastic_modulus_kgf_m2: float,
    top_node_load_kgf: float,
) -> TrussModel:
    """Crea una armadura Warren de dos paneles con dos cargas superiores."""
    return TrussModel(
        nodes=(
            Node("N1", 0.0, 0.0, SupportType.FIXED),
            Node("N2", span_m / 2.0, 0.0, SupportType.FREE),
            Node("N3", span_m, 0.0, SupportType.FIXED_Y),
            Node("N4", span_m / 4.0, height_m, SupportType.FREE),
            Node("N5", 3.0 * span_m / 4.0, height_m, SupportType.FREE),
        ),
        elements=(
            Element("E1", area_m2, elastic_modulus_kgf_m2, "N1", "N2"),
            Element("E2", area_m2, elastic_modulus_kgf_m2, "N2", "N3"),
            Element("E3", area_m2, elastic_modulus_kgf_m2, "N4", "N5"),
            Element("E4", area_m2, elastic_modulus_kgf_m2, "N1", "N4"),
            Element("E5", area_m2, elastic_modulus_kgf_m2, "N4", "N2"),
            Element("E6", area_m2, elastic_modulus_kgf_m2, "N2", "N5"),
            Element("E7", area_m2, elastic_modulus_kgf_m2, "N5", "N3"),
        ),
        loads=(
            NodalLoad(-abs(top_node_load_kgf), "N4", Direction.Y),
            NodalLoad(-abs(top_node_load_kgf), "N5", Direction.Y),
        ),
        prescribed_displacements=(
            PrescribedDisplacement(0.0, "N1", Direction.X),
            PrescribedDisplacement(0.0, "N1", Direction.Y),
            PrescribedDisplacement(0.0, "N3", Direction.Y),
        ),
    )


def read_manual_model(input_func: InputReader = input) -> TrussModel:
    """Lee desde consola un modelo completo de armadura plana."""
    node_count = _read_int("Numero de nodos: ", input_func, minimum=1)
    nodes = tuple(_read_node(index, input_func) for index in range(1, node_count + 1))

    element_count = _read_int("Numero de elementos: ", input_func, minimum=1)
    elements = tuple(
        _read_element(index, input_func) for index in range(1, element_count + 1)
    )

    load_count = _read_int("Numero de cargas nodales: ", input_func, minimum=0)
    loads = tuple(_read_load(index, input_func) for index in range(1, load_count + 1))

    displacement_count = _read_int(
        "Numero de desplazamientos prescritos adicionales: ",
        input_func,
        minimum=0,
        default=0,
    )
    prescribed_displacements = tuple(
        _read_prescribed_displacement(index, input_func)
        for index in range(1, displacement_count + 1)
    )

    return TrussModel(
        nodes=nodes,
        elements=elements,
        loads=loads,
        prescribed_displacements=prescribed_displacements,
    )


def run_interactive(
    input_func: InputReader = input,
    output_func: OutputWriter = print,
) -> AnalysisResult | None:
    """Ejecuta el menu interactivo y muestra el reporte del caso elegido."""
    output_func(_menu_text())
    choice = _read_choice(input_func)

    try:
        model = _build_model_from_choice(choice, input_func)
        result = MatrixTrussAnalyzer(model).solve()
    except (ValueError, TrussValidationError, TrussAnalysisError) as exc:
        output_func(f"No se pudo completar el analisis: {exc}")
        return None

    output_func("")
    output_func(format_detailed_report(result))
    return result


def _build_model_from_choice(choice: str, input_func: InputReader) -> TrussModel:
    """Construye el modelo asociado a una opcion de menu."""
    if choice == "1":
        factor = _read_float(
            "Factor de carga del caso base: ",
            input_func,
            default=1.0,
            positive=True,
        )
        return build_scaled_default_model(factor)

    if choice == "2":
        span_m = _read_float("Luz de la armadura [m]: ", input_func, positive=True)
        height_m = _read_float("Altura de cumbrera [m]: ", input_func, positive=True)
        area_m2 = _read_float(
            "Area de barras [m2]: ",
            input_func,
            default=AREA_M2,
            positive=True,
        )
        elastic_modulus = _read_float(
            "Modulo de elasticidad [kgf/m2]: ",
            input_func,
            default=ELASTIC_MODULUS_KGF_M2,
            positive=True,
        )
        top_load = _read_float(
            f"Carga vertical descendente en N3 [{FORCE_UNIT}]: ",
            input_func,
            positive=True,
        )
        return build_triangular_roof_truss(
            span_m,
            height_m,
            area_m2,
            elastic_modulus,
            top_load,
        )

    if choice == "3":
        span_m = _read_float("Luz total de la Warren [m]: ", input_func, positive=True)
        height_m = _read_float("Altura de la Warren [m]: ", input_func, positive=True)
        area_m2 = _read_float(
            "Area de barras [m2]: ",
            input_func,
            default=AREA_M2,
            positive=True,
        )
        elastic_modulus = _read_float(
            "Modulo de elasticidad [kgf/m2]: ",
            input_func,
            default=ELASTIC_MODULUS_KGF_M2,
            positive=True,
        )
        top_load = _read_float(
            f"Carga descendente por nodo superior [{FORCE_UNIT}]: ",
            input_func,
            positive=True,
        )
        return build_warren_truss(
            span_m,
            height_m,
            area_m2,
            elastic_modulus,
            top_load,
        )

    if choice == "4":
        return read_manual_model(input_func)

    raise ValueError("Opcion no valida.")


def _menu_text() -> str:
    """Devuelve el texto del menu interactivo."""
    return "\n".join(
        (
            "Analisis interactivo de armaduras",
            "1. Caso base con factor de carga",
            "2. Armadura triangular simple",
            "3. Armadura Warren de dos paneles",
            "4. Entrada manual completa",
        )
    )


def _read_choice(input_func: InputReader) -> str:
    """Lee una opcion de menu valida."""
    while True:
        choice = input_func("Seleccione un caso [1-4]: ").strip()
        if choice in {"1", "2", "3", "4"}:
            return choice
        print("Ingrese una opcion valida entre 1 y 4.")


def _read_node(index: int, input_func: InputReader) -> Node:
    """Lee un nodo desde consola."""
    name = _read_text(f"Nodo {index} - nombre: ", input_func)
    x = _read_float(f"Nodo {name} - coordenada X [m]: ", input_func)
    y = _read_float(f"Nodo {name} - coordenada Y [m]: ", input_func)
    support = _read_support(
        f"Nodo {name} - apoyo (Libre/Fijo/DX/DY): ",
        input_func,
    )
    return Node(name, x, y, support)


def _read_element(index: int, input_func: InputReader) -> Element:
    """Lee un elemento desde consola."""
    name = _read_text(f"Elemento {index} - nombre: ", input_func)
    area = _read_float(f"Elemento {name} - area [m2]: ", input_func, positive=True)
    elastic_modulus = _read_float(
        f"Elemento {name} - modulo de elasticidad [kgf/m2]: ",
        input_func,
        positive=True,
    )
    start_node = _read_text(f"Elemento {name} - nodo inicial: ", input_func)
    end_node = _read_text(f"Elemento {name} - nodo final: ", input_func)
    return Element(name, area, elastic_modulus, start_node, end_node)


def _read_load(index: int, input_func: InputReader) -> NodalLoad:
    """Lee una carga nodal desde consola."""
    magnitude = _read_float(f"Carga {index} - magnitud [{FORCE_UNIT}]: ", input_func)
    node = _read_text(f"Carga {index} - nodo: ", input_func)
    direction = _read_direction(f"Carga {index} - direccion (DX/DY): ", input_func)
    return NodalLoad(magnitude, node, direction)


def _read_prescribed_displacement(
    index: int,
    input_func: InputReader,
) -> PrescribedDisplacement:
    """Lee un desplazamiento prescrito desde consola."""
    value = _read_float(f"Desplazamiento {index} - valor [m]: ", input_func)
    node = _read_text(f"Desplazamiento {index} - nodo: ", input_func)
    direction = _read_direction(
        f"Desplazamiento {index} - direccion (DX/DY): ",
        input_func,
    )
    return PrescribedDisplacement(value, node, direction)


def _read_text(prompt: str, input_func: InputReader) -> str:
    """Lee texto no vacio desde consola."""
    while True:
        value = input_func(prompt).strip()
        if value:
            return value
        print("Este campo no puede estar vacio.")


def _read_int(
    prompt: str,
    input_func: InputReader,
    *,
    minimum: int,
    default: int | None = None,
) -> int:
    """Lee un entero con minimo permitido."""
    while True:
        raw_value = input_func(_format_prompt(prompt, default)).strip()
        if not raw_value and default is not None:
            return default
        try:
            value = int(raw_value)
        except ValueError:
            print("Ingrese un numero entero valido.")
            continue
        if value >= minimum:
            return value
        print(f"Ingrese un valor mayor o igual que {minimum}.")


def _read_float(
    prompt: str,
    input_func: InputReader,
    *,
    default: float | None = None,
    positive: bool = False,
) -> float:
    """Lee un numero real con validacion opcional de positividad."""
    while True:
        raw_value = input_func(_format_prompt(prompt, default)).strip()
        if not raw_value and default is not None:
            return default
        try:
            value = float(raw_value)
        except ValueError:
            print("Ingrese un numero valido.")
            continue
        if positive and value <= 0.0:
            print("Ingrese un valor positivo.")
            continue
        return value


def _read_direction(prompt: str, input_func: InputReader) -> Direction:
    """Lee una direccion nodal."""
    while True:
        try:
            return Direction.from_value(input_func(prompt))
        except ValueError as exc:
            print(exc)


def _read_support(prompt: str, input_func: InputReader) -> SupportType:
    """Lee un tipo de apoyo."""
    while True:
        try:
            return SupportType.from_value(input_func(prompt))
        except ValueError as exc:
            print(exc)


def _format_prompt(prompt: str, default: float | int | None) -> str:
    """Agrega el valor por defecto al texto del prompt."""
    if default is None:
        return prompt
    return f"{prompt}[{default}] "

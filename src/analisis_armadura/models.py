"""Modelos de datos para una armadura plana."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum


class Direction(str, Enum):
    """Direccion de un grado de libertad nodal."""

    X = "DX"
    Y = "DY"

    @classmethod
    def from_value(cls, value: str | Direction) -> Direction:
        """Convierte texto o una direccion existente en ``Direction``.

        Args:
            value: Valor ``DX`` o ``DY``.

        Returns:
            Direccion normalizada.

        Raises:
            ValueError: Si el valor no representa una direccion valida.
        """
        if isinstance(value, cls):
            return value

        normalized = str(value).strip().upper()
        for member in cls:
            if normalized == member.value:
                return member

        raise ValueError(f"Direccion no valida: {value!r}. Use 'DX' o 'DY'.")


class SupportType(str, Enum):
    """Tipo de apoyo o restriccion en un nodo."""

    FREE = "Libre"
    FIXED = "Fijo"
    FIXED_X = "DX"
    FIXED_Y = "DY"

    @classmethod
    def from_value(cls, value: str | SupportType) -> SupportType:
        """Convierte texto o un soporte existente en ``SupportType``.

        Args:
            value: Valor ``Libre``, ``Fijo``, ``DX`` o ``DY``.

        Returns:
            Tipo de apoyo normalizado.

        Raises:
            ValueError: Si el valor no representa un tipo de apoyo valido.
        """
        if isinstance(value, cls):
            return value

        normalized = str(value).strip()
        normalized_upper = normalized.upper()
        for member in cls:
            if normalized == member.value or normalized_upper == member.value.upper():
                return member

        raise ValueError(
            f"Tipo de apoyo no valido: {value!r}. Use 'Libre', 'Fijo', 'DX' o 'DY'."
        )

    def constrained_directions(self) -> tuple[Direction, ...]:
        """Devuelve las direcciones restringidas por el apoyo.

        Returns:
            Tupla con las direcciones restringidas.
        """
        if self is SupportType.FIXED:
            return (Direction.X, Direction.Y)
        if self is SupportType.FIXED_X:
            return (Direction.X,)
        if self is SupportType.FIXED_Y:
            return (Direction.Y,)
        return ()


@dataclass(frozen=True)
class Node:
    """Nodo de una armadura plana.

    Attributes:
        name: Identificador unico del nodo.
        x: Coordenada X.
        y: Coordenada Y.
        support: Tipo de restriccion del nodo.
    """

    name: str
    x: float
    y: float
    support: SupportType = SupportType.FREE

    def __post_init__(self) -> None:
        """Normaliza tipos basicos despues de crear la instancia."""
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "x", float(self.x))
        object.__setattr__(self, "y", float(self.y))
        object.__setattr__(self, "support", SupportType.from_value(self.support))


@dataclass(frozen=True)
class Element:
    """Elemento barra de una armadura plana.

    Attributes:
        name: Identificador unico del elemento.
        area: Area transversal.
        elastic_modulus: Modulo de elasticidad.
        start_node: Nodo inicial.
        end_node: Nodo final.
    """

    name: str
    area: float
    elastic_modulus: float
    start_node: str
    end_node: str

    def __post_init__(self) -> None:
        """Normaliza tipos basicos despues de crear la instancia."""
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "area", float(self.area))
        object.__setattr__(self, "elastic_modulus", float(self.elastic_modulus))
        object.__setattr__(self, "start_node", str(self.start_node))
        object.__setattr__(self, "end_node", str(self.end_node))


@dataclass(frozen=True)
class NodalLoad:
    """Carga puntual aplicada sobre un grado de libertad nodal."""

    magnitude: float
    node: str
    direction: Direction

    def __post_init__(self) -> None:
        """Normaliza tipos basicos despues de crear la instancia."""
        object.__setattr__(self, "magnitude", float(self.magnitude))
        object.__setattr__(self, "node", str(self.node))
        object.__setattr__(self, "direction", Direction.from_value(self.direction))


@dataclass(frozen=True)
class PrescribedDisplacement:
    """Desplazamiento conocido en un grado de libertad restringido."""

    value: float
    node: str
    direction: Direction

    def __post_init__(self) -> None:
        """Normaliza tipos basicos despues de crear la instancia."""
        object.__setattr__(self, "value", float(self.value))
        object.__setattr__(self, "node", str(self.node))
        object.__setattr__(self, "direction", Direction.from_value(self.direction))


@dataclass(frozen=True)
class TrussModel:
    """Modelo completo de una armadura plana.

    Attributes:
        nodes: Coleccion de nodos.
        elements: Coleccion de elementos barra.
        loads: Cargas externas aplicadas.
        prescribed_displacements: Desplazamientos conocidos en apoyos.
    """

    nodes: Sequence[Node]
    elements: Sequence[Element]
    loads: Sequence[NodalLoad] = ()
    prescribed_displacements: Sequence[PrescribedDisplacement] = ()

    def __post_init__(self) -> None:
        """Convierte colecciones mutables en tuplas inmutables."""
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "elements", tuple(self.elements))
        object.__setattr__(self, "loads", tuple(self.loads))
        object.__setattr__(
            self,
            "prescribed_displacements",
            tuple(self.prescribed_displacements),
        )

    @classmethod
    def from_legacy_tables(
        cls,
        element_table: Sequence[Sequence[object]],
        node_table: Sequence[Sequence[object]],
        load_table: Sequence[Sequence[object]],
        displacement_table: Sequence[Sequence[object]],
    ) -> TrussModel:
        """Crea un modelo desde tablas con el formato del script original.

        Args:
            element_table: Filas ``[elemento, area, E, nodo_i, nodo_f]``.
            node_table: Filas ``[nodo, x, y, tipo_apoyo]``.
            load_table: Filas ``[magnitud, nodo, direccion]``.
            displacement_table: Filas ``[valor, nodo, direccion]``.

        Returns:
            Modelo tipado listo para analizar.
        """
        elements = tuple(
            Element(
                name=str(row[0]),
                area=float(row[1]),
                elastic_modulus=float(row[2]),
                start_node=str(row[3]),
                end_node=str(row[4]),
            )
            for row in element_table
        )
        nodes = tuple(
            Node(
                name=str(row[0]),
                x=float(row[1]),
                y=float(row[2]),
                support=SupportType.from_value(str(row[3])),
            )
            for row in node_table
        )
        loads = tuple(
            NodalLoad(
                magnitude=float(row[0]),
                node=str(row[1]),
                direction=Direction.from_value(str(row[2])),
            )
            for row in load_table
        )
        prescribed_displacements = tuple(
            PrescribedDisplacement(
                value=float(row[0]),
                node=str(row[1]),
                direction=Direction.from_value(str(row[2])),
            )
            for row in displacement_table
        )
        return cls(
            nodes=nodes,
            elements=elements,
            loads=loads,
            prescribed_displacements=prescribed_displacements,
        )

"""Solucionador matricial para armaduras planas."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import hypot, isfinite

import numpy as np
import numpy.typing as npt

from analisis_armadura.models import (
    Direction,
    Element,
    Node,
    TrussModel,
)

ArrayFloat = npt.NDArray[np.float64]
DegreeOfFreedom = tuple[str, Direction]


class TrussValidationError(ValueError):
    """Error provocado por datos invalidos del modelo."""


class TrussAnalysisError(RuntimeError):
    """Error provocado por una falla numerica del analisis."""


@dataclass(frozen=True)
class DofMapping:
    """Mapeo entre grados de libertad fisicos e indices matriciales."""

    free_dofs: tuple[DegreeOfFreedom, ...]
    constrained_dofs: tuple[DegreeOfFreedom, ...]
    dof_order: tuple[DegreeOfFreedom, ...]
    dof_to_index: Mapping[DegreeOfFreedom, int]

    @property
    def free_count(self) -> int:
        """Cantidad de grados de libertad libres."""
        return len(self.free_dofs)

    @property
    def total_count(self) -> int:
        """Cantidad total de grados de libertad."""
        return len(self.dof_order)


@dataclass(frozen=True)
class TrussMember:
    """Elemento de calculo con matrices locales y globales."""

    element: Element
    start: Node
    end: Node
    dof_indices: tuple[int, int, int, int]

    @property
    def length(self) -> float:
        """Longitud del elemento."""
        return hypot(self.end.x - self.start.x, self.end.y - self.start.y)

    @property
    def direction_cosines(self) -> tuple[float, float]:
        """Cosenos directores del elemento en X e Y."""
        length = self.length
        if length <= 0.0:
            raise TrussValidationError(
                f"El elemento {self.element.name!r} tiene longitud cero."
            )
        return (
            (self.end.x - self.start.x) / length,
            (self.end.y - self.start.y) / length,
        )

    @property
    def local_stiffness_matrix(self) -> ArrayFloat:
        """Matriz de rigidez local del elemento."""
        factor = self.element.area * self.element.elastic_modulus / self.length
        return factor * np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=float)

    @property
    def transformation_matrix(self) -> ArrayFloat:
        """Matriz de transformacion de desplazamientos globales a locales."""
        lx, ly = self.direction_cosines
        return np.array([[lx, ly, 0.0, 0.0], [0.0, 0.0, lx, ly]], dtype=float)

    @property
    def global_stiffness_matrix(self) -> ArrayFloat:
        """Matriz de rigidez del elemento en coordenadas globales."""
        transformation = self.transformation_matrix
        return transformation.T @ self.local_stiffness_matrix @ transformation

    def axial_force(self, global_displacements: ArrayFloat) -> float:
        """Calcula la fuerza axial del elemento.

        La fuerza positiva indica traccion y la negativa compresion. El metodo
        usa vectores 1D para evitar conversiones ambiguas de arrays de NumPy a
        escalares, que era el problema de la funcion ``TensionCompresion``.

        Args:
            global_displacements: Vector global de desplazamientos ordenado
                segun el mapeo interno de grados de libertad.

        Returns:
            Fuerza axial del extremo final del elemento.
        """
        displacements = np.asarray(global_displacements, dtype=float).reshape(-1)
        max_index = max(self.dof_indices)
        if max_index >= displacements.size:
            raise TrussAnalysisError(
                "El vector de desplazamientos no contiene todos los grados "
                f"de libertad requeridos por {self.element.name!r}."
            )

        element_displacements = displacements[np.array(self.dof_indices, dtype=int)]
        local_displacements = self.transformation_matrix @ element_displacements
        local_forces = self.local_stiffness_matrix @ local_displacements
        return float(local_forces[1])


@dataclass(frozen=True)
class AnalysisResult:
    """Resultado completo del analisis matricial."""

    member_names: tuple[str, ...]
    free_dofs: tuple[DegreeOfFreedom, ...]
    constrained_dofs: tuple[DegreeOfFreedom, ...]
    dof_order: tuple[DegreeOfFreedom, ...]
    stiffness_matrix: ArrayFloat
    k_ff: ArrayFloat
    k_fc: ArrayFloat
    k_cf: ArrayFloat
    k_cc: ArrayFloat
    known_forces: ArrayFloat
    known_displacements: ArrayFloat
    unknown_displacements: ArrayFloat
    reactions: ArrayFloat
    global_forces: ArrayFloat
    global_displacements: ArrayFloat
    internal_forces: ArrayFloat

    def internal_forces_rounded(self, decimals: int = 2) -> list[float]:
        """Devuelve las fuerzas internas redondeadas como el script original."""
        return np.round(self.internal_forces, decimals).astype(float).tolist()

    def displacement_by_dof(self) -> dict[DegreeOfFreedom, float]:
        """Devuelve desplazamientos globales indexados por grado de libertad."""
        return {
            dof: float(value)
            for dof, value in zip(
                self.dof_order,
                self.global_displacements,
                strict=True,
            )
        }

    def reaction_by_dof(self) -> dict[DegreeOfFreedom, float]:
        """Devuelve reacciones indexadas por grado de libertad restringido."""
        return {
            dof: float(value)
            for dof, value in zip(
                self.constrained_dofs,
                self.reactions,
                strict=True,
            )
        }

    def format_summary(self) -> str:
        """Genera un reporte legible con unidades de presentacion."""
        from analisis_armadura.presentation import format_detailed_report

        return format_detailed_report(self)

    @staticmethod
    def _format_dof(dof: DegreeOfFreedom) -> str:
        """Formatea un grado de libertad como ``Nodo-Direccion``."""
        node, direction = dof
        return f"{node}-{direction.value}"


class MatrixTrussAnalyzer:
    """Analiza armaduras planas mediante el metodo matricial de rigidez."""

    def __init__(self, model: TrussModel) -> None:
        """Inicializa el analizador y valida el modelo.

        Args:
            model: Modelo de armadura plana.
        """
        self.model = model
        self.nodes_by_name = self._build_node_lookup(model.nodes)
        self.mapping = self._build_dof_mapping(model.nodes)
        self._validate_model()
        self.members = self._build_members()
        self.global_stiffness_matrix = self.assemble_global_stiffness()

    def solve(self) -> AnalysisResult:
        """Resuelve desplazamientos, reacciones y fuerzas internas.

        Returns:
            Resultado completo del analisis.

        Raises:
            TrussAnalysisError: Si la matriz de rigidez libre es singular o
                numericamente irresoluble.
        """
        free_count = self.mapping.free_count
        total_count = self.mapping.total_count
        stiffness = self.global_stiffness_matrix

        k_ff = stiffness[:free_count, :free_count]
        k_fc = stiffness[:free_count, free_count:total_count]
        k_cf = stiffness[free_count:total_count, :free_count]
        k_cc = stiffness[free_count:total_count, free_count:total_count]

        full_loads = self._build_full_load_vector()
        known_forces = full_loads[:free_count]
        constrained_loads = full_loads[free_count:total_count]
        known_displacements = self._build_known_displacement_vector()

        try:
            unknown_displacements = np.linalg.solve(
                k_ff,
                known_forces - k_fc @ known_displacements,
            )
        except np.linalg.LinAlgError as exc:
            raise TrussAnalysisError(
                "La submatriz de rigidez libre es singular. Revise apoyos, "
                "conectividad y mecanismos de la armadura."
            ) from exc

        reactions = (
            k_cf @ unknown_displacements
            + k_cc @ known_displacements
            - constrained_loads
        )
        global_forces = np.concatenate((known_forces, reactions))
        global_displacements = np.concatenate(
            (unknown_displacements, known_displacements)
        )
        internal_forces = self._calculate_internal_forces(global_displacements)

        return AnalysisResult(
            member_names=tuple(member.element.name for member in self.members),
            free_dofs=self.mapping.free_dofs,
            constrained_dofs=self.mapping.constrained_dofs,
            dof_order=self.mapping.dof_order,
            stiffness_matrix=stiffness.copy(),
            k_ff=k_ff.copy(),
            k_fc=k_fc.copy(),
            k_cf=k_cf.copy(),
            k_cc=k_cc.copy(),
            known_forces=known_forces.copy(),
            known_displacements=known_displacements.copy(),
            unknown_displacements=unknown_displacements.copy(),
            reactions=reactions.copy(),
            global_forces=global_forces.copy(),
            global_displacements=global_displacements.copy(),
            internal_forces=internal_forces.copy(),
        )

    def assemble_global_stiffness(self) -> ArrayFloat:
        """Ensambla la matriz de rigidez global de la armadura."""
        stiffness = np.zeros(
            (self.mapping.total_count, self.mapping.total_count),
            dtype=float,
        )
        for member in self.members:
            indices = np.array(member.dof_indices, dtype=int)
            stiffness[np.ix_(indices, indices)] += member.global_stiffness_matrix
        return stiffness

    def _build_node_lookup(self, nodes: tuple[Node, ...]) -> dict[str, Node]:
        """Crea un diccionario de nodos y detecta identificadores repetidos."""
        lookup: dict[str, Node] = {}
        for node in nodes:
            if node.name in lookup:
                raise TrussValidationError(f"Nodo duplicado: {node.name!r}.")
            lookup[node.name] = node
        return lookup

    def _build_dof_mapping(self, nodes: tuple[Node, ...]) -> DofMapping:
        """Ordena grados libres primero y restringidos al final."""
        free_dofs: list[DegreeOfFreedom] = []
        constrained_groups: list[tuple[DegreeOfFreedom, ...]] = []

        for node in nodes:
            constrained = set(node.support.constrained_directions())
            node_constrained: list[DegreeOfFreedom] = []
            for direction in (Direction.X, Direction.Y):
                dof = (node.name, direction)
                if direction in constrained:
                    node_constrained.append(dof)
                else:
                    free_dofs.append(dof)
            if node_constrained:
                constrained_groups.append(tuple(node_constrained))

        constrained_dofs = tuple(
            dof for group in reversed(constrained_groups) for dof in group
        )
        dof_order = tuple(free_dofs) + constrained_dofs
        dof_to_index = {dof: index for index, dof in enumerate(dof_order)}
        return DofMapping(
            free_dofs=tuple(free_dofs),
            constrained_dofs=constrained_dofs,
            dof_order=dof_order,
            dof_to_index=dof_to_index,
        )

    def _validate_model(self) -> None:
        """Valida consistencia basica del modelo estructural."""
        if not self.model.nodes:
            raise TrussValidationError("El modelo debe contener al menos un nodo.")
        if not self.model.elements:
            raise TrussValidationError("El modelo debe contener al menos un elemento.")

        self._validate_elements()
        self._validate_loads()
        self._validate_prescribed_displacements()

    def _validate_elements(self) -> None:
        """Valida conectividad y propiedades mecanicas de elementos."""
        seen_elements: set[str] = set()
        for element in self.model.elements:
            if element.name in seen_elements:
                raise TrussValidationError(f"Elemento duplicado: {element.name!r}.")
            seen_elements.add(element.name)

            if not isfinite(element.area) or element.area <= 0.0:
                raise TrussValidationError(
                    f"El area de {element.name!r} debe ser positiva."
                )
            if not isfinite(element.elastic_modulus) or element.elastic_modulus <= 0.0:
                raise TrussValidationError(
                    f"El modulo de elasticidad de {element.name!r} debe ser positivo."
                )
            if element.start_node not in self.nodes_by_name:
                raise TrussValidationError(
                    f"{element.name!r} usa un nodo inicial inexistente: "
                    f"{element.start_node!r}."
                )
            if element.end_node not in self.nodes_by_name:
                raise TrussValidationError(
                    f"{element.name!r} usa un nodo final inexistente: "
                    f"{element.end_node!r}."
                )

            start = self.nodes_by_name[element.start_node]
            end = self.nodes_by_name[element.end_node]
            if hypot(end.x - start.x, end.y - start.y) <= 0.0:
                raise TrussValidationError(
                    f"El elemento {element.name!r} tiene longitud cero."
                )

    def _validate_loads(self) -> None:
        """Valida que las cargas apunten a nodos existentes."""
        for load in self.model.loads:
            self._validate_dof_data(load.node, load.direction, "carga")
            if not isfinite(load.magnitude):
                raise TrussValidationError(
                    f"La carga en {load.node!r}-{load.direction.value} no es finita."
                )

    def _validate_prescribed_displacements(self) -> None:
        """Valida desplazamientos conocidos en grados restringidos."""
        seen: set[DegreeOfFreedom] = set()
        constrained = set(self.mapping.constrained_dofs)
        for displacement in self.model.prescribed_displacements:
            self._validate_dof_data(
                displacement.node,
                displacement.direction,
                "desplazamiento prescrito",
            )
            dof = (displacement.node, displacement.direction)
            if dof in seen:
                raise TrussValidationError(
                    f"Desplazamiento prescrito duplicado en {dof!r}."
                )
            if dof not in constrained:
                raise TrussValidationError(
                    "Solo se permiten desplazamientos prescritos en grados "
                    f"restringidos. Dato invalido: {dof!r}."
                )
            if not isfinite(displacement.value):
                raise TrussValidationError(
                    f"El desplazamiento prescrito en {dof!r} no es finito."
                )
            seen.add(dof)

    def _validate_dof_data(
        self,
        node_name: str,
        direction: Direction,
        data_label: str,
    ) -> None:
        """Valida que un dato nodal use un nodo y direccion existentes."""
        if node_name not in self.nodes_by_name:
            raise TrussValidationError(
                f"El dato de {data_label} usa un nodo inexistente: {node_name!r}."
            )
        if (node_name, direction) not in self.mapping.dof_to_index:
            raise TrussValidationError(
                f"El dato de {data_label} usa un grado de libertad invalido: "
                f"{node_name!r}-{direction.value}."
            )

    def _build_members(self) -> tuple[TrussMember, ...]:
        """Construye los miembros de calculo a partir del modelo."""
        members: list[TrussMember] = []
        for element in self.model.elements:
            start = self.nodes_by_name[element.start_node]
            end = self.nodes_by_name[element.end_node]
            dof_indices = (
                self.mapping.dof_to_index[(start.name, Direction.X)],
                self.mapping.dof_to_index[(start.name, Direction.Y)],
                self.mapping.dof_to_index[(end.name, Direction.X)],
                self.mapping.dof_to_index[(end.name, Direction.Y)],
            )
            members.append(TrussMember(element, start, end, dof_indices))
        return tuple(members)

    def _build_full_load_vector(self) -> ArrayFloat:
        """Construye el vector global de cargas externas."""
        loads = np.zeros(self.mapping.total_count, dtype=float)
        for load in self.model.loads:
            index = self.mapping.dof_to_index[(load.node, load.direction)]
            loads[index] += load.magnitude
        return loads

    def _build_known_displacement_vector(self) -> ArrayFloat:
        """Construye el vector de desplazamientos conocidos."""
        displacements = np.zeros(len(self.mapping.constrained_dofs), dtype=float)
        for prescribed in self.model.prescribed_displacements:
            index = self.mapping.dof_to_index[(prescribed.node, prescribed.direction)]
            local_index = index - self.mapping.free_count
            displacements[local_index] = prescribed.value
        return displacements

    def _calculate_internal_forces(
        self,
        global_displacements: ArrayFloat,
    ) -> ArrayFloat:
        """Calcula fuerzas internas de todos los elementos."""
        return np.array(
            [member.axial_force(global_displacements) for member in self.members],
            dtype=float,
        )

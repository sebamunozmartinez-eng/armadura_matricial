# armadura_matricial

`armadura_matricial` es un proyecto en Python para analizar armaduras planas 2D mediante el Método Matricial de Rigidez.

Nació a partir de una tarea universitaria de análisis estructural y evolucionó hacia una pieza de portafolio profesional: un solver modular, testeado, documentado y con visualización gráfica de resultados.

El proyecto combina fundamentos de ingeniería estructural con buenas prácticas de desarrollo de software.

## Capturas de resultados

### Caso base

![Caso base deformado](outputs/figures/caso_base_deformada.png)

### Armadura Warren

![Armadura Warren deformada](outputs/figures/warren_deformada.png)

## Características principales

- Solver matricial para armaduras planas 2D.
- Ensamble de la matriz de rigidez global con NumPy.
- Resolución numérica con `np.linalg.solve`, evitando invertir matrices explícitamente.
- Cálculo de desplazamientos nodales, reacciones y fuerzas axiales internas.
- Diagnósticos estructurales previos al análisis:
  - nodos aislados,
  - elementos con longitud cero,
  - apoyos insuficientes,
  - conteo de grados de libertad libres y restringidos.
- Visualización 2D de la geometría original y la deformada amplificada.
- Coloreado de barras por estado interno:
  - tensión,
  - compresión,
  - neutro.
- Representación gráfica de cargas y apoyos.
- Ejemplos interactivos desde consola.
- Arquitectura modular basada en `src`, `tests` y `examples`.
- Pruebas automatizadas con Pytest.
- Calidad de código con Ruff.
- Preparado para control de versiones con Git y publicación en GitHub.

## Por qué este proyecto es relevante

Este repositorio muestra una evolución completa desde un script académico hacia una herramienta técnica mantenible.

Desde el punto de vista estructural, implementa el flujo esencial del análisis matricial de armaduras: definición de nodos, elementos, apoyos, cargas, ensamble, solución del sistema y recuperación de fuerzas internas.

Desde el punto de vista de software, separa responsabilidades, incorpora pruebas de regresión, usa type hints cuando aportan claridad y agrega una capa de visualización sin mezclarla con el solver numérico.

## Estructura del proyecto

```text
armadura_matricial/
|-- src/
|   `-- analisis_armadura/
|       |-- __init__.py
|       |-- __main__.py
|       |-- cli.py
|       |-- data.py
|       |-- diagnostics.py
|       |-- interactive.py
|       |-- models.py
|       |-- presentation.py
|       |-- solver.py
|       `-- visualization.py
|-- tests/
|   |-- conftest.py
|   |-- test_diagnostics.py
|   |-- test_interactive.py
|   |-- test_solver.py
|   `-- test_visualization.py
|-- examples/
|   |-- analisis_interactivo.py
|   |-- caso_base.py
|   |-- graficar_caso_base.py
|   `-- graficar_warren.py
|-- outputs/
|   `-- figures/
|       |-- caso_base_deformada.png
|       `-- warren_deformada.png
|-- Analisis_Armadura.py
|-- README.md
|-- requirements.txt
|-- pyproject.toml
`-- .gitignore
```

## Instalación

### 1. Clonar el repositorio

```powershell
git clone https://github.com/USUARIO/armadura_matricial.git
cd armadura_matricial
```

Reemplaza `USUARIO` por el usuario u organización donde publiques el repositorio.

### 2. Crear un entorno virtual

```powershell
py -3 -m venv .venv
```

### 3. Activar el entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación por política de ejecución, también puedes usar directamente el intérprete del entorno:

```powershell
.\.venv\Scripts\python -m pip install --upgrade pip
```

### 4. Instalar dependencias de uso

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 5. Instalar el paquete en modo editable con dependencias de desarrollo

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Esto permite importar el paquete localmente y ejecutar herramientas como `pytest` y `ruff`.

## Ejemplos de uso

### Ejecutar el caso principal

```powershell
py Analisis_Armadura.py
```

Salida esperada:

```text
Analisis completado correctamente
Numero de nodos: 8
Numero de elementos: 15
Desplazamiento maximo: 1.624 cm
Numero de reacciones calculadas: 4
```

### Ejecutar el ejemplo detallado

```powershell
py examples\caso_base.py
```

### Ejecutar el menú interactivo

```powershell
py examples\analisis_interactivo.py
```

Casos disponibles:

- Caso base con factor de carga.
- Armadura triangular simple.
- Armadura Warren de dos paneles.
- Entrada manual completa de nodos, elementos, cargas y desplazamientos prescritos.

### Generar visualizaciones

```powershell
py examples\graficar_caso_base.py
py examples\graficar_warren.py
```

Las figuras se guardan automáticamente en:

```text
outputs/figures/
```

## Uso desde Python

```python
from analisis_armadura import (
    MatrixTrussAnalyzer,
    create_default_model,
    diagnose_model,
    plot_truss,
)
from analisis_armadura.presentation import (
    format_detailed_report,
    format_diagnostics_report,
)

model = create_default_model()

diagnostics = diagnose_model(model)
print(format_diagnostics_report(diagnostics))

result = MatrixTrussAnalyzer(model).solve()
print(format_detailed_report(result))

plot_truss(
    model,
    result,
    deformation_scale=100.0,
    output_path="outputs/figures/caso_base_deformada.png",
)
```

## Calidad del software

El proyecto aplica prácticas pensadas para mantener el código claro, extensible y verificable:

- Estructura de paquete con `src/`.
- Separación entre:
  - modelos de datos,
  - solver numérico,
  - diagnósticos,
  - presentación,
  - visualización,
  - ejemplos ejecutables.
- Pruebas automatizadas con Pytest.
- Revisión de estilo y linting con Ruff.
- Type hints en las APIs principales.
- Objetos de dominio con `dataclass`.
- Validaciones explícitas para datos estructurales inválidos.
- Ejemplos reproducibles desde consola.
- Figuras generadas automáticamente para documentación y portafolio.

## Validación actual

Estado más reciente del proyecto:

```text
pytest: 18 passed
ruff check: All checks passed
ruff format --check: 20 files already formatted
```

Comandos usados:

```powershell
py -m pytest
ruff check .
ruff format --check .
```

## Detalle técnico del método matricial

Cada barra se modela como un elemento axial con dos grados de libertad por nodo: `DX` y `DY`.

Para cada elemento se calcula:

1. Longitud `L`.
2. Cosenos directores.
3. Matriz de rigidez local.
4. Matriz de transformación.
5. Matriz de rigidez del elemento en coordenadas globales.

La matriz global `K` se ensambla acumulando la contribución de cada barra sobre sus grados de libertad asociados.

El sistema se particiona separando grados de libertad libres y restringidos:

```text
[Kff Kfc] [Df] = [Ff]
[Kcf Kcc] [Dc]   [Fc]
```

Con desplazamientos prescritos `Dc`, el sistema principal se resuelve como:

```text
Df = solve(Kff, Ff - Kfc @ Dc)
```

Las reacciones se obtienen con:

```text
R = Kcf @ Df + Kcc @ Dc - F_c_aplicadas
```

Las fuerzas internas se calculan transformando los desplazamientos globales del elemento hacia su sistema local. Una fuerza positiva indica tensión y una fuerza negativa indica compresión.

## Diagnósticos estructurales

Antes de resolver, el proyecto puede revisar condiciones básicas del modelo:

```python
from analisis_armadura import create_default_model, diagnose_model
from analisis_armadura.presentation import format_diagnostics_report

model = create_default_model()
diagnostics = diagnose_model(model)

print(format_diagnostics_report(diagnostics))
```

El diagnóstico reporta:

- número de nodos,
- número de elementos,
- grados de libertad totales,
- grados de libertad libres,
- grados de libertad restringidos,
- nodos aislados,
- elementos de longitud cero,
- apoyos insuficientes.

Estos diagnósticos no reemplazan una revisión estructural completa, pero ayudan a detectar errores frecuentes de modelado antes de resolver el sistema.

## Visualización

La visualización usa Matplotlib y se mantiene separada del solver.

La deformada se dibuja con un factor de amplificación configurable:

```python
plot_truss(
    model,
    result,
    deformation_scale=100.0,
    output_path="outputs/figures/caso_base_deformada.png",
)
```

El factor `deformation_scale` solo afecta la representación gráfica. Los desplazamientos reales almacenados en `result.global_displacements` no se modifican.

## Futuras mejoras

Hoja de ruta propuesta:

- Exportación de modelos y resultados a JSON/CSV.
- Generación automática de reportes técnicos en Markdown o HTML.
- Nuevos tipos de estructuras de ejemplo.
- Comparación entre distintas configuraciones de carga.
- Visualizaciones más avanzadas:
  - mapas de magnitud,
  - factores de escala automáticos,
  - exportación de figuras en SVG/PDF.
- Integración opcional con notebooks para uso docente.

## Licencia recomendada

Para un proyecto educativo y de portafolio, se recomienda usar la licencia MIT.

La licencia MIT es simple, ampliamente reconocida y permite que otras personas estudien, usen y adapten el código con pocas restricciones, manteniendo la atribución al autor original.

Si el proyecto se publica en GitHub, conviene agregar un archivo `LICENSE` con el texto oficial de la licencia MIT.

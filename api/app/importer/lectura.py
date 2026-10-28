"""Lectura del libro con `openpyxl` (D-016, sin pandas).

Dos decisiones importantes:

- **Los valores se vuelven JSON-safe al leer** (`time` -> `"07:00:00"`, `date` ->
  ISO). Así el mismo `HojaCruda` alimenta el preview, el PATCH de correcciones y la
  confirmación: no hay tres lecturas distintas del archivo que puedan divergir, y el
  `resumen` guardado en `importacion` es el registro fiel de lo que se leyó.
- **Las filas conservan su número de Excel**. `FILAS_VACIAS_IGNORADAS` y los hallazgos
  por fila tienen que apuntar a la fila que el usuario ve en Excel, no a un índice
  interno.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from io import BytesIO
from typing import Any, BinaryIO
from zipfile import BadZipFile

import openpyxl

from app.importer.coercion import sin_acentos

#: Encabezados canónicos por hoja: contrato del lector y de la plantilla descargable.
ENCABEZADOS: dict[str, tuple[str, ...]] = {
    "Leeme": ("Concepto", "Descripción"),
    "Bloques": ("bloque_id", "inicio", "fin"),
    "Cursos": ("curso_id", "nombre", "estudiantes"),
    "Docentes": ("docente_id", "nombre", "max_sesiones_semana"),
    "Asignaturas docentes": ("asignatura", "docente_id", "habilitado"),
    "Carga": (
        "curso_id",
        "asignatura",
        "docente_principal_id",
        "sesiones_semana",
        "tipo_salon_requerido",
    ),
    "Salones": ("salon_id", "nombre", "tipo", "capacidad"),
    "Disponibilidad": ("docente_id", "dia", "bloque_id", "disponible"),
    "Cambio": ("docente_id", "dia", "bloque_id", "disponible_nuevo", "motivo"),
}

#: Hojas sin las cuales no se puede importar nada.
OBLIGATORIAS: tuple[str, ...] = (
    "Bloques",
    "Cursos",
    "Docentes",
    "Asignaturas docentes",
    "Carga",
    "Salones",
    "Disponibilidad",
)

#: Orden de Excel: se usa para ordenar hallazgos de forma estable.
ORDEN_HOJAS: tuple[str, ...] = tuple(ENCABEZADOS)


class ArchivoInvalido(ValueError):
    """El archivo no es un .xlsx que `openpyxl` pueda abrir."""


@dataclass(frozen=True, slots=True)
class FilaCruda:
    """Fila de Excel con su número real (1 = fila del encabezado)."""

    numero: int
    celdas: tuple[Any, ...]

    @property
    def vacia(self) -> bool:
        """Totalmente nula: es lo que `FILAS_VACIAS_IGNORADAS` ignora."""
        return all(celda is None or (isinstance(celda, str) and not celda) for celda in self.celdas)


@dataclass(frozen=True, slots=True)
class HojaCruda:
    """Hoja leída: encabezado de la fila 1 y el resto de filas con su número."""

    nombre: str
    encabezado: tuple[str, ...]
    filas: tuple[FilaCruda, ...]

    def indice(self, columna: str) -> int | None:
        """Índice del encabezado, comparando sin acentos ni mayúsculas."""
        buscado = sin_acentos(columna)
        for posicion, cabecera in enumerate(self.encabezado):
            if sin_acentos(cabecera) == buscado:
                return posicion
        return None

    def valor(self, fila: FilaCruda, columna: str) -> Any:
        """Valor de `columna` en `fila`; `None` si la columna no existe o falta la celda."""
        posicion = self.indice(columna)
        if posicion is None or posicion >= len(fila.celdas):
            return None
        return fila.celdas[posicion]

    @property
    def filas_datos(self) -> tuple[FilaCruda, ...]:
        return tuple(fila for fila in self.filas if not fila.vacia)

    @property
    def filas_vacias(self) -> int:
        return sum(1 for fila in self.filas if fila.vacia)


def _json_seguro(valor: Any) -> Any:
    """Tipo de celda -> tipo JSON. Mantiene floats como floats (la trampa 1)."""
    if valor is None:
        return None
    if isinstance(valor, str):
        limpio = valor.strip()
        return limpio or None
    if isinstance(valor, bool | int | float):
        return valor
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, datetime):
        return valor.isoformat(sep=" ")
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, time):
        return valor.strftime("%H:%M:%S")
    return str(valor).strip() or None


def leer_libro(origen: bytes | BinaryIO) -> dict[str, HojaCruda]:
    """Lee todas las hojas del libro. Levanta `ArchivoInvalido` si no es un .xlsx."""
    flujo = BytesIO(origen) if isinstance(origen, bytes) else origen
    try:
        libro = openpyxl.load_workbook(flujo, data_only=True, read_only=False)
    except (BadZipFile, KeyError, OSError, ValueError) as exc:
        raise ArchivoInvalido("El archivo no es un Excel .xlsx válido.") from exc

    hojas: dict[str, HojaCruda] = {}
    for hoja in libro.worksheets:
        crudas = [
            FilaCruda(
                numero=numero,
                celdas=tuple(_json_seguro(celda) for celda in valores),
            )
            for numero, valores in enumerate(hoja.iter_rows(values_only=True), start=1)
        ]
        encabezado: tuple[str, ...] = ()
        filas = crudas
        if crudas:
            encabezado = tuple(
                "" if celda is None else str(celda) for celda in crudas[0].celdas
            )
            filas = crudas[1:]
        hojas[hoja.title] = HojaCruda(nombre=hoja.title, encabezado=encabezado, filas=tuple(filas))
    libro.close()
    return hojas


def buscar_hoja(hojas: dict[str, HojaCruda], nombre: str) -> HojaCruda | None:
    """Busca una hoja por su nombre canónico, tolerando acentos y mayúsculas."""
    buscado = sin_acentos(nombre)
    for clave, hoja in hojas.items():
        if sin_acentos(clave) == buscado:
            return hoja
    return None


def a_json(hoja: HojaCruda) -> dict[str, Any]:
    """`HojaCruda` -> dict serializable (lo que se guarda en `importacion.resumen`)."""
    return {
        "nombre": hoja.nombre,
        "encabezado": list(hoja.encabezado),
        "filas": [{"numero": fila.numero, "celdas": list(fila.celdas)} for fila in hoja.filas],
    }


def desde_json(datos: dict[str, Any]) -> HojaCruda:
    """Vuelta de `a_json`. El valor `None` de una celda sigue siendo `None`."""
    return HojaCruda(
        nombre=str(datos.get("nombre") or ""),
        encabezado=tuple(str(celda or "") for celda in datos.get("encabezado") or ()),
        filas=tuple(
            FilaCruda(numero=int(fila["numero"]), celdas=tuple(fila["celdas"]))
            for fila in datos.get("filas") or ()
        ),
    )


def hojas_a_json(hojas: dict[str, HojaCruda]) -> dict[str, Any]:
    return {clave: a_json(hoja) for clave, hoja in hojas.items()}


def hojas_desde_json(datos: dict[str, Any]) -> dict[str, HojaCruda]:
    return {clave: desde_json(valor) for clave, valor in datos.items()}

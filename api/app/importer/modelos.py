"""Modelos del importador: hallazgos, plan de importación y preview.

Las filas del Excel se convierten en **referencias por clave natural** (`codigo`,
`nombre`), no en entidades de dominio con FK: en el preview todavía no existen los
UUID de la DB. `app.importer.confirmacion` traduce esas referencias a entidades
reales y hace el upsert (D-009).

`PreviewImportacion.a_json()` es a la vez la respuesta de la API y lo que se guarda en
`importacion.resumen`: una sola representación, sin dos verdades que se desincronicen.
"""

from dataclasses import dataclass, field
from datetime import time
from typing import Any

from app.domain.enums import Gravedad, TipoBloque
from app.importer.lectura import HojaCruda, hojas_a_json, hojas_desde_json
from app.validator.diagnostico import Diagnostico

#: Códigos que NO impiden importar una fila: reportan un problema de datos que la
#: confirmación puede escribir igual (el solver y el validador lo tratan después).
NO_BLOQUEANTES: frozenset[str] = frozenset(
    {
        "DURACION_BLOQUE_INCONSISTENTE",
        "SIN_DESCANSOS",
        "FILAS_VACIAS_IGNORADAS",
        "DOCENTE_SOBRECARGA",
        "CURSO_SIN_ESTUDIANTES",
        "DOCENTE_SIN_MAXIMO",
        "DIA_NO_RECONOCIDO",
    }
)


@dataclass(frozen=True, slots=True)
class Hallazgo:
    """Error o advertencia de una celda. `codigo` es estable; `mensaje` es para la UI."""

    codigo: str
    severidad: Gravedad
    mensaje: str
    hoja: str | None = None
    fila: int | None = None
    columna: str | None = None

    @property
    def bloqueante(self) -> bool:
        """La fila a la que apunta no se puede escribir hasta corregirla."""
        return self.codigo not in NO_BLOQUEANTES

    def a_json(self) -> dict[str, Any]:
        return {
            "codigo": self.codigo,
            "severidad": str(self.severidad),
            "mensaje": self.mensaje,
            "hoja": self.hoja,
            "fila": self.fila,
            "columna": self.columna,
            "bloqueante": self.bloqueante,
        }


@dataclass(frozen=True, slots=True)
class CursoImportado:
    codigo: str
    nombre: str
    grado: int
    estudiantes: int


@dataclass(frozen=True, slots=True)
class BloqueImportado:
    codigo: str
    orden: int
    inicio: time
    fin: time
    duracion_min: int
    tipo: TipoBloque = TipoBloque.clase


@dataclass(frozen=True, slots=True)
class DocenteImportado:
    codigo: str
    nombre: str
    max_sesiones_semana: int


@dataclass(frozen=True, slots=True)
class AsignaturaImportada:
    nombre: str
    color: str


@dataclass(frozen=True, slots=True)
class AptitudImportada:
    asignatura: str
    docente: str


@dataclass(frozen=True, slots=True)
class AsignacionImportada:
    curso: str
    asignatura: str
    docente_principal: str
    sesiones_semana: int
    tipo_recurso_requerido: str


@dataclass(frozen=True, slots=True)
class RecursoImportado:
    codigo: str
    nombre: str
    tipo_recurso: str
    capacidad: int
    curso_titular: str | None = None


@dataclass(frozen=True, slots=True)
class BloqueoImportado:
    docente: str
    dia: int
    bloque: str


@dataclass(frozen=True, slots=True)
class EscenarioCambioImportado:
    docente: str
    dia: int
    bloque: str
    disponible_nuevo: bool
    motivo: str | None = None


@dataclass(frozen=True, slots=True)
class EscenarioImportado:
    nombre: str
    descripcion: str
    cambios: tuple[EscenarioCambioImportado, ...] = ()


@dataclass(frozen=True, slots=True)
class PreviewImportacion:
    """Resultado completo y serializable de analizar un libro."""

    archivo_nombre: str
    hojas: dict[str, HojaCruda]
    conteos: dict[str, int] = field(default_factory=dict)
    hallazgos: tuple[Hallazgo, ...] = ()
    diagnosticos: tuple[Diagnostico, ...] = ()
    cursos: tuple[CursoImportado, ...] = ()
    bloques: tuple[BloqueImportado, ...] = ()
    docentes: tuple[DocenteImportado, ...] = ()
    asignaturas: tuple[AsignaturaImportada, ...] = ()
    aptitudes: tuple[AptitudImportada, ...] = ()
    asignaciones: tuple[AsignacionImportada, ...] = ()
    tipos_recurso: tuple[str, ...] = ()
    recursos: tuple[RecursoImportado, ...] = ()
    bloqueos: tuple[BloqueoImportado, ...] = ()
    escenario: EscenarioImportado | None = None

    @property
    def errores(self) -> tuple[Hallazgo, ...]:
        return tuple(h for h in self.hallazgos if h.severidad == Gravedad.error)

    @property
    def advertencias(self) -> tuple[Hallazgo, ...]:
        return tuple(h for h in self.hallazgos if h.severidad == Gravedad.advertencia)

    @property
    def grados(self) -> tuple[int, ...]:
        return tuple(sorted({curso.grado for curso in self.cursos}))

    @property
    def confirmable(self) -> bool:
        """Hay algo que escribir. Los hallazgos bloqueantes solo omiten su fila."""
        return bool(
            self.cursos
            or self.bloques
            or self.docentes
            or self.asignaturas
            or self.asignaciones
        )

    def a_json(self) -> dict[str, Any]:
        return {
            "archivo_nombre": self.archivo_nombre,
            "conteos": dict(self.conteos),
            "hallazgos": [hallazgo.a_json() for hallazgo in self.hallazgos],
            "diagnosticos": [diagnostico.a_json() for diagnostico in self.diagnosticos],
            "errores": len(self.errores),
            "advertencias": len(self.advertencias),
            "codigos": sorted({hallazgo.codigo for hallazgo in self.hallazgos}),
            "confirmable": self.confirmable,
            "escenario": None
            if self.escenario is None
            else {
                "nombre": self.escenario.nombre,
                "descripcion": self.escenario.descripcion,
                "cambios": len(self.escenario.cambios),
            },
            "hojas": hojas_a_json(self.hojas),
        }


def hojas_de_preview(resumen: dict[str, Any]) -> dict[str, HojaCruda]:
    """Recupera las hojas crudas guardadas en `importacion.resumen`."""
    return hojas_desde_json(resumen.get("hojas") or {})


@dataclass(frozen=True, slots=True)
class ConfirmaImportacion:
    """Qué escribió la confirmación, por entidad."""

    creados: dict[str, int] = field(default_factory=dict)
    actualizados: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.creados.values()) + sum(self.actualizados.values())

    def a_json(self) -> dict[str, Any]:
        return {
            "creados": dict(self.creados),
            "actualizados": dict(self.actualizados),
            "total": self.total,
        }

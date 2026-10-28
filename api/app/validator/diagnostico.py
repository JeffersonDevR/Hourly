"""`diagnosticar_carga`: aritmética de demanda docente. Puro, sin DB ni IA.

Es el diagnóstico que corre ANTES de generar (D-003, D-007): con el Excel real dice
"D4 demanda 28 y su máximo es 24", que es la causa real de que `modo_docente=principal`
sea INFACTIBLE. No se persiste como `conflicto` (D-007): `conflicto.horario_version_id`
es NOT NULL y este diagnóstico existe sin versión.

Fase 3 agrega `validar()` al mismo paquete y reutiliza este módulo; por eso la entrada
es `EstadoHorario` y no filas de la DB.
"""

import uuid
from dataclasses import dataclass

from app.domain.enums import Gravedad, TipoBloque
from app.validator.estado import EstadoHorario

#: Un día por cada `dia` posible (1=lunes … 5=viernes, DOMAIN.md).
DIAS_SEMANA = 5

#: Demanda del docente principal > `max_sesiones_semana` (DOMAIN.md, gravedad error).
DOCENTE_SOBRECARGA = "DOCENTE_SOBRECARGA"
#: Demanda > franjas de clase libres del docente (bloqueos y escenario incluidos).
DOCENTE_SIN_HOLGURA = "DOCENTE_SIN_HOLGURA"
#: Asignatura con demanda y una sola (o ninguna) aptitud: sin margen de reasignación.
ASIGNATURA_UNICO_DOCENTE = "ASIGNATURA_UNICO_DOCENTE"


@dataclass(frozen=True, slots=True)
class Diagnostico:
    """Hallazgo aritmético sobre la carga. `codigo` es estable y sin acentos."""

    codigo: str
    gravedad: Gravedad
    mensaje: str
    docente_codigo: str | None = None
    docente_nombre: str | None = None
    asignatura: str | None = None
    demanda: int | None = None
    maximo: int | None = None
    franjas: int | None = None

    def a_json(self) -> dict[str, object]:
        """Forma serializable: el preview de la API devuelve exactamente esto."""
        return {
            "codigo": self.codigo,
            "gravedad": str(self.gravedad),
            "mensaje": self.mensaje,
            "docente_codigo": self.docente_codigo,
            "docente_nombre": self.docente_nombre,
            "asignatura": self.asignatura,
            "demanda": self.demanda,
            "maximo": self.maximo,
            "franjas": self.franjas,
        }


def diagnosticar_carga(estado: EstadoHorario) -> list[Diagnostico]:
    """Demanda por docente vs. máximo y vs. franjas, más asignaturas sin margen.

    Args:
        estado: horario en memoria. Solo se leen `docentes`, `bloques`, `asignaturas`,
            `aptitudes`, `asignaciones`, `bloqueos` y `escenario_cambios`.

    Returns:
        Diagnósticos ordenados de forma determinista (por docente, luego por código).
        Lista vacía si no hay nada que reportar.
    """
    bloques_clase = {bloque.id for bloque in estado.bloques if bloque.tipo == TipoBloque.clase}
    franjas_base = len(bloques_clase) * DIAS_SEMANA

    #: Franjas (dia, bloque) que el docente no puede usar, sin doble conteo.
    ocupadas: dict[uuid.UUID, set[tuple[int, uuid.UUID]]] = {}
    for bloqueo in estado.bloqueos:
        if bloqueo.bloque_id in bloques_clase:
            ocupadas.setdefault(bloqueo.docente_id, set()).add((bloqueo.dia, bloqueo.bloque_id))
    for cambio in estado.escenario_cambios:
        if not cambio.disponible_nuevo and cambio.bloque_id in bloques_clase:
            ocupadas.setdefault(cambio.docente_id, set()).add((cambio.dia, cambio.bloque_id))

    demanda: dict[uuid.UUID, int] = {}
    for asignacion in estado.asignaciones:
        actual = demanda.get(asignacion.docente_principal_id, 0)
        demanda[asignacion.docente_principal_id] = actual + asignacion.sesiones_semana

    diagnosticos: list[Diagnostico] = []
    for docente in estado.docentes:
        carga = demanda.get(docente.id, 0)
        maximo = docente.max_sesiones_semana
        if carga > maximo:
            diagnosticos.append(
                Diagnostico(
                    codigo=DOCENTE_SOBRECARGA,
                    gravedad=Gravedad.error,
                    mensaje=(
                        f"{docente.codigo} ({docente.nombre}): demanda {carga} sesiones "
                        f"> máximo {maximo}."
                    ),
                    docente_codigo=docente.codigo,
                    docente_nombre=docente.nombre,
                    demanda=carga,
                    maximo=maximo,
                )
            )
        franjas = franjas_base - len(ocupadas.get(docente.id, ()))
        if carga > franjas:
            diagnosticos.append(
                Diagnostico(
                    codigo=DOCENTE_SIN_HOLGURA,
                    gravedad=Gravedad.error,
                    mensaje=(
                        f"{docente.codigo} ({docente.nombre}): demanda {carga} sesiones "
                        f"> {franjas} franjas disponibles."
                    ),
                    docente_codigo=docente.codigo,
                    docente_nombre=docente.nombre,
                    demanda=carga,
                    franjas=franjas,
                )
            )

    habilitados: dict[uuid.UUID, set[uuid.UUID]] = {}
    for aptitud in estado.aptitudes:
        habilitados.setdefault(aptitud.asignatura_id, set()).add(aptitud.docente_id)

    nombres = {asignatura.id: asignatura.nombre for asignatura in estado.asignaturas}
    demandadas = {asignacion.asignatura_id for asignacion in estado.asignaciones}
    for asignatura_id in sorted(demandadas, key=lambda clave: nombres.get(clave, "")):
        nombre = nombres.get(asignatura_id, "(asignatura desconocida)")
        posibles = habilitados.get(asignatura_id, set())
        if len(posibles) == 1:
            diagnosticos.append(
                Diagnostico(
                    codigo=ASIGNATURA_UNICO_DOCENTE,
                    gravedad=Gravedad.advertencia,
                    mensaje=f"{nombre}: un solo docente habilitado; no hay margen para reasignar.",
                    asignatura=nombre,
                )
            )
        elif not posibles:
            diagnosticos.append(
                Diagnostico(
                    codigo=ASIGNATURA_UNICO_DOCENTE,
                    gravedad=Gravedad.advertencia,
                    mensaje=f"{nombre}: ningún docente habilitado para dictarla.",
                    asignatura=nombre,
                )
            )

    diagnosticos.sort(
        key=lambda d: (d.docente_codigo or "", d.codigo, d.asignatura or "")
    )
    return diagnosticos

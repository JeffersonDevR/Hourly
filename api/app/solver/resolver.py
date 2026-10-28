"""`resolver`: de `EstadoHorario` a `Resultado`, sin DB y sin IA.

Cadena de esta fase (D-003): CP-SAT con `fijas` → asignación de aulas →
`diagnosticar_carga` si no hay solución. El paso greedy vive en `app.solver.greedy`
y devuelve propuestas, no se aplica acá: D-003 lo usa para resolver un conflicto
concreto, no para generar un horario desde cero.

Reutilización: si el estado ya trae sesiones, son `fijas` por defecto (D-008). Solo
`limpiar=True` las descarta.
"""

import uuid
from collections.abc import Iterable

from app.config import get_settings
from app.domain.enums import ModoDocente
from app.domain.horario import Escenario, Sesion
from app.solver.comun import id_sesion
from app.solver.modelo import PESO_PESADAS, PRESUPUESTO_MEJORA, resolver_cpsat
from app.solver.recursos import asignar_recursos
from app.solver.resultado import EstadoResultado, Resultado
from app.validator.diagnostico import diagnosticar_carga
from app.validator.estado import EstadoHorario

#: Versión sintética cuando el estado no trae ninguna sesión y el llamador no pasa
#: `horario_version_id`. Determinista: los ids de las sesiones generadas también.
_VERSION_SINTETICA = uuid.uuid5(uuid.NAMESPACE_URL, "hourly/solver/version")


def resolver(
    estado: EstadoHorario,
    modo_docente: ModoDocente | str = ModoDocente.habilitados,
    escenario: Escenario | uuid.UUID | None = None,
    fijas: Iterable[Sesion] | None = None,
    solo_curso_id: uuid.UUID | None = None,
    limpiar: bool = False,
    timeout_s: float | None = None,
    peso_pesadas: int = PESO_PESADAS,
    presupuesto_mejora: float | None = None,
    horario_version_id: uuid.UUID | None = None,
) -> Resultado:
    """Genera el horario completo de la semana (o de un curso).

    Args:
        estado: catálogo + carga + bloqueos + escenario + sesiones existentes.
        modo_docente: `principal` usa solo `docente_principal_id`; `habilitados` usa
            `aptitud`. Con el Excel real, `principal` es INFACTIBLE (D4 28 > 24).
        escenario: objeto o id del escenario activo. Su overlay se aplica sobre
            `disponibilidad_bloqueo` (D-005).
        fijas: sesiones que no se mueven. `None` = las sesiones existentes del estado
            (D-008). Una tupla explícita manda; `limpiar` la ignora.
        solo_curso_id: regenera solo ese curso; las sesiones de los demás se conservan.
        limpiar: descarta las sesiones existentes del alcance (lo único que las borra,
            D-008).
        timeout_s: tope de reloj de CP-SAT. `None` toma `SOLVER_TIMEOUT_S` (20 s).
        peso_pesadas: peso del objetivo blando D-006. `0` mide el modelo sin él.
        presupuesto_mejora: presupuesto determinista de mejora. `None` usa el default
            del modelo; `0` lo desactiva y deja solo el tope de reloj.
        horario_version_id: versión de las sesiones generadas. Por defecto, la de las
            sesiones existentes.

    Returns:
        `Resultado` con el plan (fijas + generadas, con aula) o el diagnóstico que
        explica la ausencia de solución.
    """
    version = horario_version_id or _version(estado)
    presupuesto = get_settings().solver_timeout_s if timeout_s is None else timeout_s
    inmoviles = _fijas_efectivas(estado, fijas, limpiar, solo_curso_id)

    plan = resolver_cpsat(
        estado,
        modo_docente=ModoDocente(modo_docente),
        escenario=escenario,
        fijas=inmoviles,
        solo_curso_id=solo_curso_id,
        timeout_s=presupuesto,
        peso_pesadas=peso_pesadas,
        presupuesto_mejora=PRESUPUESTO_MEJORA if presupuesto_mejora is None else presupuesto_mejora,
    )

    if plan.estado in (EstadoResultado.INFACTIBLE, EstadoResultado.TIMEOUT):
        # Sin incumbente: lo único honesto es la aritmética de la carga.
        return Resultado(
            estado=plan.estado,
            diagnostico=tuple(diagnosticar_carga(estado)),
        )

    asignaciones = {asignacion.id: asignacion for asignacion in estado.asignaciones}
    generadas = tuple(
        Sesion(
            horario_version_id=version,
            asignacion_carga_id=asignacion_id,
            curso_id=asignaciones[asignacion_id].curso_id,
            docente_id=docente_id,
            dia=dia,
            bloque_id=bloque_id,
            id=id_sesion(version, asignacion_id, dia, bloque_id),
        )
        for asignacion_id, docente_id, dia, bloque_id in plan.colocaciones
        if asignacion_id in asignaciones
    )

    sesiones, diagnosticos = asignar_recursos(estado, (*inmoviles, *generadas))
    return Resultado(
        estado=plan.estado,
        sesiones=sesiones,
        diagnostico=diagnosticos,
        objetivo=plan.objetivo,
    )


def _version(estado: EstadoHorario) -> uuid.UUID:
    if estado.sesiones:
        return estado.sesiones[0].horario_version_id
    return _VERSION_SINTETICA


def _fijas_efectivas(
    estado: EstadoHorario,
    fijas: Iterable[Sesion] | None,
    limpiar: bool,
    solo_curso_id: uuid.UUID | None,
) -> tuple[Sesion, ...]:
    """Sesiones que el modelo no puede mover (D-008).

    Con `solo_curso_id`, las sesiones de los otros cursos se conservan aunque
    `limpiar=True`: regenerar un curso no puede borrar el trabajo de los demás.
    """
    if solo_curso_id is not None:
        propias = () if limpiar else _en_alcance(estado, fijas, solo_curso_id)
        ajenas = tuple(
            sesion for sesion in estado.sesiones if sesion.curso_id != solo_curso_id
        )
        return _sin_repetidas((*ajenas, *propias))
    if limpiar:
        return ()
    if fijas is None:
        return tuple(estado.sesiones)
    return _sin_repetidas(tuple(fijas))


def _en_alcance(
    estado: EstadoHorario, fijas: Iterable[Sesion] | None, solo_curso_id: uuid.UUID
) -> tuple[Sesion, ...]:
    origen = estado.sesiones if fijas is None else tuple(fijas)
    return tuple(sesion for sesion in origen if sesion.curso_id == solo_curso_id)


def _sin_repetidas(sesiones: tuple[Sesion, ...]) -> tuple[Sesion, ...]:
    vistas: dict[uuid.UUID, Sesion] = {}
    for sesion in sesiones:
        vistas.setdefault(sesion.id, sesion)
    return tuple(vistas.values())


__all__ = ["resolver"]

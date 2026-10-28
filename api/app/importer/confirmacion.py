"""Confirmación de una importación: escritura idempotente en una sola transacción.

D-009: todo es upsert por clave natural. Reimportar el mismo archivo no duplica ni
falla. La transacción la cierra quien llama (el router hace un único `commit()`):
este módulo solo escribe y hace `flush()`, igual que los repositorios.

Los campos que el Excel no trae (`asignatura.es_pesada`, `docente.activo`) se
conservan del registro existente: importar un archivo no debe resetear una decisión
que el usuario ya tomó en la UI.
"""

import dataclasses
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.domain.carga import AsignacionCarga, DisponibilidadBloqueo
from app.domain.catalogo import Aptitud, Asignatura, Bloque, Curso, Docente, Grado
from app.domain.enums import OrigenBloqueo
from app.domain.horario import Escenario, EscenarioCambio
from app.domain.recursos import Recurso, TipoRecurso
from app.importer.modelos import ConfirmaImportacion, PreviewImportacion
from app.models.base import utcnow
from app.repositories.base import Repositorio
from app.repositories.carga import RepositorioAsignacionCarga, RepositorioDisponibilidad
from app.repositories.catalogo import (
    RepositorioAptitud,
    RepositorioAsignatura,
    RepositorioBloque,
    RepositorioCurso,
    RepositorioDocente,
    RepositorioGrado,
)
from app.repositories.horario import RepositorioEscenario, RepositorioEscenarioCambio
from app.repositories.recursos import RepositorioRecurso, RepositorioTipoRecurso

#: Detalle del bloqueo importado: `disponibilidad_bloqueo.origen` no tiene una
#: categoría "importado" y el Excel no distingue el motivo (origen=personal).
DETALLE_BLOQUEO = "Importado de la hoja Disponibilidad"


def _para_actualizar(nueva: Any, existente: Any) -> Any:
    """Conserva `id` y `created_at`; renueva `updated_at` (merge sin perder marcas)."""
    return dataclasses.replace(
        nueva,
        id=existente.id,
        created_at=existente.created_at,
        updated_at=utcnow(),
    )


class _Contadores:
    """Cuenta creados/actualizados por entidad, en orden estable."""

    def __init__(self) -> None:
        self.creados: dict[str, int] = {}
        self.actualizados: dict[str, int] = {}

    def crear(self, entidad: str) -> None:
        self.creados[entidad] = self.creados.get(entidad, 0) + 1

    def actualizar(self, entidad: str) -> None:
        self.actualizados[entidad] = self.actualizados.get(entidad, 0) + 1

    def resultado(self) -> ConfirmaImportacion:
        return ConfirmaImportacion(creados=self.creados, actualizados=self.actualizados)


def confirmar_importacion(
    sesion: Session, preview: PreviewImportacion
) -> ConfirmaImportacion:
    """Escribe el plan del preview. No hace `commit()`; el llamador cierra la transacción.

    Args:
        sesion: sesión SQLAlchemy abierta.
        preview: plan ya validado por `analizar_libro`.

    Returns:
        Conteos de filas creadas y actualizadas por entidad.
    """
    contadores = _Contadores()
    repos = {
        "grado": RepositorioGrado(sesion),
        "curso": RepositorioCurso(sesion),
        "bloque": RepositorioBloque(sesion),
        "asignatura": RepositorioAsignatura(sesion),
        "docente": RepositorioDocente(sesion),
        "aptitud": RepositorioAptitud(sesion),
        "tipo_recurso": RepositorioTipoRecurso(sesion),
        "recurso": RepositorioRecurso(sesion),
        "asignacion_carga": RepositorioAsignacionCarga(sesion),
        "disponibilidad_bloqueo": RepositorioDisponibilidad(sesion),
        "escenario": RepositorioEscenario(sesion),
        "escenario_cambio": RepositorioEscenarioCambio(sesion),
    }

    # 1. Grados: el dígito inicial del código de curso es la clave natural.
    grado_id: dict[int, uuid.UUID] = {}
    for orden in preview.grados:
        existente = repos["grado"].obtener_por_orden(orden)
        if existente is None:
            grado = repos["grado"].agregar(Grado(nombre=str(orden), orden=orden))
            contadores.crear("grado")
        else:
            grado = repos["grado"].actualizar(
                _para_actualizar(Grado(nombre=str(orden), orden=orden), existente)
            )
            contadores.actualizar("grado")
        grado_id[orden] = grado.id

    # 2. Cursos.
    curso_id: dict[str, uuid.UUID] = {}
    for importado in preview.cursos:
        curso = Curso(
            codigo=importado.codigo,
            nombre=importado.nombre,
            grado_id=grado_id[importado.grado],
            estudiantes=importado.estudiantes,
        )
        curso_id[importado.codigo] = _upsert(
            repos["curso"],
            repos["curso"].obtener_por_codigo(importado.codigo),
            curso,
            "curso",
            contadores,
        )

    # 3. Bloques.
    bloque_id: dict[str, uuid.UUID] = {}
    for importado in preview.bloques:
        bloque = Bloque(
            codigo=importado.codigo,
            orden=importado.orden,
            inicio=importado.inicio,
            fin=importado.fin,
            duracion_min=importado.duracion_min,
            tipo=importado.tipo,
        )
        bloque_id[importado.codigo] = _upsert(
            repos["bloque"],
            repos["bloque"].obtener_por_codigo(importado.codigo),
            bloque,
            "bloque",
            contadores,
        )

    # 4. Asignaturas: `es_pesada` es decisión de la UI (D-006), no del Excel.
    asignatura_id: dict[str, uuid.UUID] = {}
    for importado in preview.asignaturas:
        existente = repos["asignatura"].obtener_por_nombre(importado.nombre)
        asignatura = Asignatura(
            nombre=importado.nombre,
            color=importado.color,
            es_pesada=False if existente is None else existente.es_pesada,
        )
        asignatura_id[importado.nombre] = _upsert(
            repos["asignatura"], existente, asignatura, "asignatura", contadores
        )

    # 5. Docentes: `activo` es decisión de la UI, no del Excel.
    docente_id: dict[str, uuid.UUID] = {}
    for importado in preview.docentes:
        existente = repos["docente"].obtener_por_codigo(importado.codigo)
        docente = Docente(
            codigo=importado.codigo,
            nombre=importado.nombre,
            max_sesiones_semana=importado.max_sesiones_semana,
            activo=True if existente is None else existente.activo,
        )
        docente_id[importado.codigo] = _upsert(
            repos["docente"], existente, docente, "docente", contadores
        )

    # 6. Tipos de recurso (catálogo derivado de la hoja Salones).
    for tipo in preview.tipos_recurso:
        if repos["tipo_recurso"].obtener(tipo) is None:
            repos["tipo_recurso"].agregar(TipoRecurso(codigo=tipo))
            contadores.crear("tipo_recurso")

    # 7. Recursos: "Aula 7A" es el aula titular de 7A (DOMAIN.md).
    for importado in preview.recursos:
        recurso = Recurso(
            codigo=importado.codigo,
            nombre=importado.nombre,
            tipo_recurso=importado.tipo_recurso,
            capacidad=importado.capacidad,
            curso_titular_id=(
                None if importado.curso_titular is None else curso_id[importado.curso_titular]
            ),
        )
        _upsert(
            repos["recurso"],
            repos["recurso"].obtener_por_codigo(importado.codigo),
            recurso,
            "recurso",
            contadores,
        )

    # 8. Aptitudes: PK compuesta, sin campos mutables.
    for importado in preview.aptitudes:
        clave = (docente_id[importado.docente], asignatura_id[importado.asignatura])
        if repos["aptitud"].obtener(clave) is None:
            repos["aptitud"].agregar(
                Aptitud(docente_id=clave[0], asignatura_id=clave[1])
            )
            contadores.crear("aptitud")

    # 9. Asignaciones de carga: UNIQUE(curso_id, asignatura_id) (D-009).
    for importado in preview.asignaciones:
        asignacion = AsignacionCarga(
            curso_id=curso_id[importado.curso],
            asignatura_id=asignatura_id[importado.asignatura],
            docente_principal_id=docente_id[importado.docente_principal],
            sesiones_semana=importado.sesiones_semana,
            tipo_recurso_requerido=importado.tipo_recurso_requerido,
        )
        existente = repos["asignacion_carga"].obtener_por_curso_asignatura(
            asignacion.curso_id, asignacion.asignatura_id
        )
        _upsert(
            repos["asignacion_carga"],
            existente,
            asignacion,
            "asignacion_carga",
            contadores,
        )

    # 10. Bloqueos base: solo las franjas con 0 (D-005: nunca escenarios acá).
    for importado in preview.bloqueos:
        bloqueo = DisponibilidadBloqueo(
            docente_id=docente_id[importado.docente],
            dia=importado.dia,
            bloque_id=bloque_id[importado.bloque],
            origen=OrigenBloqueo.personal,
            detalle=DETALLE_BLOQUEO,
        )
        existente = repos["disponibilidad_bloqueo"].obtener_por_franja(
            bloqueo.docente_id, bloqueo.dia, bloqueo.bloque_id
        )
        _upsert(
            repos["disponibilidad_bloqueo"],
            existente,
            bloqueo,
            "disponibilidad_bloqueo",
            contadores,
        )

    # 11. Escenario "¿y si...?" + su overlay (D-005, D-010).
    if preview.escenario is not None:
        existente = repos["escenario"].obtener_por_nombre(preview.escenario.nombre)
        escenario = Escenario(
            nombre=preview.escenario.nombre, descripcion=preview.escenario.descripcion
        )
        escenario_id = _upsert(
            repos["escenario"], existente, escenario, "escenario", contadores
        )
        for importado in preview.escenario.cambios:
            cambio = EscenarioCambio(
                escenario_id=escenario_id,
                docente_id=docente_id[importado.docente],
                dia=importado.dia,
                bloque_id=bloque_id[importado.bloque],
                disponible_nuevo=importado.disponible_nuevo,
                motivo=importado.motivo,
            )
            existente_cambio = repos["escenario_cambio"].obtener_por_franja(
                escenario_id, cambio.docente_id, cambio.dia, cambio.bloque_id
            )
            _upsert(
                repos["escenario_cambio"],
                existente_cambio,
                cambio,
                "escenario_cambio",
                contadores,
            )

    sesion.flush()
    return contadores.resultado()


def _upsert(
    repo: Repositorio[Any, Any, Any],
    existente: Any | None,
    nueva: Any,
    entidad: str,
    contadores: _Contadores,
) -> uuid.UUID:
    """Inserta o actualiza preservando el `id`, y registra el conteo."""
    if existente is None:
        guardada = repo.agregar(nueva)
        contadores.crear(entidad)
    else:
        guardada = repo.actualizar(_para_actualizar(nueva, existente))
        contadores.actualizar(entidad)
    return guardada.id

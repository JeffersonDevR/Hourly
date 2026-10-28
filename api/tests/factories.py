"""Grafo mínimo y válido de entidades para los tests de esquema.

No son datos de negocio: solo lo imprescindible para que las FKs se satisfagan.
Los nombres siguen el vocabulario del archivo real (6A, D1, B1, Aula 6A).
"""

from dataclasses import dataclass
from datetime import time

from sqlalchemy.orm import Session

from app.domain.carga import AsignacionCarga
from app.domain.catalogo import Asignatura, Bloque, Curso, Docente, Grado
from app.domain.enums import EstadoVersion, TipoBloque
from app.domain.horario import HorarioVersion, Sesion
from app.domain.recursos import Recurso, TipoRecurso
from app.repositories.carga import RepositorioAsignacionCarga
from app.repositories.catalogo import (
    RepositorioAsignatura,
    RepositorioBloque,
    RepositorioCurso,
    RepositorioDocente,
    RepositorioGrado,
)
from app.repositories.horario import RepositorioHorarioVersion
from app.repositories.recursos import RepositorioRecurso, RepositorioTipoRecurso

TIPO_GENERAL = "GENERAL"


@dataclass(frozen=True)
class BaseHorario:
    """Todo lo que necesita una `sesion` para existir, con variantes para duplicar."""

    grado: Grado
    curso_a: Curso
    curso_b: Curso
    asignatura: Asignatura
    docente_a: Docente
    docente_b: Docente
    tipo_recurso: TipoRecurso
    recurso_a: Recurso
    recurso_b: Recurso
    bloque: Bloque
    version: HorarioVersion
    carga_a: AsignacionCarga
    carga_b: AsignacionCarga


def crear_base_horario(sesion: Session) -> BaseHorario:
    grado = RepositorioGrado(sesion).agregar(Grado(nombre="6", orden=1))
    curso_a = RepositorioCurso(sesion).agregar(
        Curso(codigo="6A", nombre="6A", grado_id=grado.id, estudiantes=30)
    )
    curso_b = RepositorioCurso(sesion).agregar(
        Curso(codigo="6B", nombre="6B", grado_id=grado.id, estudiantes=28)
    )
    asignatura = RepositorioAsignatura(sesion).agregar(
        Asignatura(nombre="Matemáticas", color="#2563EB")
    )
    docente_a = RepositorioDocente(sesion).agregar(
        Docente(codigo="D1", nombre="Docente 1", max_sesiones_semana=24)
    )
    docente_b = RepositorioDocente(sesion).agregar(
        Docente(codigo="D2", nombre="Docente 2", max_sesiones_semana=24)
    )
    tipo_recurso = RepositorioTipoRecurso(sesion).agregar(TipoRecurso(codigo=TIPO_GENERAL))
    recurso_a = RepositorioRecurso(sesion).agregar(
        Recurso(
            codigo="A6A",
            nombre="Aula 6A",
            tipo_recurso=tipo_recurso.codigo,
            capacidad=30,
            curso_titular_id=curso_a.id,
        )
    )
    recurso_b = RepositorioRecurso(sesion).agregar(
        Recurso(
            codigo="A6B",
            nombre="Aula 6B",
            tipo_recurso=tipo_recurso.codigo,
            capacidad=30,
            curso_titular_id=curso_b.id,
        )
    )
    bloque = RepositorioBloque(sesion).agregar(
        Bloque(
            codigo="B1",
            orden=1,
            inicio=time(7, 0),
            fin=time(8, 0),
            duracion_min=60,
            tipo=TipoBloque.clase,
        )
    )
    version = RepositorioHorarioVersion(sesion).agregar(
        HorarioVersion(numero=1, estado=EstadoVersion.borrador)
    )
    carga_a = RepositorioAsignacionCarga(sesion).agregar(
        AsignacionCarga(
            curso_id=curso_a.id,
            asignatura_id=asignatura.id,
            docente_principal_id=docente_a.id,
            sesiones_semana=4,
            tipo_recurso_requerido=tipo_recurso.codigo,
        )
    )
    carga_b = RepositorioAsignacionCarga(sesion).agregar(
        AsignacionCarga(
            curso_id=curso_b.id,
            asignatura_id=asignatura.id,
            docente_principal_id=docente_b.id,
            sesiones_semana=4,
            tipo_recurso_requerido=tipo_recurso.codigo,
        )
    )
    return BaseHorario(
        grado=grado,
        curso_a=curso_a,
        curso_b=curso_b,
        asignatura=asignatura,
        docente_a=docente_a,
        docente_b=docente_b,
        tipo_recurso=tipo_recurso,
        recurso_a=recurso_a,
        recurso_b=recurso_b,
        bloque=bloque,
        version=version,
        carga_a=carga_a,
        carga_b=carga_b,
    )


def sesion_en_primera_franja(
    base: BaseHorario,
    *,
    curso: Curso | None = None,
    docente: Docente | None = None,
    recurso: Recurso | None = None,
    dia: int = 1,
) -> Sesion:
    """Sesión con valores por defecto = la primera franja del lunes."""
    curso = curso or base.curso_a
    docente = docente or base.docente_a
    recurso = recurso or base.recurso_a
    carga = base.carga_a if curso.id == base.curso_a.id else base.carga_b
    return Sesion(
        horario_version_id=base.version.id,
        asignacion_carga_id=carga.id,
        curso_id=curso.id,
        docente_id=docente.id,
        dia=dia,
        bloque_id=base.bloque.id,
        recurso_id=recurso.id,
    )

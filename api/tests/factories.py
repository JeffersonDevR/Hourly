"""Fábricas de pruebas: grafo mínimo para los tests de esquema y estado en memoria.

`crear_base_horario` escribe en SQLite (tests de esquema y de índices únicos).
`HorarioEnMemoria` arma el mismo vocabulario (6A, D1, B1, Aula 6A) como
dataclasses, sin DB: es la entrada de los tests del validador puro.
"""

import uuid
from dataclasses import dataclass, field
from datetime import time

from sqlalchemy.orm import Session

from app.domain.carga import AsignacionCarga, DisponibilidadBloqueo
from app.domain.catalogo import Aptitud, Asignatura, Bloque, Curso, Docente, Grado
from app.domain.enums import EstadoVersion, OrigenBloqueo, TipoBloque
from app.domain.horario import EscenarioCambio, HorarioVersion, Sesion
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
from app.validator.estado import EstadoHorario

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


@dataclass
class HorarioEnMemoria:
    """Constructor de `EstadoHorario` sin DB, para el validador y el solver.

    Cada método agrega una entidad y la devuelve; `estado()` congela las tuplas que
    espera `validar()` / `diagnosticar_carga()`. Todo comparte un `version_id`.
    """

    version_id: uuid.UUID = field(default_factory=uuid.uuid4)
    grado_id: uuid.UUID = field(default_factory=uuid.uuid4)
    cursos: list[Curso] = field(default_factory=list)
    docentes: list[Docente] = field(default_factory=list)
    bloques: list[Bloque] = field(default_factory=list)
    asignaturas: list[Asignatura] = field(default_factory=list)
    aptitudes: list[Aptitud] = field(default_factory=list)
    asignaciones: list[AsignacionCarga] = field(default_factory=list)
    bloqueos: list[DisponibilidadBloqueo] = field(default_factory=list)
    recursos: list[Recurso] = field(default_factory=list)
    escenario_cambios: list[EscenarioCambio] = field(default_factory=list)
    sesiones: list[Sesion] = field(default_factory=list)

    @property
    def escenario_id(self) -> uuid.UUID:
        """Id estable del escenario que arman `bloquear_en_escenario` y compañía."""
        return uuid.uuid5(self.version_id, "escenario")

    def curso(self, codigo: str = "6A", estudiantes: int = 30) -> Curso:
        curso = Curso(
            codigo=codigo, nombre=codigo, grado_id=self.grado_id, estudiantes=estudiantes
        )
        self.cursos.append(curso)
        return curso

    def docente(self, codigo: str = "D1", maximo: int = 24) -> Docente:
        docente = Docente(
            codigo=codigo, nombre=f"Docente {codigo}", max_sesiones_semana=maximo
        )
        self.docentes.append(docente)
        return docente

    def bloque(
        self,
        codigo: str = "B1",
        orden: int | None = None,
        tipo: TipoBloque = TipoBloque.clase,
    ) -> Bloque:
        orden = len(self.bloques) + 1 if orden is None else orden
        bloque = Bloque(
            codigo=codigo,
            orden=orden,
            inicio=time(6 + orden, 0),
            fin=time(7 + orden, 0),
            duracion_min=60,
            tipo=tipo,
        )
        self.bloques.append(bloque)
        return bloque

    def asignatura(self, nombre: str = "Matemáticas", pesada: bool = False) -> Asignatura:
        asignatura = Asignatura(nombre=nombre, color="#2563EB", es_pesada=pesada)
        self.asignaturas.append(asignatura)
        return asignatura

    def habilitar(self, docente: Docente, asignatura: Asignatura) -> Aptitud:
        aptitud = Aptitud(docente_id=docente.id, asignatura_id=asignatura.id)
        self.aptitudes.append(aptitud)
        return aptitud

    def asignacion(
        self,
        curso: Curso,
        asignatura: Asignatura,
        docente: Docente | None = None,
        sesiones: int = 1,
        tipo_recurso: str = TIPO_GENERAL,
    ) -> AsignacionCarga:
        if docente is None:
            docente = self.docente(codigo=f"D-{asignatura.nombre}")
        carga = AsignacionCarga(
            curso_id=curso.id,
            asignatura_id=asignatura.id,
            docente_principal_id=docente.id,
            sesiones_semana=sesiones,
            tipo_recurso_requerido=tipo_recurso,
        )
        self.asignaciones.append(carga)
        return carga

    def recurso(
        self,
        codigo: str = "Aula 6A",
        tipo: str = TIPO_GENERAL,
        capacidad: int = 30,
        curso_titular: Curso | None = None,
    ) -> Recurso:
        recurso = Recurso(
            codigo=codigo,
            nombre=codigo,
            tipo_recurso=tipo,
            capacidad=capacidad,
            curso_titular_id=curso_titular.id if curso_titular is not None else None,
        )
        self.recursos.append(recurso)
        return recurso

    def bloquear(self, docente: Docente, dia: int, bloque: Bloque) -> DisponibilidadBloqueo:
        bloqueo = DisponibilidadBloqueo(
            docente_id=docente.id, dia=dia, bloque_id=bloque.id, origen=OrigenBloqueo.personal
        )
        self.bloqueos.append(bloqueo)
        return bloqueo

    def cambiar_escenario(
        self,
        docente: Docente,
        dia: int,
        bloque: Bloque,
        *,
        disponible: bool,
        escenario_id: uuid.UUID | None = None,
    ) -> EscenarioCambio:
        cambio = EscenarioCambio(
            escenario_id=escenario_id or self.escenario_id,
            docente_id=docente.id,
            dia=dia,
            bloque_id=bloque.id,
            disponible_nuevo=disponible,
        )
        self.escenario_cambios.append(cambio)
        return cambio

    def colocar(
        self,
        asignacion: AsignacionCarga,
        dia: int,
        bloque: Bloque,
        docente: Docente | None = None,
        recurso: Recurso | None = None,
    ) -> Sesion:
        sesion = Sesion(
            horario_version_id=self.version_id,
            asignacion_carga_id=asignacion.id,
            curso_id=asignacion.curso_id,
            docente_id=docente.id if docente is not None else asignacion.docente_principal_id,
            dia=dia,
            bloque_id=bloque.id,
            recurso_id=recurso.id if recurso is not None else None,
        )
        self.sesiones.append(sesion)
        return sesion

    def estado(self) -> EstadoHorario:
        return EstadoHorario(
            cursos=tuple(self.cursos),
            docentes=tuple(self.docentes),
            bloques=tuple(self.bloques),
            asignaturas=tuple(self.asignaturas),
            aptitudes=tuple(self.aptitudes),
            asignaciones=tuple(self.asignaciones),
            bloqueos=tuple(self.bloqueos),
            recursos=tuple(self.recursos),
            escenario_cambios=tuple(self.escenario_cambios),
            sesiones=tuple(self.sesiones),
        )

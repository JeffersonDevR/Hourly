"""CRUD de catálogos: cursos, docentes, recursos y carga académica.

Las reglas de integridad las decide la DB (FKs y UNIQUE, D-001): acá se traducen a
`409`/`400` en vez de dejarlas explotar como `500`. Los errores usan el formato único
de la API `{codigo, mensaje}`, que `main.py` aplana desde el `detail` de `HTTPException`.
"""

from __future__ import annotations

import dataclasses
import uuid
from datetime import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.carga import AsignacionCarga
from app.domain.catalogo import Aptitud, Asignatura, Bloque, Curso, Docente, Grado
from app.domain.enums import TipoBloque
from app.domain.recursos import Recurso, TipoRecurso
from app.repositories.carga import RepositorioAsignacionCarga
from app.repositories.catalogo import (
    RepositorioAptitud,
    RepositorioAsignatura,
    RepositorioBloque,
    RepositorioCurso,
    RepositorioDocente,
    RepositorioGrado,
)
from app.repositories.recursos import RepositorioRecurso, RepositorioTipoRecurso
from app.routers.comun import error, no_encontrado

router = APIRouter(tags=["catalogos"])

Sesion = Annotated[Session, Depends(get_session)]


def _obtener(repo: Any, clave: Any, entidad: str) -> Any:
    hallado = repo.obtener(clave)
    if hallado is None:
        no_encontrado(entidad)
    return hallado


def _exigir_fk(repo: Any, clave: Any, entidad: str) -> None:
    if repo.obtener(clave) is None:
        error(400, "REFERENCIA_INVALIDA", f"{entidad} inexistente.")


def _unico(repo: Any, codigo: str, entidad: str, id_actual: uuid.UUID | None = None) -> None:
    otro = repo.obtener_por_codigo(codigo)
    if otro is not None and otro.id != id_actual:
        error(409, "CODIGO_DUPLICADO", f"Ya existe {entidad} con el código {codigo!r}.")


def _crear(repo: Any, entidad: Any, sesion: Session) -> Any:
    guardado = repo.agregar(entidad)
    sesion.commit()
    return guardado


def _actualizar(repo: Any, actual: Any, cambios: dict[str, Any], sesion: Session) -> Any:
    guardado = repo.actualizar(dataclasses.replace(actual, **cambios))
    sesion.commit()
    return guardado


def _eliminar(repo: Any, clave: Any, entidad: str, sesion: Session) -> None:
    """Borra o explica por qué no: `409` si otra tabla lo referencia (D-001, FKs reales)."""
    try:
        # SAVEPOINT: el DELETE falla y la transacción de la request sigue viva para responder.
        with sesion.begin_nested():
            borrado = repo.eliminar(clave)
    except IntegrityError:
        error(
            409,
            "EN_USO",
            f"{entidad} en uso: hay datos que lo referencian. "
            "Borrá o cambiá esos datos primero.",
        )
    if not borrado:
        no_encontrado(entidad)
    sesion.commit()


# --- esquemas -----------------------------------------------------------------------


class CursoLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    nombre: str
    grado_id: uuid.UUID
    estudiantes: int


class CursoCrear(BaseModel):
    codigo: str = Field(min_length=1, max_length=32)
    nombre: str = Field(min_length=1, max_length=120)
    grado_id: uuid.UUID
    estudiantes: int = Field(ge=0)


class CursoActualizar(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=32)
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    grado_id: uuid.UUID | None = None
    estudiantes: int | None = Field(default=None, ge=0)


class DocenteLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    nombre: str
    max_sesiones_semana: int
    activo: bool


class DocenteCrear(BaseModel):
    codigo: str = Field(min_length=1, max_length=32)
    nombre: str = Field(min_length=1, max_length=120)
    max_sesiones_semana: int = Field(ge=0)
    activo: bool = True


class DocenteActualizar(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=32)
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    max_sesiones_semana: int | None = Field(default=None, ge=0)
    activo: bool | None = None


class RecursoLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    nombre: str
    tipo_recurso: str
    capacidad: int
    curso_titular_id: uuid.UUID | None


class RecursoCrear(BaseModel):
    codigo: str = Field(min_length=1, max_length=32)
    nombre: str = Field(min_length=1, max_length=120)
    tipo_recurso: str = Field(min_length=1, max_length=32)
    capacidad: int = Field(ge=0)
    curso_titular_id: uuid.UUID | None = None


class RecursoActualizar(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=32)
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    tipo_recurso: str | None = Field(default=None, min_length=1, max_length=32)
    capacidad: int | None = Field(default=None, ge=0)
    curso_titular_id: uuid.UUID | None = None


class AsignacionLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    curso_id: uuid.UUID
    asignatura_id: uuid.UUID
    docente_principal_id: uuid.UUID
    sesiones_semana: int
    tipo_recurso_requerido: str


class AsignacionCrear(BaseModel):
    curso_id: uuid.UUID
    asignatura_id: uuid.UUID
    docente_principal_id: uuid.UUID
    sesiones_semana: int = Field(ge=0)
    tipo_recurso_requerido: str = Field(min_length=1, max_length=32)


class AsignacionActualizar(BaseModel):
    curso_id: uuid.UUID | None = None
    asignatura_id: uuid.UUID | None = None
    docente_principal_id: uuid.UUID | None = None
    sesiones_semana: int | None = Field(default=None, ge=0)
    tipo_recurso_requerido: str | None = Field(default=None, min_length=1, max_length=32)


class TipoRecursoLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str


class TipoRecursoCrear(BaseModel):
    codigo: str = Field(min_length=1, max_length=32)


class AptitudLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    docente_id: uuid.UUID
    asignatura_id: uuid.UUID


class AptitudCrear(BaseModel):
    docente_id: uuid.UUID
    asignatura_id: uuid.UUID


class GradoLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    orden: int


class GradoCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=60)
    orden: int = Field(ge=0)


class GradoActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=60)
    orden: int | None = Field(default=None, ge=0)


class BloqueLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    orden: int
    inicio: Any
    fin: Any
    duracion_min: int
    tipo: str


class BloqueCrear(BaseModel):
    codigo: str = Field(min_length=1, max_length=32)
    orden: int = Field(ge=0)
    inicio: time
    fin: time
    tipo: TipoBloque = TipoBloque.clase
    # Si se omite se deriva de inicio/fin: una sola fuente de verdad.
    duracion_min: int | None = Field(default=None, ge=1)


class BloqueActualizar(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=32)
    orden: int | None = Field(default=None, ge=0)
    inicio: time | None = None
    fin: time | None = None
    tipo: TipoBloque | None = None
    duracion_min: int | None = Field(default=None, ge=1)


class AsignaturaCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    color: str = Field(min_length=4, max_length=16)
    es_pesada: bool = False


class AsignaturaActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    color: str | None = Field(default=None, min_length=4, max_length=16)
    es_pesada: bool | None = None


class AsignaturaLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    color: str
    es_pesada: bool


# --- cursos -------------------------------------------------------------------------


@router.get("/cursos", response_model=list[CursoLeer])
def listar_cursos(sesion: Sesion) -> list[Curso]:
    return RepositorioCurso(sesion).listar()


@router.post("/cursos", response_model=CursoLeer, status_code=201)
def crear_curso(datos: CursoCrear, sesion: Sesion) -> Curso:
    repo = RepositorioCurso(sesion)
    _unico(repo, datos.codigo, "un curso")
    _exigir_fk(RepositorioGrado(sesion), datos.grado_id, "Grado")
    return _crear(repo, Curso(**datos.model_dump()), sesion)


@router.get("/cursos/{curso_id}", response_model=CursoLeer)
def leer_curso(curso_id: uuid.UUID, sesion: Sesion) -> Curso:
    return _obtener(RepositorioCurso(sesion), curso_id, "Curso")


@router.patch("/cursos/{curso_id}", response_model=CursoLeer)
def actualizar_curso(curso_id: uuid.UUID, datos: CursoActualizar, sesion: Sesion) -> Curso:
    repo = RepositorioCurso(sesion)
    actual = _obtener(repo, curso_id, "Curso")
    cambios = datos.model_dump(exclude_unset=True)
    if "codigo" in cambios:
        _unico(repo, cambios["codigo"], "un curso", curso_id)
    if "grado_id" in cambios:
        _exigir_fk(RepositorioGrado(sesion), cambios["grado_id"], "Grado")
    return _actualizar(repo, actual, cambios, sesion)


@router.delete("/cursos/{curso_id}", status_code=204)
def eliminar_curso(curso_id: uuid.UUID, sesion: Sesion) -> None:
    _eliminar(RepositorioCurso(sesion), curso_id, "Curso", sesion)


# --- docentes -----------------------------------------------------------------------


@router.get("/docentes", response_model=list[DocenteLeer])
def listar_docentes(sesion: Sesion) -> list[Docente]:
    return RepositorioDocente(sesion).listar()


@router.post("/docentes", response_model=DocenteLeer, status_code=201)
def crear_docente(datos: DocenteCrear, sesion: Sesion) -> Docente:
    repo = RepositorioDocente(sesion)
    _unico(repo, datos.codigo, "un docente")
    return _crear(repo, Docente(**datos.model_dump()), sesion)


@router.get("/docentes/{docente_id}", response_model=DocenteLeer)
def leer_docente(docente_id: uuid.UUID, sesion: Sesion) -> Docente:
    return _obtener(RepositorioDocente(sesion), docente_id, "Docente")


@router.patch("/docentes/{docente_id}", response_model=DocenteLeer)
def actualizar_docente(docente_id: uuid.UUID, datos: DocenteActualizar, sesion: Sesion) -> Docente:
    repo = RepositorioDocente(sesion)
    actual = _obtener(repo, docente_id, "Docente")
    cambios = datos.model_dump(exclude_unset=True)
    if "codigo" in cambios:
        _unico(repo, cambios["codigo"], "un docente", docente_id)
    return _actualizar(repo, actual, cambios, sesion)


@router.delete("/docentes/{docente_id}", status_code=204)
def eliminar_docente(docente_id: uuid.UUID, sesion: Sesion) -> None:
    _eliminar(RepositorioDocente(sesion), docente_id, "Docente", sesion)


# --- recursos -----------------------------------------------------------------------


@router.get("/recursos", response_model=list[RecursoLeer])
def listar_recursos(sesion: Sesion) -> list[Recurso]:
    return RepositorioRecurso(sesion).listar()


def _exigir_recurso(sesion: Session, datos: dict[str, Any]) -> None:
    if "tipo_recurso" in datos:
        _exigir_fk(RepositorioTipoRecurso(sesion), datos["tipo_recurso"], "Tipo de recurso")
    if datos.get("curso_titular_id") is not None:
        _exigir_fk(RepositorioCurso(sesion), datos["curso_titular_id"], "Curso titular")


@router.post("/recursos", response_model=RecursoLeer, status_code=201)
def crear_recurso(datos: RecursoCrear, sesion: Sesion) -> Recurso:
    repo = RepositorioRecurso(sesion)
    _unico(repo, datos.codigo, "un recurso")
    cuerpo = datos.model_dump()
    _exigir_recurso(sesion, cuerpo)
    return _crear(repo, Recurso(**cuerpo), sesion)


@router.get("/recursos/{recurso_id}", response_model=RecursoLeer)
def leer_recurso(recurso_id: uuid.UUID, sesion: Sesion) -> Recurso:
    return _obtener(RepositorioRecurso(sesion), recurso_id, "Recurso")


@router.patch("/recursos/{recurso_id}", response_model=RecursoLeer)
def actualizar_recurso(recurso_id: uuid.UUID, datos: RecursoActualizar, sesion: Sesion) -> Recurso:
    repo = RepositorioRecurso(sesion)
    actual = _obtener(repo, recurso_id, "Recurso")
    cambios = datos.model_dump(exclude_unset=True)
    if "codigo" in cambios:
        _unico(repo, cambios["codigo"], "un recurso", recurso_id)
    _exigir_recurso(sesion, cambios)
    return _actualizar(repo, actual, cambios, sesion)


@router.delete("/recursos/{recurso_id}", status_code=204)
def eliminar_recurso(recurso_id: uuid.UUID, sesion: Sesion) -> None:
    _eliminar(RepositorioRecurso(sesion), recurso_id, "Recurso", sesion)


# --- carga académica ----------------------------------------------------------------


def _exigir_asignacion(sesion: Session, datos: dict[str, Any]) -> None:
    if "curso_id" in datos:
        _exigir_fk(RepositorioCurso(sesion), datos["curso_id"], "Curso")
    if "asignatura_id" in datos:
        _exigir_fk(RepositorioAsignatura(sesion), datos["asignatura_id"], "Asignatura")
    if "docente_principal_id" in datos:
        _exigir_fk(RepositorioDocente(sesion), datos["docente_principal_id"], "Docente")
    if "tipo_recurso_requerido" in datos:
        _exigir_fk(
            RepositorioTipoRecurso(sesion),
            datos["tipo_recurso_requerido"],
            "Tipo de recurso",
        )


def _par_unico(sesion: Session, cuerpo: dict[str, Any], id_actual: uuid.UUID | None) -> None:
    otro = RepositorioAsignacionCarga(sesion).obtener_por_curso_asignatura(
        cuerpo["curso_id"], cuerpo["asignatura_id"]
    )
    if otro is not None and otro.id != id_actual:
        error(
            409,
            "ASIGNACION_DUPLICADA",
            "El curso ya tiene una asignación para esa asignatura.",
        )


@router.get("/asignaciones", response_model=list[AsignacionLeer])
def listar_asignaciones(
    sesion: Sesion, curso_id: Annotated[uuid.UUID | None, Query()] = None
) -> list[AsignacionCarga]:
    repo = RepositorioAsignacionCarga(sesion)
    return repo.listar_por_curso(curso_id) if curso_id else repo.listar()


@router.post("/asignaciones", response_model=AsignacionLeer, status_code=201)
def crear_asignacion(datos: AsignacionCrear, sesion: Sesion) -> AsignacionCarga:
    cuerpo = datos.model_dump()
    _exigir_asignacion(sesion, cuerpo)
    _par_unico(sesion, cuerpo, None)
    return _crear(RepositorioAsignacionCarga(sesion), AsignacionCarga(**cuerpo), sesion)


@router.get("/asignaciones/{asignacion_id}", response_model=AsignacionLeer)
def leer_asignacion(asignacion_id: uuid.UUID, sesion: Sesion) -> AsignacionCarga:
    return _obtener(RepositorioAsignacionCarga(sesion), asignacion_id, "Asignación")


@router.patch("/asignaciones/{asignacion_id}", response_model=AsignacionLeer)
def actualizar_asignacion(
    asignacion_id: uuid.UUID, datos: AsignacionActualizar, sesion: Sesion
) -> AsignacionCarga:
    repo = RepositorioAsignacionCarga(sesion)
    actual = _obtener(repo, asignacion_id, "Asignación")
    cambios = datos.model_dump(exclude_unset=True)
    _exigir_asignacion(sesion, cambios)
    _par_unico(sesion, {**dataclasses.asdict(actual), **cambios}, asignacion_id)
    return _actualizar(repo, actual, cambios, sesion)


@router.delete("/asignaciones/{asignacion_id}", status_code=204)
def eliminar_asignacion(asignacion_id: uuid.UUID, sesion: Sesion) -> None:
    _eliminar(RepositorioAsignacionCarga(sesion), asignacion_id, "Asignación", sesion)


# --- tipos de recurso y aptitudes (sin Excel también tienen que existir) -------------


@router.get("/tipos-recurso", response_model=list[TipoRecursoLeer])
def listar_tipos_recurso(sesion: Sesion) -> list[TipoRecurso]:
    return RepositorioTipoRecurso(sesion).listar()


@router.post("/tipos-recurso", response_model=TipoRecursoLeer, status_code=201)
def crear_tipo_recurso(datos: TipoRecursoCrear, sesion: Sesion) -> TipoRecurso:
    repo = RepositorioTipoRecurso(sesion)
    if repo.obtener(datos.codigo) is not None:
        error(409, "CODIGO_DUPLICADO", f"Ya existe el tipo de recurso {datos.codigo!r}.")
    return _crear(repo, TipoRecurso(codigo=datos.codigo), sesion)


@router.delete("/tipos-recurso/{codigo}", status_code=204)
def eliminar_tipo_recurso(codigo: str, sesion: Sesion) -> None:
    _eliminar(RepositorioTipoRecurso(sesion), codigo, "Tipo de recurso", sesion)


@router.get("/aptitudes", response_model=list[AptitudLeer])
def listar_aptitudes(sesion: Sesion) -> list[Aptitud]:
    return RepositorioAptitud(sesion).listar()


@router.post("/aptitudes", response_model=AptitudLeer, status_code=201)
def crear_aptitud(datos: AptitudCrear, sesion: Sesion) -> Aptitud:
    _exigir_fk(RepositorioDocente(sesion), datos.docente_id, "Docente")
    _exigir_fk(RepositorioAsignatura(sesion), datos.asignatura_id, "Asignatura")
    repo = RepositorioAptitud(sesion)
    if repo.obtener((datos.docente_id, datos.asignatura_id)) is not None:
        error(409, "APTITUD_DUPLICADA", "Ese docente ya está habilitado para esa asignatura.")
    return _crear(repo, Aptitud(**datos.model_dump()), sesion)


@router.delete("/aptitudes/{docente_id}/{asignatura_id}", status_code=204)
def eliminar_aptitud(docente_id: uuid.UUID, asignatura_id: uuid.UUID, sesion: Sesion) -> None:
    _eliminar(
        RepositorioAptitud(sesion),
        (docente_id, asignatura_id),
        "Aptitud",
        sesion,
    )


# --- grados -------------------------------------------------------------------------


@router.get("/grados", response_model=list[GradoLeer])
def listar_grados(sesion: Sesion) -> list[Grado]:
    return sorted(RepositorioGrado(sesion).listar(), key=lambda grado: grado.orden)


@router.post("/grados", response_model=GradoLeer, status_code=201)
def crear_grado(datos: GradoCrear, sesion: Sesion) -> Grado:
    return _crear(RepositorioGrado(sesion), Grado(**datos.model_dump()), sesion)


@router.patch("/grados/{grado_id}", response_model=GradoLeer)
def actualizar_grado(grado_id: uuid.UUID, datos: GradoActualizar, sesion: Sesion) -> Grado:
    repo = RepositorioGrado(sesion)
    actual = _obtener(repo, grado_id, "Grado")
    return _actualizar(repo, actual, datos.model_dump(exclude_unset=True), sesion)


@router.delete("/grados/{grado_id}", status_code=204)
def eliminar_grado(grado_id: uuid.UUID, sesion: Sesion) -> None:
    _eliminar(RepositorioGrado(sesion), grado_id, "Grado", sesion)


# --- bloques ------------------------------------------------------------------------


def _minutos(inicio: time, fin: time) -> int:
    return (fin.hour * 60 + fin.minute) - (inicio.hour * 60 + inicio.minute)


def _duracion(datos: dict[str, Any]) -> int | None:
    """Deriva `duracion_min` de inicio/fin. Si viene y no coincide, es un error del cliente."""
    if "inicio" not in datos or "fin" not in datos:
        return None
    real = _minutos(datos["inicio"], datos["fin"])
    if real <= 0:
        error(400, "BLOQUE_INVALIDO", "El fin del bloque tiene que ser posterior al inicio.")
    declarada = datos.get("duracion_min")
    if declarada is not None and declarada != real:
        error(
            400,
            "DURACION_INCONSISTENTE",
            f"El bloque dura {real} minutos, no {declarada}.",
        )
    return real


@router.get("/bloques", response_model=list[BloqueLeer])
def listar_bloques(sesion: Sesion) -> list[Bloque]:
    return sorted(RepositorioBloque(sesion).listar(), key=lambda bloque: bloque.orden)


@router.post("/bloques", response_model=BloqueLeer, status_code=201)
def crear_bloque(datos: BloqueCrear, sesion: Sesion) -> Bloque:
    repo = RepositorioBloque(sesion)
    _unico(repo, datos.codigo, "un bloque")
    cuerpo = datos.model_dump()
    cuerpo["duracion_min"] = _duracion(cuerpo)
    return _crear(repo, Bloque(**cuerpo), sesion)


@router.patch("/bloques/{bloque_id}", response_model=BloqueLeer)
def actualizar_bloque(
    bloque_id: uuid.UUID, datos: BloqueActualizar, sesion: Sesion
) -> Bloque:
    repo = RepositorioBloque(sesion)
    actual = _obtener(repo, bloque_id, "Bloque")
    cambios = datos.model_dump(exclude_unset=True)
    if "codigo" in cambios:
        _unico(repo, cambios["codigo"], "un bloque", bloque_id)
    duracion = _duracion({**dataclasses.asdict(actual), **cambios})
    if duracion is not None:
        cambios["duracion_min"] = duracion
    return _actualizar(repo, actual, cambios, sesion)


@router.delete("/bloques/{bloque_id}", status_code=204)
def eliminar_bloque(bloque_id: uuid.UUID, sesion: Sesion) -> None:
    _eliminar(RepositorioBloque(sesion), bloque_id, "Bloque", sesion)


# --- asignaturas --------------------------------------------------------------------


@router.get("/asignaturas", response_model=list[AsignaturaLeer])
def listar_asignaturas(sesion: Sesion) -> list[Asignatura]:
    return RepositorioAsignatura(sesion).listar()


@router.post("/asignaturas", response_model=AsignaturaLeer, status_code=201)
def crear_asignatura(datos: AsignaturaCrear, sesion: Sesion) -> Asignatura:
    repo = RepositorioAsignatura(sesion)
    if repo.obtener_por_nombre(datos.nombre) is not None:
        error(409, "NOMBRE_DUPLICADO", f"Ya existe la asignatura {datos.nombre!r}.")
    return _crear(repo, Asignatura(**datos.model_dump()), sesion)


@router.patch("/asignaturas/{asignatura_id}", response_model=AsignaturaLeer)
def actualizar_asignatura(
    asignatura_id: uuid.UUID, datos: AsignaturaActualizar, sesion: Sesion
) -> Asignatura:
    repo = RepositorioAsignatura(sesion)
    actual = _obtener(repo, asignatura_id, "Asignatura")
    return _actualizar(repo, actual, datos.model_dump(exclude_unset=True), sesion)


@router.delete("/asignaturas/{asignatura_id}", status_code=204)
def eliminar_asignatura(asignatura_id: uuid.UUID, sesion: Sesion) -> None:
    _eliminar(RepositorioAsignatura(sesion), asignatura_id, "Asignatura", sesion)

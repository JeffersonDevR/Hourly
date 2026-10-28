"""Endpoints de importación: preview, corrección de filas, confirmación y plantilla.

Solo los cuatro endpoints de la fase 2 (`ARCHITECTURE.md`). Toda la lógica está en
`app.importer`: acá se traduce HTTP <-> dominio, se persiste `importacion` /
`importacion_error` y se cierra la transacción.

Cada análisis es autoritativo, como `POST /horarios/{v}/validar` en D-011: los
hallazgos de la importación se borran y se regeneran, así una fila corregida no deja
un error fantasma en la tabla.
"""

import dataclasses
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.procesos import Importacion, ImportacionError
from app.importer.analisis import analizar_libro
from app.importer.confirmacion import confirmar_importacion
from app.importer.correcciones import Correccion, CorreccionInvalida, aplicar_correcciones
from app.importer.lectura import ArchivoInvalido, leer_libro
from app.importer.modelos import hojas_de_preview
from app.importer.plantilla import MEDIA_TYPE_XLSX, NOMBRE_ARCHIVO, plantilla_bytes
from app.models.base import utcnow
from app.repositories.procesos import RepositorioImportacion, RepositorioImportacionError

router = APIRouter(prefix="/importaciones", tags=["importaciones"])

ESTADO_PREVIEW = "preview"
ESTADO_CONFIRMADA = "confirmada"


class CorreccionCuerpo(BaseModel):
    """Una celda a corregir, identificada igual que en el hallazgo."""

    hoja: str
    fila: int
    columna: str
    valor: str | int | float | bool | None = None


class CorreccionesCuerpo(BaseModel):
    correcciones: list[CorreccionCuerpo] = Field(default_factory=list)


def _obtener(sesion: Session, importacion_id: uuid.UUID) -> Importacion:
    guardada = RepositorioImportacion(sesion).obtener(importacion_id)
    if guardada is None:
        raise HTTPException(status_code=404, detail="Importación no encontrada.")
    return guardada


def _guardar_hallazgos(
    sesion: Session, importacion_id: uuid.UUID, preview: Any
) -> None:
    """Reemplaza los `importacion_error` de la importación (análisis autoritativo)."""
    repositorio = RepositorioImportacionError(sesion)
    for anterior in repositorio.listar_por_importacion(importacion_id):
        repositorio.eliminar(anterior.id)
    for hallazgo in preview.hallazgos:
        repositorio.agregar(
            ImportacionError(
                importacion_id=importacion_id,
                severidad=hallazgo.severidad,
                mensaje=hallazgo.mensaje,
                hoja=hallazgo.hoja,
                fila=hallazgo.fila,
                columna=hallazgo.columna,
                codigo=hallazgo.codigo,
            )
        )


def _respuesta(guardada: Importacion, preview: Any) -> dict[str, Any]:
    return {
        "id": str(guardada.id),
        "estado": guardada.estado,
        **preview.a_json(),
    }


@router.get("/plantilla")
def descargar_plantilla() -> Response:
    """Plantilla .xlsx con las hojas y encabezados que espera el importador."""
    return Response(
        content=plantilla_bytes(),
        media_type=MEDIA_TYPE_XLSX,
        headers={"Content-Disposition": f'attachment; filename="{NOMBRE_ARCHIVO}"'},
    )


@router.post("")
def crear_importacion(
    archivo: Annotated[UploadFile, File()],
    sesion: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Sube un .xlsx y devuelve el preview con un hallazgo por fila problemática."""
    contenido = archivo.file.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    try:
        hojas = leer_libro(contenido)
    except ArchivoInvalido as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    preview = analizar_libro(hojas, archivo_nombre=archivo.filename or NOMBRE_ARCHIVO)
    guardada = RepositorioImportacion(sesion).agregar(
        Importacion(
            archivo_nombre=preview.archivo_nombre,
            estado=ESTADO_PREVIEW,
            resumen=preview.a_json(),
        )
    )
    _guardar_hallazgos(sesion, guardada.id, preview)
    sesion.commit()
    return _respuesta(guardada, preview)


@router.patch("/{importacion_id}/filas")
def corregir_filas(
    importacion_id: uuid.UUID,
    cuerpo: CorreccionesCuerpo,
    sesion: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Corrige celdas y revalida el libro completo."""
    guardada = _obtener(sesion, importacion_id)
    if guardada.estado == ESTADO_CONFIRMADA:
        raise HTTPException(
            status_code=409,
            detail="La importación ya fue confirmada: sube el archivo de nuevo para corregir.",
        )

    hojas = hojas_de_preview(guardada.resumen or {})
    try:
        hojas = aplicar_correcciones(
            hojas,
            [
                Correccion(
                    hoja=correccion.hoja,
                    fila=correccion.fila,
                    columna=correccion.columna,
                    valor=correccion.valor,
                )
                for correccion in cuerpo.correcciones
            ],
        )
    except CorreccionInvalida as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    preview = analizar_libro(hojas, archivo_nombre=guardada.archivo_nombre)
    repositorio = RepositorioImportacion(sesion)
    actualizada = repositorio.actualizar(
        dataclasses.replace(guardada, resumen=preview.a_json(), updated_at=utcnow())
    )
    _guardar_hallazgos(sesion, actualizada.id, preview)
    sesion.commit()
    return _respuesta(actualizada, preview)


@router.post("/{importacion_id}/confirmar")
def confirmar(
    importacion_id: uuid.UUID,
    sesion: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    """Escribe el plan en una transacción, con upsert por clave natural (D-009)."""
    guardada = _obtener(sesion, importacion_id)
    preview = analizar_libro(
        hojas_de_preview(guardada.resumen or {}), archivo_nombre=guardada.archivo_nombre
    )
    if not preview.confirmable:
        raise HTTPException(
            status_code=409,
            detail="La importación no tiene filas válidas para confirmar.",
        )

    repositorio = RepositorioImportacion(sesion)
    try:
        resultado = confirmar_importacion(sesion, preview)
        resumen = preview.a_json()
        resumen["resultado"] = resultado.a_json()
        actualizada = repositorio.actualizar(
            dataclasses.replace(
                guardada,
                estado=ESTADO_CONFIRMADA,
                resumen=resumen,
                updated_at=utcnow(),
            )
        )
        _guardar_hallazgos(sesion, actualizada.id, preview)
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise

    return {
        "id": str(actualizada.id),
        "estado": actualizada.estado,
        "escritura": resultado.a_json(),
        "conteos": dict(preview.conteos),
        "codigos": sorted({hallazgo.codigo for hallazgo in preview.hallazgos}),
    }

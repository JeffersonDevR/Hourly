"""Reglas en lenguaje natural → disponibilidad base del docente.

El contrato de D-004/D-021: la regla vuelve **editable**, el usuario la confirma y recién
ahí se escribe. No hay tabla `regla`: una restricción de un docente en un día/bloque es
exactamente `disponibilidad_bloqueo` con `origen=personal`.

La interpretación tiene tres orígenes, en este orden: parser determinista (8a, sin red),
proveedor de IA (8b) y modo manual (la tarjeta vacía para que el usuario elija).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.ai import interpretar_determinista, proveedor
from app.ai.base import ReglaEstructurada
from app.domain.carga import DisponibilidadBloqueo
from app.domain.enums import OrigenBloqueo
from app.repositories.carga import RepositorioDisponibilidad
from app.repositories.catalogo import RepositorioBloque, RepositorioDocente
from app.routers.comun import error

MENSAJE_MANUAL = (
    "No se pudo interpretar la frase. Elegí el docente, el día y el bloque a mano: la regla "
    "no se guarda hasta que la confirmes."
)


def contexto(sesion: Session) -> dict[str, Any]:
    """Catálogo mínimo para el proveedor: códigos, no ids."""
    return {
        "docentes": [
            {"codigo": docente.codigo, "nombre": docente.nombre}
            for docente in RepositorioDocente(sesion).listar()
        ],
        "bloques": [
            {"codigo": bloque.codigo, "orden": bloque.orden}
            for bloque in sorted(
                (b for b in RepositorioBloque(sesion).listar() if b.tipo == "clase"),
                key=lambda bloque: bloque.orden,
            )
        ],
        "dias": ["lunes", "martes", "miércoles", "jueves", "viernes"],
    }


def _regla_json(regla: ReglaEstructurada, nombre_docente: str) -> dict[str, Any]:
    return {
        "docente_codigo": regla.docente_codigo,
        "docente_nombre": nombre_docente,
        "dias": list(regla.dias),
        "bloque_codigo": regla.bloque_codigo,
        "bloquea": regla.bloquea,
        "motivo": regla.motivo,
    }


def interpretar(sesion: Session, texto: str) -> dict[str, Any]:
    regla = interpretar_determinista(texto)
    origen = "determinista" if regla is not None else "manual"
    if regla is None:
        try:
            regla = proveedor().interpretar_regla(texto, contexto(sesion))
        except Exception:  # sin key, sin red o JSON inválido: se cae al modo manual
            regla = None
        if regla is not None:
            origen = "ia"

    if regla is None:
        return {"regla": None, "origen": "manual", "mensaje": MENSAJE_MANUAL}

    docente = RepositorioDocente(sesion).obtener_por_codigo(regla.docente_codigo)
    if docente is None:
        return {
            "regla": None,
            "origen": "manual",
            "mensaje": f"No existe el docente {regla.docente_codigo}. Elegilo a mano.",
        }
    return {"regla": _regla_json(regla, docente.nombre), "origen": origen, "mensaje": None}


def confirmar(sesion: Session, datos: dict[str, Any]) -> dict[str, Any]:
    """Escribe (o borra) las filas de `disponibilidad_bloqueo`. Idempotente."""
    docente = RepositorioDocente(sesion).obtener_por_codigo(datos["docente_codigo"])
    if docente is None:
        error(400, "REFERENCIA_INVALIDA", f"No existe el docente {datos['docente_codigo']}.")

    bloques = [bloque for bloque in RepositorioBloque(sesion).listar() if bloque.tipo == "clase"]
    if datos.get("bloque_codigo"):
        bloques = [bloque for bloque in bloques if bloque.codigo == datos["bloque_codigo"]]
        if not bloques:
            error(400, "REFERENCIA_INVALIDA", f"No existe el bloque {datos['bloque_codigo']}.")

    dias = sorted({dia for dia in datos["dias"] if 1 <= dia <= 5})
    if not dias:
        error(400, "REFERENCIA_INVALIDA", "Elegí al menos un día de la semana.")

    repo = RepositorioDisponibilidad(sesion)
    detalle = f"Regla: {datos.get('motivo') or 'sin detalle'}"
    creados = 0
    eliminados = 0
    for dia in dias:
        for bloque in bloques:
            existente = repo.obtener_por_franja(docente.id, dia, bloque.id)
            if datos.get("bloquea", True) and existente is None:
                repo.agregar(
                    DisponibilidadBloqueo(
                        docente_id=docente.id,
                        dia=dia,
                        bloque_id=bloque.id,
                        origen=OrigenBloqueo.personal,
                        detalle=detalle,
                    )
                )
                creados += 1
            elif not datos.get("bloquea", True) and existente is not None:
                repo.eliminar(existente.id)
                eliminados += 1

    return {
        "docente_codigo": docente.codigo,
        "dias": dias,
        "bloques": [bloque.codigo for bloque in bloques],
        "bloquea": bool(datos.get("bloquea", True)),
        "creados": creados,
        "eliminados": eliminados,
    }


def sin_cambios(resultado: dict[str, Any]) -> bool:
    """Una confirmación que no escribió nada casi siempre es una regla repetida."""
    return resultado["creados"] == 0 and resultado["eliminados"] == 0


__all__ = ["confirmar", "contexto", "interpretar", "sin_cambios"]

_ = uuid  # el módulo no genera ids propios; se deja para tipos de la firma

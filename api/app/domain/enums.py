"""Enumeraciones del dominio.

`StrEnum` de la stdlib: el paquete `app.domain` no conoce SQLAlchemy (ni FastAPI).
Los modelos reutilizan estos tipos en columnas `VARCHAR + CHECK`
(`native_enum=False`, D-001) para que un valor inválido no llegue a la DB.
"""

from enum import StrEnum


class TipoBloque(StrEnum):
    """Naturaleza del bloque: solo `clase` admite sesiones."""

    clase = "clase"
    descanso = "descanso"
    almuerzo = "almuerzo"


class OrigenBloqueo(StrEnum):
    """Motivo del bloqueo base de un docente (D-005: nunca `escenario`)."""

    personal = "personal"
    otra_sede = "otra_sede"
    otra_institucion = "otra_institucion"


class EstadoVersion(StrEnum):
    borrador = "borrador"
    publicado = "publicado"
    archivado = "archivado"


class Gravedad(StrEnum):
    """Gravedad de un conflicto y a la vez severidad de un error de importación."""

    error = "error"
    advertencia = "advertencia"


class EstadoConflicto(StrEnum):
    abierto = "abierto"
    resuelto = "resuelto"
    ignorado = "ignorado"


class OrigenPropuesta(StrEnum):
    solver = "solver"
    ia = "ia"


class EstadoPropuesta(StrEnum):
    pendiente = "pendiente"
    aceptada = "aceptada"
    rechazada = "rechazada"


class TipoCambioPropuesta(StrEnum):
    mover_sesion = "mover_sesion"
    cambiar_docente = "cambiar_docente"
    cambiar_recurso = "cambiar_recurso"


class ModoDocente(StrEnum):
    principal = "principal"
    habilitados = "habilitados"

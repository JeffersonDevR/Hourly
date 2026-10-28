"""Repositorios de tipos de recurso y recursos."""

from app.domain.recursos import Recurso, TipoRecurso
from app.models.recursos import RecursoDB, TipoRecursoDB
from app.repositories.base import Repositorio, RepositorioCodigo


class RepositorioTipoRecurso(Repositorio[TipoRecursoDB, TipoRecurso, str]):
    """La PK es el código ('GENERAL', 'CANCHA'...)."""

    modelo = TipoRecursoDB


class RepositorioRecurso(RepositorioCodigo[RecursoDB, Recurso]):
    modelo = RecursoDB

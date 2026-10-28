"""Capa de servicios: reglas de negocio y transacciones, por encima de los repositorios.

Los routers (fase 5) llaman a estos servicios; nunca escriben `historial_cambio` ni
mezclan lógica con SQL.
"""

from app.services.historial import registrar_cambio

__all__ = ["registrar_cambio"]

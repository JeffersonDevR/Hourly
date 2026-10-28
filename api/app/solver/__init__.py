"""Solver CP-SAT (OR-Tools) del horario. Paquete puro.

Entra `EstadoHorario` (o un conflicto concreto) y sale `Resultado` o una lista de
propuestas. Nunca importa `app.ai` ni SQLAlchemy: la IA es opcional y posterior
(D-003), y la DB es de la fase 5.

Piezas:

- `greedy`: paso 0 de D-003, reparación local determinista que devuelve propuestas.
- `modelo`: CP-SAT con una booleana por (asignación, docente, día, bloque).
- `recursos`: asignación de aulas posterior al modelo.
- `resolver`: la puerta pública, con `fijas` (D-008) y el diagnóstico de INFACTIBLE.
"""

from app.solver.greedy import PropuestaCambio, reparar_greedy
from app.solver.modelo import PESO_DESBALANCE, PESO_HUECO, PESO_PESADAS
from app.solver.recursos import RECURSO_NO_DISPONIBLE, asignar_recursos
from app.solver.resolver import resolver
from app.solver.resultado import EstadoResultado, Resultado

__all__ = [
    "PESO_DESBALANCE",
    "PESO_HUECO",
    "PESO_PESADAS",
    "RECURSO_NO_DISPONIBLE",
    "EstadoResultado",
    "PropuestaCambio",
    "Resultado",
    "asignar_recursos",
    "reparar_greedy",
    "resolver",
]

"""Modelo CP-SAT del horario: una booleana por (asignación, docente, día, bloque).

Restricciones duras (ARCHITECTURE.md:7):

- cada curso ocupa como máximo una franja por (día, bloque de clase), y exactamente
  una cuando su malla llena la semana (30 sesiones para 30 franjas). La igualdad
  propaga mucho mejor que la cota; con una malla parcial se deja `<= 1` para no
  convertir un dato faltante en INFACTIBLE;
- suma por asignación = `sesiones_semana` (menos las que ya están fijas);
- un docente, como máximo una sesión por franja;
- un docente, como máximo `max_sesiones_semana` sesiones en la semana;
- ninguna sesión en una franja bloqueada o cerrada por el escenario activo.

Objetivo BLANDO (nunca una restricción, D-006): huecos de docentes, desbalance entre
docentes que comparten una asignatura y adyacencia de materias pesadas. Con la grilla
100 % llena, prohibir las adyacencias pesadas haría la instancia INFACTIBLE.

Determinismo y velocidad
------------------------
Un solo worker y semilla fija no alcanzan: el óptimo de "cero huecos" es una aguja
combinatoria y CP-SAT tarda ~13 s en encontrarla (medido). Por eso la mejora tiene un
presupuesto DETERMINISTA (`max_deterministic_time`, unidades de trabajo independientes
de la máquina) además del tope de reloj. Mismo input → mismo plan, mismo objetivo; la
diferencia entre máquinas es cuánto tarda, no qué devuelve. El tope de reloj
(`SOLVER_TIMEOUT_S`) sigue siendo la red de seguridad.

Un presupuesto mayor devuelve horarios con menos huecos (medido: 0.5 → 7 huecos,
1.0 → 6, sin presupuesto → 0 en 13 s). El default prioriza la demo: la generación
completa queda en ~2 s.
"""

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass

from ortools.sat.python import cp_model

from app.domain.horario import Sesion
from app.solver.comun import (
    DIAS,
    bloques_clase,
    docentes_permitidos,
    franjas,
    franjas_bloqueadas,
    pares_adyacentes,
)
from app.solver.resultado import EstadoResultado
from app.validator.estado import EstadoHorario

#: Peso de un hueco en el día de un docente. Calidad, no corrección.
PESO_HUECO = 1
#: Peso de la diferencia de carga entre dos docentes que comparten asignatura. Es lo
#: que reparte Inglés entre D4 y D6 en vez de dejarlo todo en uno.
PESO_DESBALANCE = 3
#: Peso por par adyacente de materias pesadas (D-006). El más caro: es la única regla
#: de calidad que la UI reporta como advertencia.
PESO_PESADAS = 10
#: Semilla fija: con `num_search_workers=1` la corrida es reproducible.
SEMILLA = 42
#: Presupuesto determinista de mejora, en segundos de trabajo de CP-SAT (no de reloj).
#: 0.5 deja la generación de la demo en ~2 s; subirlo mejora la calidad y acerca al
#: óptimo de huecos (que tarda ~4.6 unidades deterministas).
PRESUPUESTO_MEJORA = 0.5

#: (asignación, docente, día, bloque) de una sesión colocada.
Colocacion = tuple[uuid.UUID, uuid.UUID, int, uuid.UUID]


@dataclass(frozen=True, slots=True)
class PlanCP:
    """Lo que devuelve el modelo: estado, colocaciones generadas y objetivo."""

    estado: EstadoResultado
    colocaciones: tuple[Colocacion, ...] = ()
    objetivo: int | None = None


class _Recolector(cp_model.CpSolverSolutionCallback):
    """Guarda la última solución encontrada.

    Con `max_deterministic_time` el solver puede terminar en UNKNOWN teniendo un plan
    válido en la mano; leer `solver.value()` en ese estado es inválido. El callback
    congela la solución cuando aparece. `encontrada` distingue "no hubo solución" de
    "hubo solución sin sesiones generadas" (todo el alcance ya estaba fijo).
    """

    def __init__(self, variables: dict[Colocacion, cp_model.IntVar], hay_objetivo: bool):
        super().__init__()
        self._variables = variables
        self._hay_objetivo = hay_objetivo
        self.encontrada = False
        self.colocaciones: tuple[Colocacion, ...] = ()
        self.objetivo: int | None = None

    def on_solution_callback(self) -> None:
        self.encontrada = True
        self.colocaciones = tuple(
            clave for clave, var in self._variables.items() if self.value(var) == 1
        )
        if self._hay_objetivo:
            self.objetivo = int(round(self.objective_value))


@dataclass(frozen=True, slots=True)
class _Armado:
    """Modelo construido, listo para resolver."""

    modelo: cp_model.CpModel
    variables: dict[Colocacion, cp_model.IntVar]
    tiene_objetivo: bool


def resolver_cpsat(
    estado: EstadoHorario,
    *,
    modo_docente: str,
    escenario: object,
    fijas: tuple[Sesion, ...],
    solo_curso_id: uuid.UUID | None,
    timeout_s: float,
    peso_pesadas: int = PESO_PESADAS,
    presupuesto_mejora: float = PRESUPUESTO_MEJORA,
) -> PlanCP:
    """Resuelve en dos fases: factibilidad garantizada y después mejora blanda.

    Fase 1 — sin objetivo: encuentra *algún* plan válido o demuestra que no existe.
    Es rápida (0.3-0.6 s en la demo) y no tiene presupuesto determinista: cortarla
    dejaría al llamador sin plan. Fase 2 — con el objetivo blando y sin pista: mejora
    el plan dentro de `presupuesto_mejora`. Si la mejora no encuentra nada, se devuelve
    el plan de la fase 1.

    Sin pista a propósito: con `add_hint` CP-SAT salta el presolve y la semilla de la
    fase 1 (que no piensa en calidad) ancla la búsqueda. Medido: con pista el objetivo
    quedaba en 43; sin pista, en 7 con el mismo presupuesto.

    Args:
        estado: foto del horario.
        modo_docente: `principal` o `habilitados` (ver `docentes_permitidos`).
        escenario: objeto o id del escenario activo; su overlay se aplica encima de
            `disponibilidad_bloqueo` (D-005).
        fijas: sesiones que no se mueven. Ocupan franja y capacidad del docente y
            descuentan demanda de su asignación.
        solo_curso_id: si viene, solo se generan las asignaciones de ese curso.
        timeout_s: tope de reloj de cada fase. `<= 0` significa sin límite.
        peso_pesadas: peso de la adyacencia pesada. `0` la desactiva (se usa para
            medir su efecto sin cambiar el resto del modelo).
        presupuesto_mejora: presupuesto determinista de la fase 2. `<= 0` = sin
            límite, solo el tope de reloj (útil para medir el óptimo, no para la demo).
    """
    inicio = time.perf_counter()
    factibilidad = _armar(
        estado,
        modo_docente=modo_docente,
        escenario=escenario,
        fijas=fijas,
        solo_curso_id=solo_curso_id,
        pesos=(0, 0, 0),
    )
    if factibilidad is None:
        return PlanCP(EstadoResultado.INFACTIBLE)

    estado_cp, recolector = _resolver(
        factibilidad, timeout_s=timeout_s, presupuesto_mejora=0
    )
    if estado_cp == cp_model.INFEASIBLE:
        return PlanCP(EstadoResultado.INFACTIBLE)
    if not recolector.encontrada:
        # Ni un plan: el tope de reloj (o un modelo imposible) cortó antes.
        return PlanCP(EstadoResultado.TIMEOUT)

    if presupuesto_mejora <= 0:
        # Sin presupuesto: la fase 2 corre solo con el tope de reloj (medición).
        restante = timeout_s
    else:
        restante = timeout_s - (time.perf_counter() - inicio) if timeout_s > 0 else 0
        if timeout_s > 0 and restante <= 0:
            return PlanCP(EstadoResultado.FACTIBLE, recolector.colocaciones, None)

    mejora = _armar(
        estado,
        modo_docente=modo_docente,
        escenario=escenario,
        fijas=fijas,
        solo_curso_id=solo_curso_id,
        pesos=(PESO_HUECO, PESO_DESBALANCE, peso_pesadas),
    )
    if mejora is None:  # no puede pasar: misma estructura que la fase 1
        return PlanCP(EstadoResultado.FACTIBLE, recolector.colocaciones, None)

    estado_mejora, mejor = _resolver(
        mejora, timeout_s=restante or timeout_s, presupuesto_mejora=presupuesto_mejora
    )
    if not mejor.encontrada:
        return PlanCP(EstadoResultado.FACTIBLE, recolector.colocaciones, None)

    return PlanCP(
        EstadoResultado.OPTIMO
        if estado_mejora == cp_model.OPTIMAL
        else EstadoResultado.FACTIBLE,
        mejor.colocaciones,
        mejor.objetivo,
    )


def _armar(
    estado: EstadoHorario,
    *,
    modo_docente: str,
    escenario: object,
    fijas: tuple[Sesion, ...],
    solo_curso_id: uuid.UUID | None,
    pesos: tuple[int, int, int],
) -> _Armado | None:
    """Modelo completo con las restricciones duras y, si `pesos` no es cero, el objetivo."""
    bloques = bloques_clase(estado)
    if not bloques:
        return None

    peso_huecos, peso_desbalance, peso_pesadas = pesos
    modelo = cp_model.CpModel()
    permitidos = docentes_permitidos(estado, modo_docente)
    bloqueadas = franjas_bloqueadas(estado, escenario)
    todas_las_franjas = franjas(bloques)
    asignaturas = {asignatura.id: asignatura for asignatura in estado.asignaturas}

    # --- Ocupación de las fijas: se resta antes de armar las restricciones. ---
    ocupado_curso: dict[tuple[uuid.UUID, int, uuid.UUID], int] = defaultdict(int)
    ocupado_docente: dict[tuple[uuid.UUID, int, uuid.UUID], int] = defaultdict(int)
    carga_fija: dict[uuid.UUID, int] = defaultdict(int)
    demanda_fija: dict[uuid.UUID, int] = defaultdict(int)
    for sesion in fijas:
        ocupado_curso[(sesion.curso_id, sesion.dia, sesion.bloque_id)] += 1
        ocupado_docente[(sesion.docente_id, sesion.dia, sesion.bloque_id)] += 1
        carga_fija[sesion.docente_id] += 1
        demanda_fija[sesion.asignacion_carga_id] += 1

    en_alcance = [
        asignacion
        for asignacion in estado.asignaciones
        if solo_curso_id is None or asignacion.curso_id == solo_curso_id
    ]

    # --- Variables e índices auxiliares. ---
    variables: dict[Colocacion, cp_model.IntVar] = {}
    por_asignacion: dict[uuid.UUID, list[cp_model.IntVar]] = defaultdict(list)
    por_asignacion_franja: dict[tuple[uuid.UUID, int, uuid.UUID], list] = defaultdict(list)
    por_curso_franja: dict[tuple[uuid.UUID, int, uuid.UUID], list] = defaultdict(list)
    por_docente_franja: dict[tuple[uuid.UUID, int, uuid.UUID], list] = defaultdict(list)
    por_docente: dict[uuid.UUID, list] = defaultdict(list)

    for asignacion in en_alcance:
        for docente in permitidos.get(asignacion.id, ()):
            for dia, bloque in todas_las_franjas:
                if (docente.id, dia, bloque.id) in bloqueadas:
                    continue
                var = modelo.new_bool_var("")
                variables[(asignacion.id, docente.id, dia, bloque.id)] = var
                por_asignacion[asignacion.id].append(var)
                por_asignacion_franja[(asignacion.id, dia, bloque.id)].append(var)
                por_curso_franja[(asignacion.curso_id, dia, bloque.id)].append(var)
                por_docente_franja[(docente.id, dia, bloque.id)].append(var)
                por_docente[docente.id].append(var)

    # --- Duras. ---
    demanda_curso: dict[uuid.UUID, int] = defaultdict(int)
    for asignacion in en_alcance:
        demanda_curso[asignacion.curso_id] += asignacion.sesiones_semana
    malla_completa = {
        curso_id: demanda == len(todas_las_franjas)
        for curso_id, demanda in demanda_curso.items()
    }

    for (curso_id, dia, bloque_id), grupo in por_curso_franja.items():
        ocupadas = ocupado_curso[(curso_id, dia, bloque_id)]
        if malla_completa.get(curso_id):
            modelo.add(sum(grupo) + ocupadas == 1)
        else:
            modelo.add(sum(grupo) + ocupadas <= 1)

    for (docente_id, dia, bloque_id), grupo in por_docente_franja.items():
        modelo.add(sum(grupo) + ocupado_docente[(docente_id, dia, bloque_id)] <= 1)

    for docente in estado.docentes:
        modelo.add(
            sum(por_docente.get(docente.id, [])) + carga_fija[docente.id]
            <= max(docente.max_sesiones_semana, 0)
        )

    for asignacion in en_alcance:
        restantes = asignacion.sesiones_semana - demanda_fija[asignacion.id]
        modelo.add(sum(por_asignacion[asignacion.id]) == restantes)

    # --- Blandas. ---
    terminos = []

    if peso_huecos > 0:
        huecos = _variables_de_huecos(modelo, estado, bloques, por_docente_franja)
        if huecos:
            terminos.append(peso_huecos * sum(huecos))

    if peso_desbalance > 0:
        desbalances = _variables_de_desbalance(
            modelo, en_alcance, permitidos, por_docente, carga_fija
        )
        if desbalances:
            terminos.append(peso_desbalance * sum(desbalances))

    if peso_pesadas > 0:
        pesadas = _variables_de_pesadas(
            modelo, en_alcance, asignaturas, por_asignacion_franja, bloques
        )
        if pesadas:
            terminos.append(peso_pesadas * sum(pesadas))

    if terminos:
        modelo.minimize(sum(terminos))

    return _Armado(modelo, variables, tiene_objetivo=bool(terminos))


def _resolver(
    armado: _Armado, *, timeout_s: float, presupuesto_mejora: float
) -> tuple[int, _Recolector]:
    """Una resolución del modelo ya armado, con los parámetros de reproducibilidad."""
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = SEMILLA
    if timeout_s > 0:
        solver.parameters.max_time_in_seconds = timeout_s
    if presupuesto_mejora > 0:
        solver.parameters.max_deterministic_time = presupuesto_mejora

    recolector = _Recolector(armado.variables, hay_objetivo=armado.tiene_objetivo)
    estado_cp = solver.solve(armado.modelo, recolector)
    if estado_cp == cp_model.MODEL_INVALID:
        raise RuntimeError(f"Modelo CP-SAT inválido: {solver.response_proto.solution_info}")
    return estado_cp, recolector


def _variables_de_huecos(
    modelo: cp_model.CpModel,
    estado: EstadoHorario,
    bloques: tuple,
    por_docente_franja: dict,
) -> list[cp_model.IntVar]:
    """Huecos de un docente en un día: `última - primera + 1 - sesiones del día`.

    Sin esto la calidad del horario no se mide: un docente puede quedar con una clase
    a primera hora y otra a última, con horas muertas en el medio. La formulación
    trabaja sobre `primera` y `última` (dos enteros por docente y día) en vez de un
    AND de tres booleanos por bloque: es la misma cuenta, con 90 variables en lugar
    de 600 y sin el plateau que hacía que CP-SAT tardara 55 s en demostrar el óptimo.
    """
    huecos: list[cp_model.IntVar] = []
    ancho = len(bloques)
    if ancho < 3:
        return huecos

    for docente in estado.docentes:
        for dia in DIAS:
            usados = [
                sum(por_docente_franja.get((docente.id, dia, bloque.id), []))
                for bloque in bloques
            ]
            # `primera` = min(k tal que usados[k] = 1), con `ancho` si no hay clases:
            # el término vale `ancho` cuando la franja está libre y `k` cuando se usa.
            primera = modelo.new_int_var(0, ancho, "")
            modelo.add_min_equality(
                primera,
                [ancho - (ancho - posicion) * usados[posicion] for posicion in range(ancho)],
            )
            ultima = modelo.new_int_var(0, ancho - 1, "")
            modelo.add_max_equality(
                ultima, [posicion * usados[posicion] for posicion in range(ancho)]
            )

            hueco = modelo.new_int_var(0, ancho, "")
            modelo.add(hueco >= ultima - primera + 1 - sum(usados))
            huecos.append(hueco)
    return huecos


def _variables_de_desbalance(
    modelo: cp_model.CpModel,
    en_alcance: list,
    permitidos: dict,
    por_docente: dict,
    carga_fija: dict,
) -> list[cp_model.IntVar]:
    """`|carga_a - carga_b|` para cada par que comparte una asignatura repartible.

    Con el Excel real el único par es (D4, D6) por Inglés: es exactamente lo que pide
    "repartir la carga entre D4 y D6 cuando Inglés es divisible".
    """
    pares: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for asignacion in en_alcance:
        candidatos = [docente.id for docente in permitidos.get(asignacion.id, ())]
        for indice, primero in enumerate(candidatos):
            for segundo in candidatos[indice + 1 :]:
                pares.add((primero, segundo) if str(primero) < str(segundo) else (segundo, primero))

    if not pares:
        return []

    maximo = sum(asignacion.sesiones_semana for asignacion in en_alcance) + sum(
        carga_fija.values()
    )
    desbalances: list[cp_model.IntVar] = []
    for primero, segundo in sorted(pares, key=lambda par: (str(par[0]), str(par[1]))):
        carga_primero = sum(por_docente.get(primero, [])) + carga_fija.get(primero, 0)
        carga_segundo = sum(por_docente.get(segundo, [])) + carga_fija.get(segundo, 0)
        var = modelo.new_int_var(0, max(maximo, 0), "")
        modelo.add(var >= carga_primero - carga_segundo)
        modelo.add(var >= carga_segundo - carga_primero)
        desbalances.append(var)
    return desbalances


def _variables_de_pesadas(
    modelo: cp_model.CpModel,
    en_alcance: list,
    asignaturas: dict,
    por_asignacion_franja: dict,
    bloques: tuple,
) -> list[cp_model.IntVar]:
    """`y >= x_b + x_{b+1} - 1` por par adyacente con dos materias pesadas (D-006)."""
    pesadas: list[cp_model.IntVar] = []
    for curso_id in sorted({asignacion.curso_id for asignacion in en_alcance}, key=str):
        pesadas_del_curso = [
            asignacion.id
            for asignacion in en_alcance
            if asignacion.curso_id == curso_id
            and getattr(asignaturas.get(asignacion.asignatura_id), "es_pesada", False)
        ]
        if not pesadas_del_curso:
            continue
        for dia in DIAS:
            for primero, segundo in pares_adyacentes(bloques):
                antes = [
                    var
                    for asignacion_id in pesadas_del_curso
                    for var in por_asignacion_franja.get((asignacion_id, dia, primero.id), [])
                ]
                despues = [
                    var
                    for asignacion_id in pesadas_del_curso
                    for var in por_asignacion_franja.get((asignacion_id, dia, segundo.id), [])
                ]
                if not antes or not despues:
                    continue
                var = modelo.new_bool_var("")
                modelo.add(var >= sum(antes) + sum(despues) - 1)
                pesadas.append(var)
    return pesadas

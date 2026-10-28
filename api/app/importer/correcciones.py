"""Corrección en línea de celdas antes de confirmar (`PATCH .../filas`).

El cliente manda `(hoja, fila, columna, valor)` con los mismos identificadores que
vio en el hallazgo. La corrección se aplica sobre las `HojaCruda` guardadas en
`importacion.resumen` y el libro se reanaliza completo: no hay una segunda ruta de
validación que pueda quedar desincronizada de la primera.
"""

from dataclasses import dataclass, replace
from typing import Any

from app.importer.coercion import a_texto, sin_acentos
from app.importer.lectura import HojaCruda


class CorreccionInvalida(ValueError):
    """La hoja, la fila o la columna de la corrección no existen en el libro."""


@dataclass(frozen=True, slots=True)
class Correccion:
    hoja: str
    fila: int
    columna: str
    valor: Any = None


def _buscar(hojas: dict[str, HojaCruda], nombre: str) -> HojaCruda:
    buscado = sin_acentos(nombre)
    for clave, hoja in hojas.items():
        if sin_acentos(clave) == buscado:
            return hoja
    raise CorreccionInvalida(f"La hoja '{nombre}' no existe en la importación.")


def _columna(hoja: HojaCruda, nombre: str) -> int:
    """Índice de la columna: por encabezado o, si no, por letra de Excel ('D')."""
    indice = hoja.indice(nombre)
    if indice is not None:
        return indice
    letra = nombre.strip().upper()
    if len(letra) == 1 and letra.isalpha():
        desde_letra = ord(letra) - ord("A")
        if desde_letra < len(hoja.encabezado):
            return desde_letra
    raise CorreccionInvalida(
        f"La columna '{nombre}' no existe en la hoja '{hoja.nombre}' "
        f"(encabezados: {', '.join(hoja.encabezado)})."
    )


def aplicar_correcciones(
    hojas: dict[str, HojaCruda], correcciones: tuple[Correccion, ...] | list[Correccion]
) -> dict[str, HojaCruda]:
    """Devuelve una copia de `hojas` con las celdas corregidas."""
    resultado = dict(hojas)
    for correccion in correcciones:
        hoja = _buscar(resultado, correccion.hoja)
        indice = _columna(hoja, correccion.columna)
        objetivo = next((fila for fila in hoja.filas if fila.numero == correccion.fila), None)
        if objetivo is None:
            raise CorreccionInvalida(
                f"La fila {correccion.fila} no existe en la hoja '{hoja.nombre}'."
            )
        celdas = list(objetivo.celdas)
        celdas.extend([None] * (indice + 1 - len(celdas)))
        celdas[indice] = None if correccion.valor is None else correccion.valor
        filas = tuple(
            replace(fila, celdas=tuple(celdas)) if fila.numero == objetivo.numero else fila
            for fila in hoja.filas
        )
        resultado[hoja.nombre] = replace(hoja, filas=filas)
    return resultado


def correcciones_desde_json(datos: list[dict[str, Any]]) -> tuple[Correccion, ...]:
    """Valida el cuerpo del PATCH y lo convierte en `Correccion`."""
    correcciones: list[Correccion] = []
    for entrada in datos:
        hoja = a_texto(entrada.get("hoja"))
        columna = a_texto(entrada.get("columna"))
        fila = entrada.get("fila")
        if hoja is None or columna is None or not isinstance(fila, int) or isinstance(fila, bool):
            raise CorreccionInvalida(
                "Cada corrección necesita 'hoja' (texto), 'fila' (entero) y 'columna' (texto)."
            )
        correcciones.append(
            Correccion(hoja=hoja, fila=fila, columna=columna, valor=entrada.get("valor"))
        )
    return tuple(correcciones)

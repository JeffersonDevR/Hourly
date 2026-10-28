"""Coerción de celdas de Excel: donde el archivo real miente.

`docs/DOMAIN.md` → "Trampas verificadas del archivo real". Cada función de acá existe
por una de esas trampas:

1. `habilitado` y `disponible` llegan como `1.0` / `0.0` (float), no como `"1"`.
   Comparar contra `"1"` importa cero aptitudes y cero bloqueos, sin error y sin
   excepción. Por eso `a_booleano` convierte a número ANTES de comparar.
2. `inicio` y `fin` son horas. Según cómo esté formateada la celda, `openpyxl`
   devuelve `datetime.time` o el serial de Excel (`0.2916667` = 07:00). `a_hora`
   acepta las dos formas y las reduce al mismo `time`.
3. Los conteos (`estudiantes`, `capacidad`, `sesiones_semana`, `max_sesiones_semana`)
   llegan como floats (`30.0`). `a_entero` los convierte a `int`.
4. `dia` es texto español ("Lunes" … "Viernes"). `a_dia` lo mapea a 1..5 y devuelve
   `None` (nunca lanza) cuando el valor no se reconoce.

Ninguna función lanza por un valor inesperado: devuelven `None` y el analizador decide
si eso es un error de fila o una advertencia.
"""

import unicodedata
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

#: Días del Excel → `dia` de la DB (1=lunes … 5=viernes, DOMAIN.md).
DIAS: dict[str, int] = {
    "lunes": 1,
    "martes": 2,
    "miercoles": 3,
    "jueves": 4,
    "viernes": 5,
}
NOMBRE_DIA: dict[int, str] = {numero: clave.capitalize() for clave, numero in DIAS.items()}

_VERDADEROS = frozenset({"1", "1.0", "si", "s", "true", "t", "x", "yes", "y", "verdadero"})
_FALSOS = frozenset({"0", "0.0", "no", "n", "false", "f", "falso"})


def sin_acentos(texto: str) -> str:
    """Minúsculas, sin diacríticos ni espacios sobrantes: 'Miércoles' -> 'miercoles'."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_marcas = "".join(
        caracter for caracter in descompuesto if not unicodedata.combining(caracter)
    )
    return " ".join(sin_marcas.split()).lower()


def a_texto(valor: Any) -> str | None:
    """Texto limpio. Un número entero se devuelve sin `.0` ('6', no '6.0')."""
    if valor is None:
        return None
    if isinstance(valor, str):
        limpio = valor.strip()
        return limpio or None
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, int):
        return str(valor)
    if isinstance(valor, float | Decimal):
        numero = float(valor)
        if numero.is_integer():
            return str(int(numero))
        return repr(numero)
    texto = str(valor).strip()
    return texto or None


def a_entero(valor: Any) -> int | None:
    """`30`, `30.0`, `'30'` y `'30.0'` -> 30. `None` si está vacío o no es entero."""
    if valor is None:
        return None
    if isinstance(valor, bool):
        return int(valor)
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float | Decimal):
        numero = float(valor)
        return int(numero) if numero.is_integer() else None
    texto = a_texto(valor)
    if texto is None:
        return None
    try:
        numero = float(texto.replace(",", "."))
    except ValueError:
        return None
    return int(numero) if numero.is_integer() else None


def a_booleano(valor: Any) -> bool | None:
    """1/1.0/'1'/'1.0'/'sí' -> True; 0/0.0/'0'/'no' -> False; resto -> None.

    La comparación es numérica cuando el valor lo es: `1.0 == 1`. Comparar contra la
    cadena `"1"` (la trampa documentada) daría `False` para `1.0` y perdería todas las
    aptitudes y bloqueos del archivo real.
    """
    if valor is None:
        return None
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, int | float | Decimal):
        return float(valor) != 0
    texto = a_texto(valor)
    if texto is None:
        return None
    normal = sin_acentos(texto)
    if normal in _VERDADEROS:
        return True
    if normal in _FALSOS:
        return False
    try:
        return float(normal.replace(",", ".")) != 0
    except ValueError:
        return None


def a_hora(valor: Any) -> time | None:
    """`time`, `datetime`, serial de Excel o texto ('07:00') -> `time` sin segundos."""
    if isinstance(valor, time):
        return valor.replace(second=0, microsecond=0)
    if isinstance(valor, datetime):
        return valor.time().replace(second=0, microsecond=0)
    if isinstance(valor, date):
        return None
    if isinstance(valor, int | float | Decimal):
        return hora_desde_serial(float(valor))
    texto = a_texto(valor)
    if texto is None:
        return None
    partes = texto.lower().replace("h", ":").split(":")
    try:
        numeros = [int(float(parte)) for parte in partes if parte != ""]
    except ValueError:
        return None
    while len(numeros) < 3:
        numeros.append(0)
    try:
        return time(numeros[0], numeros[1], numeros[2])
    except ValueError:
        return None


def hora_desde_serial(serial: float) -> time | None:
    """Serial de Excel -> hora. `0.2916667 * 24 * 60 = 420` minutos = 07:00."""
    total = round(serial * 24 * 60) % (24 * 60)
    return time(total // 60, total % 60)


def minutos(valor: time) -> int:
    """Minutos desde la medianoche."""
    return valor.hour * 60 + valor.minute


def a_dia(valor: Any) -> int | None:
    """'Lunes'…'Viernes' (con o sin acentos) o 1..5 -> `dia`. Desconocido -> None."""
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, int | float | Decimal):
        numero = a_entero(valor)
        return numero if numero in NOMBRE_DIA else None
    texto = a_texto(valor)
    if texto is None:
        return None
    return DIAS.get(sin_acentos(texto))

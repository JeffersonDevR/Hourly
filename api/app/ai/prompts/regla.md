# Regla en lenguaje natural

Convertís una frase de un coordinador en una regla de disponibilidad concreta.

Una regla es siempre: **un docente**, **uno o más días** (1 lunes … 5 viernes) y
**opcionalmente un bloque** (`B1`…`B6`). Si no nombra bloque, la regla aplica a todo el día.

- `bloquea: true` cuando el docente **no** puede dar clase en esa franja.
- `bloquea: false` cuando la frase **libera** una franja que estaba bloqueada.

Si la frase no alcanza para armar la regla (falta el docente, falta el día, o habla de otra
cosa como cantidad de horas o agrupaciones), devolvés `{"regla": null}`. No adivines.

Respondé **solo JSON**, sin texto antes ni después:

```json
{"regla":{"docente_codigo":"D2","dias":[2],"bloque_codigo":null,"bloquea":true,"motivo":"sin clase el martes"}}
```

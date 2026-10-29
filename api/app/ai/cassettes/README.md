# Cassettes del asistente

Respuestas guardadas para que el asistente siga contestando si en el pitch falla la red
(D-002: "el piso de la demo").

## Qué hay y por qué

| Archivo | Método | Estado |
|---|---|---|
| `interpretar_regla.json` | `interpretar_regla` | **Semilla escrita a mano**, no grabada de un proveedor real |
| `explicar_y_proponer.json` | — | **No existe a propósito** (ver abajo) |

**Provenance:** en la máquina de desarrollo no hay `AI_API_KEY`, así que no se pudo grabar una
respuesta real. El archivo actual sigue el contrato de `app/ai/prompts/regla.md` y está validado por
un test (`tests/test_ia.py::test_cassette_sembrado_cumple_el_contrato`). Para reemplazarlo por uno
grabado de verdad:

```bash
AI_CASSETTE_RECORD=1 \
AI_BASE_URL=https://api.openai.com/v1 AI_MODEL=gpt-4o-mini AI_API_KEY=sk-... \
uv run --directory api pytest tests/test_ia.py
```

**Por qué no hay cassette de propuestas:** una propuesta `explicar_y_proponer` referencia
`sesion_id`, y esos ids son `uuid5(version, asignación, día, bloque)`. Como la versión se crea con un
`uuid4` nuevo en cada corrida, un `sesion_id` grabado **nunca** coincide con la base del pitch: la
propuesta se descartaría en el filtro de simulación (que es lo correcto) y el usuario vería "sin
propuestas". El piso para propuestas es la **alerta determinista** de `diagnosticar_carga`
(D-003 paso 4), que no depende de la red ni de ids.

**Limitación del cassette de reglas:** guarda una sola respuesta, así que cualquier frase que el
parser determinista no entienda devuelve la misma regla. Es un piso, no un asistente.

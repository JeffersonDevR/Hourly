---
description: Fase 8 — IA desacoplada: propuestas de resolución, modo revisión y lenguaje natural a reglas
---
Implementa `app/ai` según el contrato de docs/ARCHITECTURE.md: `AIProvider`, `OpenAICompatibleProvider` (SDK `openai` contra `/v1/chat/completions`, JSON validado con Pydantic, timeout y 1 reintento; env `AI_BASE_URL`/`AI_MODEL`/`AI_API_KEY`), `NullProvider` y `CassetteProvider`. El `CassetteProvider` es obligatorio: graba una respuesta real por método (`explicar_y_proponer`, `interpretar_regla`) en un fixture JSON y la replaya si el provider live falla o hace timeout. Prompts del sistema en `app/ai/prompts/*.md`, en español, tono claro, breve y sugerente.
Backend: `POST /conflictos/{id}/propuestas` (solver → IA → alerta con diagnóstico), simulación y validación de cada propuesta antes de mostrarla, aceptar/rechazar con historial y deshacer, `POST /reglas/interpretar` y **`POST /reglas/confirmar`**.
- `interpretar_regla` intenta primero el parser determinista de patrones (D-004) y solo delega en el provider si ningún patrón matchea.
- Las propuestas `cambiar_docente` se validan contra `aptitud` y contra la capacidad restante de `max_sesiones_semana` del docente destino.

**Reglas en lenguaje natural — dos bloques separados, y el primero NO necesita proveedor:**

**8a — Parser determinista + confirmación (sin IA, sin red, sin API key).** Es lo que exige D-004 y lo que `POST /reglas/interpretar` no define: **dónde aterriza la regla confirmada**. No hay tabla `regla` en `DOMAIN.md` y no hace falta agregar una.
- `ReglaEstructurada` = `{docente_id, dia, bloque_id | None, motivo}`, que es exactamente `disponibilidad_bloqueo`. Confirmar una regla = escribir (o borrar) una fila de `disponibilidad_bloqueo` con `origen=personal` y `detalle="Regla interpretada: <texto original>"`. El validador y el solver ya la respetan sin tocar nada.
- El parser cubre las ~6 formas de D-004 (`D1 no puede los martes`, `D3 libre el viernes B6`, `D2 no disponible lunes y miércoles`). Si ningún patrón matchea **y no hay provider**, no se inventa una regla: se devuelve la tarjeta en modo manual con docente/día/bloque vacíos y un mensaje explícito. Nunca "no entendí" y punto.
- `POST /reglas/confirmar` recibe la regla ya editada por el usuario y es el único que escribe. Nunca se activa sola (ARCHITECTURE.md).
- Pruebas: cada patrón, un texto que no matchea, y que confirmar una regla existente no duplique (`UNIQUE(docente_id, dia, bloque_id)`).

**8b — Provider real.** Recién acá entra `OpenAICompatibleProvider` + `CassetteProvider` para el caso que ningún patrón cubre y para `explicar_y_proponer`. Si el provider falla o expira, 8a sigue funcionando: la pantalla cae al modo manual.
Frontend `/conflictos`: lista agrupada por tipo y gravedad con filtros; detalle con mini-cuadrícula; estados visibles (solver intentando → propuestas de IA → modo revisión antes/después → alerta si nadie resuelve); confirmación antes de aplicar. Aviso "Asistente IA no disponible" sin romper nada. En `/reglas`: cuadro de lenguaje natural con tarjeta "Regla interpretada" editable. Con 8a sola (sin provider) la tarjeta funciona igual: el parser determinista llena docente/día/bloque y el usuario confirma.
Pruebas: golden #5 y #6 con proveedor simulado, más un test con el provider live apagado que verifica que `CassetteProvider` responde `explicar_y_proponer` e `interpretar_regla` desde el fixture.
Criterios: escenario de la demo (principal fijo → falla → IA propone pasar Inglés a D6 → aceptar → verde) funciona de punta a punta; con `NullProvider` se muestra la alerta determinista.
$ARGUMENTS

---
description: Fase 8 — IA desacoplada: propuestas de resolución, modo revisión y lenguaje natural a reglas
---
Implementa `app/ai` según el contrato de docs/ARCHITECTURE.md: `AIProvider`, `OpenAICompatibleProvider` (SDK `openai` contra `/v1/chat/completions`, JSON validado con Pydantic, timeout y 1 reintento; env `AI_BASE_URL`/`AI_MODEL`/`AI_API_KEY`), `NullProvider` y `CassetteProvider`. El `CassetteProvider` es obligatorio: graba una respuesta real por método (`explicar_y_proponer`, `interpretar_regla`) en un fixture JSON y la replaya si el provider live falla o hace timeout. Prompts del sistema en `app/ai/prompts/*.md`, en español, tono claro, breve y sugerente.
Backend: `POST /conflictos/{id}/propuestas` (solver → IA → alerta con diagnóstico), simulación y validación de cada propuesta antes de mostrarla, aceptar/rechazar con historial y deshacer, `POST /reglas/interpretar`.
- `interpretar_regla` intenta primero el parser determinista de patrones (D-004) y solo delega en el provider si ningún patrón matchea.
- Las propuestas `cambiar_docente` se validan contra `aptitud` y contra la capacidad restante de `max_sesiones_semana` del docente destino.
Frontend `/conflictos`: lista agrupada por tipo y gravedad con filtros; detalle con mini-cuadrícula; estados visibles (solver intentando → propuestas de IA → modo revisión antes/después → alerta si nadie resuelve); confirmación antes de aplicar. Aviso "Asistente IA no disponible" sin romper nada. En `/reglas`: cuadro de lenguaje natural con tarjeta "Regla interpretada" editable.
Pruebas: golden #5 y #6 con proveedor simulado, más un test con el provider live apagado que verifica que `CassetteProvider` responde `explicar_y_proponer` e `interpretar_regla` desde el fixture.
Criterios: escenario de la demo (principal fijo → falla → IA propone pasar Inglés a D6 → aceptar → verde) funciona de punta a punta; con `NullProvider` se muestra la alerta determinista.
$ARGUMENTS

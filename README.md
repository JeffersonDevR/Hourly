# Houry — Kit OpenCode

Esta carpeta **es** el proyecto: ejecuta `git init` aquí y abre OpenCode en este directorio.
No copies nada a la raíz del workspace.

## Orden de trabajo
1. **Diseño: ya está hecho.** Vive en `design/stitch/`. Empieza por `design/stitch/README.md`:
   es el índice único con el sistema, las 11 pantallas, los tokens y los defectos abiertos.
   Para implementar, los tokens salen de `design/stitch/tokens.css`.
2. En OpenCode ejecuta, en orden y revisando cada resultado antes de seguir:
   `/fase-00-scaffold` → `/fase-01-db` → `/fase-02-import` → `/fase-03-validator` → `/fase-04-solver` → `/fase-05-api` → `/fase-06-ui-shell` → `/fase-07-ui-grid` → `/fase-08-conflicts-ai` → `/fase-09-scenario-publish` → `/fase-10-demo`
   Opcional: `/extra-vision-import`.
3. Al cerrar cada fase puedes invocar al subagente `@revisor`.

Cada comando acepta texto extra: `/fase-04-solver prioriza equilibrar la carga entre D4 y D6`.

## Archivos
- `AGENTS.md`: reglas persistentes que OpenCode carga siempre.
- `opencode.json`: instrucciones adicionales y permisos (comandos de bash permitidos).
- `docs/DOMAIN.md` y `docs/ARCHITECTURE.md`: fuente de verdad del modelo, la API, el solver y la IA.
- `.opencode/commands/`: un prompt por fase. `.opencode/agents/revisor.md`: revisor de solo lectura.
- `data/Datos_prueba_Gnosoft.xlsx`: datos de prueba.

Si tu versión de OpenCode no encuentra los comandos o el agente, revisa la ruta (`.opencode/commands/` y `.opencode/agents/`) y la documentación en opencode.ai/docs.

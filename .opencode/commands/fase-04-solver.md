---
description: Fase 4 — solver CP-SAT con modos de docente, escenario, regeneración parcial y diagnóstico
---
Implementa `app/solver` según docs/ARCHITECTURE.md.
- **Paso 0 — reparación local greedy** (D-003), antes de cualquier CP-SAT o llamada a IA: mover sesión a franja libre válida, cambiar docente por `aptitud` con capacidad, o cambiar recurso por tipo+capacidad. Determinista y <100 ms.
- Modelo CP-SAT descrito allí; asignación de recursos en un paso posterior (tipo + capacidad, preferir aula titular).
- Parámetros: `modo_docente` (principal|habilitados), `escenario_id`, `solo_curso_id` / `fijas`, `limpiar`, `timeout_s`. `fijas` por defecto son las sesiones ya existentes de la versión; `limpiar=true` es lo único que las borra (D-008).
- Objetivo suave: minimizar huecos de docentes, repartir la carga entre D4 y D6 de forma equilibrada, y penalizar materias pesadas consecutivas (D-006; formulación en ARCHITECTURE.md). La penalidad de `es_pesada` NUNCA puede volverse restricción dura: con la grilla 100% llena la instancia se vuelve INFACTIBLE.
- Asignación de recursos: si no hay aula del tipo correcto y con capacidad libre en esa franja, reportarlo como caso diagnosticable en vez de dejar un `RECURSO_*` silencioso.
- INFACTIBLE → devolver `diagnostico` de `diagnosticar_carga` con causas legibles.
- Registrar `ejecucion_solver` y exponer `POST /horarios/{v}/generar`.
- El solver NO puede importar `app.ai` (test que lo verifique). Cadena completa: greedy → CP-SAT con `fijas` → IA → `diagnosticar_carga` (D-003).
Pruebas: golden #2, #3 y #4 de ARCHITECTURE.md; todo resultado pasa por `validar()` sin errores.
Criterios: golden en verde; generación completa < 10 s en la demo.
$ARGUMENTS

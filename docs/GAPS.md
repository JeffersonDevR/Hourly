# GAPS.md — casos abiertos

Solo lo que **sigue sin resolver**. Todo lo demás que estaba acá se cerró y vive en
`DECISIONS.md`; si dudás de un caso viejo, la respuesta está en la decisión, no en este archivo.
Estado: `abierto` hasta que se resuelva en la fase o en `DECISIONS.md`.

| Caso | Por qué importa | Dónde | Tipo |
|---|---|---|---|
| Demanda por curso ≠ 30 indiagnosticable: `diagnosticar_carga` es solo aritmética de docentes y CP-SAT pone `<= 1` sesión por (día,bloque) por curso | **medio** — un Excel sucio produce un diagnóstico "D4" por una causa no relacionada | `fase-04`, `ARCHITECTURE.md:5` | faltante |
| `propuesta_cambio.cambiar_docente` sobre `sesion_id` o `asignacion_carga_id` sin regla: mutar la asignación reescribe otras versiones; mutar solo la sesión se revierte en el próximo solve | **medio** — el "pasá Inglés a D6" del guion se evapora al regenerar | `fase-08`, `DOMAIN.md:31` | faltante |
| DB vacía en primer arranque: `institucion` es "una sola fila" pero nadie la inserta; `/api/estado` y `/horario` sin definir con 0 filas | **bajo** — es lo que ve un jurado tras `clone && demo.ps1` si la importación falla | `fase-00`, `fase-05` | faltante |

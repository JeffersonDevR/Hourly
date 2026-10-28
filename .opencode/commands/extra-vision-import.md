---
description: Extra opcional — importar horario existente desde PDF o foto con visión de IA
---
Solo si las fases 0–9 están completas. Añade al importador la lectura de un horario existente en PDF/imagen mediante visión del modelo (vía `AIProvider`, método `extraer_horario(archivo)`), devolviendo sesiones candidatas (curso, asignatura, docente, día, bloque) con nivel de confianza. Se muestran en el paso "Revisar" para corregir, y luego se audita con el validador como cualquier horario. Sin IA disponible: mensaje claro y fallback a Excel. Requiere un modelo con capacidad de visión: si `AI_MODEL` apunta a un modelo solo-texto (p. ej. un Ollama local), `extraer_horario` debe fallar explícito y ofrecer el mapeo manual de columnas, nunca devolver sesiones inventadas. Pruebas con un PDF de ejemplo generado en el test.
$ARGUMENTS

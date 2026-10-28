# DEMO.md — guion de 3 minutos

Pitch: *"No empieces de cero: partimos del horario que ya tienes y en segundos lo auditamos, lo corregimos y lo dejamos listo para publicar."*

1. **Arranque pre-cargado.** `.\demo.ps1` deja la DB reseteada, el Excel importado y el horario resuelto, con un conflicto abierto (D4 con 28 sesiones, máx. 24), una propuesta válida y un ejemplo de regla en lenguaje natural (D-007). El pitch NO abre con una importación.
2. **Auditar.** Mostrar el semáforo en ámbar, el conflicto D4 y los avisos de importación (bloques de 60 min vs 50 declarados, sin descansos).
3. **IA** explica en lenguaje simple y propone 2–3 alternativas (p. ej. pasar parte de Inglés a D6). Vista antes/después → **Aceptar** → semáforo en verde.
4. **Publicar** y **exportar** PDF/Excel.
5. **Escenario "¿y si D2 no viene el martes?"** → vista previa de impacto → re-planifica tomando como `fijas` las sesiones no afectadas, propone reasignaciones por aptitud y capacidad → 0 conflictos. **Cierre.**
6. **Importación en vivo:** flujo aparte, se muestra solo si sobra tiempo o si lo piden; nunca es el primer paso del guion.

Plan B: si falla la IA o la red, usar la alerta determinista de `diagnosticar_carga` y las propuestas pregrabadas de `CassetteProvider`.

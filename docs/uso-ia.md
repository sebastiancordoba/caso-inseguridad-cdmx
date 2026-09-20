# Registro de uso de IA generativa

*La rúbrica permite herramientas de IA generativa y exige documentar su uso (§1.1, fila
«Herramientas»). Una entrada por sesión: fecha, qué se pidió, qué se usó de lo que salió y
qué no. Las decisiones —qué encuadre, qué supuestos, qué se afirma— son de Sebastián
Córdoba; aquí se anota qué parte del trabajo hizo la herramienta.*

*Este registro empieza el 2026-09-20. Las sesiones anteriores con asistencia de IA
(verificación de fuentes, `src/descarga.py`, `src/panel.py`, revisión de literatura) quedan
en el historial de git, en los commits con la línea `Co-Authored-By: Claude`; falta
pasarlas a este formato.*

| Fecha | Herramienta | Qué le pedí | Qué produjo | Qué usé |
|---|---|---|---|---|
| 2026-09-20 | Claude Code (Claude Opus 5) | Analizar el repositorio y escribir un `CLAUDE.md` con comandos, arquitectura y convenciones para sesiones futuras | `CLAUDE.md` en la raíz | *Por llenar por Sebas* |
| 2026-09-20 | Claude Code (Claude Fable 5.1) | Investigación de factibilidad, sin código de análisis ni redacción del reporte: cinco encuadres candidatos, cada uno con pregunta, tomador de decisiones, hipótesis falsable, fuentes verificadas con descarga de muestra, método, dashboard, riesgo y antecedentes; ordenarlos y decir cuál descartar | `docs/fase1-encuadres.md`. Para escribirlo: consultó el API del portal de datos de la CDMX, descargó hoy muestras o archivos completos de cada fuente (911, cuadrantes, colonias, afluencia y estaciones del Metro), corrió conteos descriptivos sobre el CSV de la FGJ ya descargado (cobertura de coordenadas, concentración por celda, distancia de robos a estaciones, demora en denunciar, razón llamadas/carpetas) e hizo búsquedas web de antecedentes. Los scripts de esas mediciones fueron desechables y no están en el repo | *Por llenar por Sebas: qué encuadre se eligió y qué de este documento pasó al escrito* |
| 2026-09-20 | Claude Code (Claude Fable 5.1) | Fase 2 del encuadre del Metro, solo datos, pruebas de viabilidad y EDA, sin modelo, dashboard ni reporte: llave de estaciones, panel estación × mes, y las pruebas C1–C3 en orden parando en la primera que fallara | `src/metro/` (`comun.py`, `01_llave_estaciones.py`, `02_panel_estacion.py`, `03_pruebas.py`, `correr.py`), la fuente `metro` en `src/descarga.py`, `docs/decisiones.md` y `docs/fase2-pruebas.md`. La lista de las 28 correspondencias la escribió la herramienta de memoria y el script la contrasta contra el campo `TIPO` del shapefile (coinciden). El criterio de falla de C2 lo propuso la herramienta y quedó escrito antes de correr la prueba. **C2 falló** y la sesión paró ahí: no hay C3, EDA ni `hipotesis.md` | *Por llenar por Sebas: qué se hizo con el encuadre después de C2* |

## Cómo leer lo que produce la herramienta

- Las cifras de `fase1-encuadres.md` salen de archivos descargados, no de la memoria del
  modelo; aun así, las mediciones fueron rápidas y sin revisión. Antes de que una cifra
  entre al escrito se recalcula desde `src/`.
- En los antecedentes, el documento distingue lo leído completo, lo leído en resumen y lo
  que no abrió. Nada de lo marcado como «no abierto» o «resumen del buscador» se cita en el
  escrito sin abrir la fuente.

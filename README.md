# Caso 2 — Inseguridad urbana en la Ciudad de México

Titulación por caso, ITAM.

**Este repositorio guarda el trabajo.**

## Los tres entregables

| # | Qué | Cuándo | Dónde vive aquí |
|---|---|---|---|
| 1 | Trabajo escrito, IEEE doble columna, 5–8 pp. | una semana antes de la presentación | `docs/escrito/` |
| 2 | Aplicación funcional con **repo público** e instrucciones de instalación | demo en vivo el día de la presentación | `app/`, este README |
| 3 | Presentación oral, 15–20 min + 10 de preguntas | slides a los sinodales 24 h antes | `docs/presentacion/` |

Los tres son condición de piso: falta cualquiera y es No Acredita, sin importar la calificación.

## Estructura

```
docs/        entregables escritos y notas de decisión
datos/
  crudos/       descargas tal cual, sin tocar (fuera de git)
  intermedios/  limpiezas parciales (fuera de git)
  procesados/   tablas finales que alimentan el análisis (fuera de git)
notebooks/   exploración; lo que sobreviva se muda a src/
src/         código reutilizable: descarga, limpieza, modelos
app/         la aplicación funcional que se demuestra en vivo
referencias/ PDFs del caso, rúbrica, plantilla IEEE, papers
```

Los datos no se versionan: se reconstruyen con `src/descarga.py`, que deja constancia
de qué se bajó y cuándo en `datos/crudos/MANIFIESTO.md`. Un CSV de 2 GB en git es un
repositorio que nadie puede clonar el día de la demo.

## Reconstruir desde cero

```bash
git clone <url>
cd caso-inseguridad-cdmx
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/descarga.py --fuente fgj
```

*(Las instrucciones completas de instalación son parte calificada del entregable 2.
Se terminan cuando exista la app, no antes.)*

## Fuentes

Ver `datos/FUENTES.md`: URLs verificadas, columnas reales, y las inconsistencias
documentadas que el caso pide caracterizar explícitamente.

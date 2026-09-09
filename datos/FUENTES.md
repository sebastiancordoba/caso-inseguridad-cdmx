# Fuentes de datos

*Verificado el 2026-09-08 contra los portales, no citado de memoria. Cada bloque dice
qué se comprobó y qué sigue sin comprobarse.*

El caso advierte que estas fuentes traen «inconsistencias, cambios de clasificación entre
períodos y brechas» y que **el alumno debe caracterizarlas y manejarlas explícitamente**.
Eso no es una molestia del ejercicio: es la dimensión D2 (10%) y buena parte de los
supuestos explícitos que deciden el 4 en D1–D4. Lo que se encuentre aquí se escribe aquí.

---

## 1. Carpetas de investigación — FGJ CDMX

- Portal: <https://datos.cdmx.gob.mx/dataset/carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico>
- Licencia: CC-BY-4.0. Metadatos modificados el 2026-08-31.
- Acumulado 2016–2024: <https://archivo.datos.cdmx.gob.mx/FGJ/carpetas/carpetasFGJ_acumulado_2025_01.csv>
- Anuales sueltos: `carpetasFGJ_2016.csv` … `carpetasFGJ_2024.csv` en la misma ruta.

**Columnas reales** (leídas del encabezado del acumulado, 2026-09-08):

```
anio_inicio, mes_inicio, fecha_inicio, hora_inicio,
anio_hecho, mes_hecho, fecha_hecho, hora_hecho,
delito, categoria_delito, competencia,
fiscalia, agencia, unidad_investigacion,
colonia_hecho, colonia_catalogo, alcaldia_hecho, alcaldia_catalogo,
municipio_hecho, latitud, longitud
```

**Lo que ya se sabe que hay que manejar:**

- **Dos fechas por registro.** `fecha_inicio` (apertura de la carpeta) y `fecha_hecho`
  (cuándo ocurrió). No son la misma y la diferencia entre ambas *es* un dato: mide la
  demora en denunciar. La primera fila del archivo abre en enero de 2016 un hecho de
  diciembre de 2015. Elegir una de las dos es una decisión con consecuencias y hay que
  declarar por qué.
- **Reclasificación del 29 de julio de 2020.** El propio portal publica una nota
  explicándola y ofrece por separado los datos previos
  (`archivo.datos.cdmx.gob.mx/…/carpetas_ss_junio2020.csv`). Es exactamente el «cambio de
  clasificación entre períodos» que el caso menciona: cualquier serie que cruce julio de
  2020 sin tratarlo tiene un salto que no es del mundo, es del catálogo.
- **El portal dice actualización mensual, pero el último anual publicado es 2024** y el
  acumulado se llama `_2025_01`. Verificar la cobertura real antes de prometer un
  análisis «hasta hoy». *(Comprobado el 2026-09-08 sobre la lista de recursos; falta
  confirmar la última fecha dentro del archivo.)*
- **Columnas duplicadas `_hecho` / `_catalogo`** para colonia y alcaldía: una es el texto
  capturado, otra la normalizada contra catálogo. `municipio_hecho` viene vacío en las
  primeras filas. Hay que medir cuánto difieren antes de escoger.
- **Numerador sin denominador.** Son carpetas, no tasas. Sin población por alcaldía o
  colonia, un mapa de conteos es un mapa de dónde vive la gente.
- **Y el sesgo que define el caso: esto mide denuncias, no delitos.** El subregistro es
  el objeto de estudio, no un defecto que se limpia.

## 2. ENSU — INEGI (percepción)

- <https://www.inegi.org.mx/programas/ensu/>
- Trimestral, representativa a nivel de ciudad. Aquí vive la tensión central del caso:
  la percepción no coincide con la incidencia reportada.
- **Pendiente de verificar:** desagregación geográfica disponible. Si la ENSU no baja de
  «ciudad» o «demarcación», cualquier cruce con carpetas a nivel colonia es una
  imputación, y como tal se declara.
- Complemento a considerar: **ENVIPE** (<https://www.inegi.org.mx/programas/envipe/2025/>),
  que estima la **cifra negra** directamente — el porcentaje de delitos no denunciados.
  Es la pieza que permite hablar de subregistro con un número en vez de con un adjetivo.
  Anual y de menor desagregación geográfica que la ENSU.

## 3. C5

- Lo que el portal publica como abierto son **incidentes viales**:
  <https://datos.cdmx.gob.mx/dataset/incidentes-viales-c5> (2014–2015, 2016–2018,
  2019–2021, 2022–2024, más diccionario de datos en XLSX). Metadatos al 2026-09-01.
- **Ojo — brecha entre el caso y el portal:** el documento habla de «registros del C5 —
  incidentes reportados» en general; lo que hay abierto y a la mano es la serie vial.
  Si se necesitan reportes de emergencia no viales, hay que buscarlos o pedirlos. Esta
  discrepancia se pregunta a los sinodales o se declara como limitación; no se maquilla.

## 4. Sociodemográficos — INEGI

- Censo 2020: <https://www.inegi.org.mx/programas/ccpv/2020/>
- El nivel útil aquí es **AGEB / manzana**, que es lo que permite denominadores y
  estratificación por colonia. El marco geoestadístico (shapefiles de AGEB y colonias
  CDMX) hace falta para cualquier mapa: pendiente de bajar.
- Sirve para las dos cosas que el caso pide: convertir conteos en tasas, y sostener la
  afirmación de que distintos grupos viven la inseguridad distinto.

---

## Preguntas que las fuentes no contestan

1. ¿A qué unidad geográfica se puede llegar de verdad con **todas** las fuentes a la vez?
   Es la restricción que amarra el diseño entero, y hoy no está medida.
2. ¿Qué período común cubren las cuatro? La intersección puede ser más corta que
   cualquiera de ellas por separado.
3. ¿La percepción de la ENSU se puede pegar a la incidencia sin cometer una falacia
   ecológica? Si no, el diseño cambia.

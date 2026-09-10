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
- **La cobertura real, medida el 2026-09-09 dentro de los archivos, no en las etiquetas.**
  Se muestreó cada CSV por rangos de bytes (`curl -r`) en varios puntos; las fechas suben
  de forma monótona, así que los archivos están ordenados y el muestreo es concluyente:

  | Archivo | Lo que dice la etiqueta | Lo que trae de verdad |
  |---|---|---|
  | `carpetasFGJ_acumulado_2025_01.csv` | «acumulado 2016-2024» | **enero 2016 – diciembre 2021** |
  | `carpetasFGJ_2022.csv` | 2022 | 2022 completo |
  | `carpetasFGJ_2023.csv` | 2023 | 2023 completo |
  | `carpetasFGJ_2024.csv` | 2024 | **enero – julio 2024** |

  **El acumulado miente por tres años en su propio nombre y en su propia etiqueta.**
  Quien lo baje creyendo el rótulo y no mire las fechas trabaja con 2016–2021 pensando
  que tiene hasta 2024. Es el modo de falla que no grita: no falla, desaparece.

- **El portal dice «se actualiza mensualmente» y el último dato es de julio de 2024:
  veintiséis meses de atraso** al 2026-09-09. No hay archivos de 2025 ni de 2026, y el
  dataset gemelo de víctimas (`victimasFGJ_*`) se detiene igual, con acumulado
  `victimasFGJ_acumulado_2024_09.csv`. Los metadatos sí se tocaron el 2026-08-31, lo que
  hace la trampa peor: el dataset *parece* vivo. **Cualquier promesa de análisis
  «actual» hay que retirarla, y la fecha de corte hay que declararla en el escrito.**
- **Columnas duplicadas `_hecho` / `_catalogo`** para colonia y alcaldía: una es el texto
  capturado, otra la normalizada contra catálogo. `municipio_hecho` viene vacío en las
  primeras filas. Hay que medir cuánto difieren antes de escoger.
- **Numerador sin denominador.** Son carpetas, no tasas. Sin población por alcaldía o
  colonia, un mapa de conteos es un mapa de dónde vive la gente.
- **Y el sesgo que define el caso: esto mide denuncias, no delitos.** El subregistro es
  el objeto de estudio, no un defecto que se limpia.

## 2. ENSU — INEGI (percepción)

- <https://www.inegi.org.mx/programas/ensu/>
- Trimestral. Aquí vive la tensión central del caso: la percepción no coincide con la
  incidencia reportada.

**Desagregación: cerrado el 2026-09-09 contra la fuente primaria.** La sesión anterior lo
respondió bien pero desde fuentes secundarias, y dejó dicho cómo cerrarlo: abrir el diseño
muestral. Se abrió. Fuente: *ENSU 2024. Diseño muestral. Información complementaria al 4°
trimestre* (<https://www.inegi.org.mx/contenidos/programas/ensu/doc/889463922926.pdf>),
más la presentación ejecutiva de septiembre de 2021.

- **Confirmado: la ENSU llega a alcaldía y ahí se detiene.** Y el documento dice algo más
  fuerte que «publica las 16 por separado»: las demarcaciones **no son un desglose** de
  una muestra diseñada para la ciudad. Cada una es un **«área urbana (ciudad) de interés»**
  por derecho propio, con su propio tamaño de muestra — el anexo lista las dieciséis con
  **300 viviendas cada una, cada trimestre**. Por debajo de alcaldía la encuesta no estima
  nada.
- **Refutado, y era el supuesto que sostenía el diseño del panel:** ~~dieciséis por unos
  cuarenta trimestres es un panel~~. **La serie por alcaldía empieza en 2021-T3, no antes.**
  El mismo documento traza la cobertura: la ENSU nace en 2013 con 32 ciudades; en 2016 se
  reformula a 35 **con la CDMX partida en cuatro regiones**, no en dieciséis; las 16
  demarcaciones entran hasta el tercer trimestre de 2021 —la presentación ejecutiva de
  septiembre de 2021 reporta «75 ciudades (con la Ciudad de México dividida en 16
  demarcaciones territoriales)»—. Antes de esa fecha **el dato por alcaldía no existe**.
- **Precisión: el paso dos, medio cerrado.** El INEGI publica error estándar, CV e
  intervalo por dominio desde 2018-T2, con umbral oficial: precisión **alta** con CV en
  (0, 15 %), **moderada** en [15, 30 %), **baja** de ahí en adelante.
  *Inferencia propia, no leída —los CV por alcaldía viven en los tabulados trimestrales,
  que no se localizaron en el portal—:* con n = 300 y una proporción cerca de 0.6, el
  error estándar bajo muestreo simple es 2.8 pp (CV ≈ 4.7 %); con efecto de diseño 1.5,
  3.5 pp (CV ≈ 5.8 %). **El indicador grueso de percepción aguanta la comparación entre
  alcaldías.** Para un evento de prevalencia 5 % el CV se va a ~25 % simple y ~31 % con
  deff 1.5: **precisión baja**. Desagregar dentro de la alcaldía —por sexo, edad o delito
  específico— rompe la estimación. Leer los CV reales del tabulado sigue pendiente.

**De qué lado de la ecuación va la percepción — agregado el 2026-09-10, y no es cosmético.**
Los dos hechos de arriba se componen: el panel es **corto** (192 observaciones, menos 16
efectos fijos) **y** su variable de percepción viene medida con error de muestreo de unos
3.5 pp. Eso obliga a decidir algo antes de escribir el modelo:

- Si la percepción entra como **variable dependiente** —que es el caso si el objeto es la
  brecha— el error de medición clásico **infla los errores estándar y no sesga los
  coeficientes**. Se pierde potencia, que ya es escasa, pero lo estimado sigue apuntando a
  donde debe.
- Si entrara como **regresor**, el mismo error **atenúa los coeficientes hacia cero**. Con
  192 observaciones eso es la diferencia entre un efecto que se detecta y uno que no
  aparece nunca — y el fracaso se vería como «no hay relación», que es la conclusión
  equivocada por la razón equivocada.

**Conclusión operativa: la brecha va del lado izquierdo, y se dice por qué.** Es un supuesto
explícito, verificable, y de los que la rúbrica premia — no una preferencia de forma.

**Consecuencia sobre el encuadre:**

- **Cruzar ENSU con carpetas a nivel COLONIA queda descartado.** No es que sea difícil: la
  encuesta no estima ahí. Sería falacia ecológica, y del tipo caro — la heterogeneidad
  intraalcaldía en la CDMX es enorme.
- **A nivel ALCALDÍA el cruce es legítimo y la unidad natural es la alcaldía-trimestre**,
  con efectos fijos por alcaldía y estacionalidad. **Pero el panel es corto y hay que
  decir de qué tamaño:** ver la cuenta de doce trimestres en «Preguntas» al final.
  **Y la reclasificación de julio de 2020 deja de ser el quiebre a modelar: cae fuera de
  la ventana**, porque la ventana empieza en 2021-T3.
- **La colonia sigue viva para lo que no necesita ENSU:** las carpetas traen colonia y
  coordenadas, y el censo da denominadores a nivel AGEB. Un encuadre de priorización
  operativa puede vivir a nivel colonia sin tocar la encuesta.
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

~~1. ¿A qué unidad geográfica se puede llegar de verdad con todas las fuentes a la vez?~~
**Contestado el 2026-09-08 y confirmado contra el diseño muestral el 2026-09-09: alcaldía.**

~~2. ¿Qué período común cubren las cuatro?~~ **Contestado el 2026-09-09, y es la
restricción que de verdad aprieta.** La serie por alcaldía de la ENSU empieza en
**2021-T3**; las carpetas de la FGJ terminan en **julio de 2024**. La intersección son
**doce trimestres completos** —2021-T3 y T4, 2022, 2023, 2024-T1 y T2— por 16 alcaldías:
**192 observaciones**, más un julio suelto que no completa trimestre. Es un panel, pero
uno corto: con efectos fijos por alcaldía se van dieciséis grados de libertad antes de
estimar nada.

3. ¿La percepción de la ENSU se puede pegar a la incidencia sin cometer falacia ecológica?
   A nivel alcaldía el cruce es legítimo. **A nivel colonia no**, y eso cierra esa puerta.
4. **Nueva, y es la que hoy no tiene respuesta:** ¿doce trimestres alcanzan para sostener
   una afirmación causal, o solo descriptiva? Con estacionalidad y un post-pandemia de por
   medio son pocos. Conviene decidirlo antes de prometer un modelo, no después.
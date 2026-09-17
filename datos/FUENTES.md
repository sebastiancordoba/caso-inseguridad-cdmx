# Fuentes de datos

*Verificado el 2026-09-08 contra los portales, no citado de memoria. Cada bloque dice
qué se comprobó y qué sigue sin comprobarse.*

**Corregido el 2026-09-13.** Dos datos de la verificación del 9 de septiembre eran falsos:
hasta dónde llegan las carpetas de la FGJ y desde cuándo publica la ENSU por alcaldía. Se
tachan donde estaban y la corrección va al lado, con su fuente. Los dos fallaban en el
mismo sentido —achicaban la ventana común— y entre los dos sostenían la cuenta de 192
observaciones, que en realidad son 336.

**Corregido otra vez el 2026-09-14**, al leer completas las tres notas técnicas de la FGJ:
la «reclasificación del 29 de julio de 2020» no existe; se habían mezclado dos notas
(sección 1). Y dos hallazgos nuevos: `alcaldia_catalogo` está vacía casi siempre (sección
1), y la ENSU sí mide la percepción en las calles por alcaldía (sección 2). Lo que hay que
bajar para el problema acotado (`docs/problema.md`) va al final.

El caso advierte que estas fuentes traen «inconsistencias, cambios de clasificación entre
períodos y brechas» y que **el alumno debe caracterizarlas y manejarlas explícitamente**.
Eso no es una molestia del ejercicio: es la dimensión D2 (10%) y buena parte de los
supuestos explícitos que deciden el 4 en D1–D4. Lo que se encuentre aquí se escribe aquí.

---

## 1. Carpetas de investigación — FGJ CDMX

- Portal: <https://datos.cdmx.gob.mx/dataset/carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico>
- Licencia: CC-BY-4.0. Metadatos modificados el 2026-08-31.
- Acumulado ~~2016–2024~~ **2016 – enero de 2025** (medido, ver abajo): <https://archivo.datos.cdmx.gob.mx/FGJ/carpetas/carpetasFGJ_acumulado_2025_01.csv>
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
- ~~**Reclasificación del 29 de julio de 2020.** El propio portal publica una nota
  explicándola y ofrece por separado los datos previos
  (`archivo.datos.cdmx.gob.mx/…/carpetas_ss_junio2020.csv`). Es exactamente el «cambio de
  clasificación entre períodos» que el caso menciona: cualquier serie que cruce julio de
  2020 sin tratarlo tiene un salto que no es del mundo, es del catálogo.~~
  **Corregido el 2026-09-14, leyendo las tres notas del portal: esa reclasificación no
  existe. Se habían mezclado dos notas distintas.**
  - La [nota de reclasificación](https://datos.cdmx.gob.mx/dataset/250f29c0-31c7-44dc-9d31-f7e6cc78b79e/resource/360e2aa0-77e0-463c-b20d-345ef1c1d95b/download/360e2aa0-77e0-463c-b20d-345ef1c1d95b.pdf)
    es de **febrero de 2020** y da la equivalencia entre el catálogo de delitos de
    2016–2018 y el de **2019 en adelante**. Del robo a transeúnte solo renombra tres
    delitos de taxi («a bordo de taxi» → «a bordo de taxi público y privado»); **el robo a
    transeúnte en vía pública no cambia**. Trae además dos avisos: en 2019 se revisaron
    homicidios dolosos y feminicidios (lesiones que acabaron en muerte, homicidios de
    mujeres reclasificados como feminicidio), y en enero de 2020 se agregaron tipos de
    ofendido (persona moral, estado, sociedad). Todo queda fuera de la ventana del
    problema, que empieza en 2019-T3 con el catálogo nuevo.
  - La [nota del 29 de julio de 2020](https://datos.cdmx.gob.mx/dataset/250f29c0-31c7-44dc-9d31-f7e6cc78b79e/resource/1128fb92-59af-452f-ae38-36b4d835d23e/download/1128fb92-59af-452f-ae38-36b4d835d23e.pdf)
    **no reclasifica**: explica que las carpetas **se corrigen después de publicadas** —el
    delito y el lugar pueden cambiar a diario, cada semana y cada mes— y reporta 86
    carpetas nuevas de enero a marzo de 2020 tras una actualización. Consecuencia: los
    datos del portal no son estáticos, y se trabaja sobre una descarga fija identificada
    por su hash.
  - Una [tercera nota](https://datos.cdmx.gob.mx/dataset/250f29c0-31c7-44dc-9d31-f7e6cc78b79e/resource/bcb29264-91fa-4cc6-8c7e-561d8eb771e9/download/bcb29264-91fa-4cc6-8c7e-561d8eb771e9.pdf),
    de enero de 2020, explica por qué el portal no coincide con el SESNSP: criterios de
    homologación distintos. Para compararlos hay que quedarse con las 16 alcaldías, el
    mismo periodo y la misma categoría, y quitar los hechos no delictivos.
  - El archivo `carpetas_ss_junio2020.csv` que se citaba aquí no se volvió a verificar.
- **La cobertura real.** ~~Medida el 2026-09-09 por rangos de bytes: el acumulado trae
  enero 2016 – diciembre 2021 («miente por tres años») y la serie termina en julio de
  2024.~~ **Falso, corregido el 2026-09-13.** No se sabe qué falló en ese muestreo. La
  cifra de hoy no sale de muestrear: sale de consultar la tabla completa en el API del
  portal (`datastore_search_sql` sobre el recurso `35e87ce4…`, que se carga del mismo CSV),
  y se confirmó leyendo el CSV por rangos de bytes en seis puntos (byte 280 M: octubre de
  2021; 420 M: enero de 2023; 540 M: octubre de 2024).

  | Archivo | Lo que dice la etiqueta | Lo que trae de verdad (`fecha_inicio`) |
  |---|---|---|
  | `carpetasFGJ_acumulado_2025_01.csv` | «acumulado 2016-2024» | **1 ene 2016 – 31 ene 2025**, 2,098,743 registros |
  | `carpetasFGJ_2024.csv` | 2024 | **1 ene – 31 jul 2024**, 138,630 registros |

  Por año de inicio, en el acumulado: 2016 197,914 · 2017 228,323 · 2018 255,350 ·
  2019 250,457 · **2020 204,129** · 2021 230,574 · 2022 239,692 · 2023 242,392 ·
  2024 232,321 · 2025 (solo enero) 17,588 · sin fecha 3. Los doce meses de 2024 están
  completos, entre 17 y 21 mil carpetas cada uno.

  **De dónde salía el «julio de 2024»:** del archivo *anual* de 2024, que sí se corta en
  julio. La serie completa vive en el acumulado, que llega seis meses más lejos. La
  etiqueta del acumulado se queda corta por un mes, no por tres años.

- **Inconsistencia nueva, encontrada en la misma verificación: `fecha_inicio` no tiene un
  solo formato.** En la mayor parte del archivo trae solo la fecha (`2016-01-01`) y la hora
  va aparte; al final trae fecha y hora juntas (`2024-07-26 00:10:00`), y el máximo de la
  tabla es `2025-01-31 23:59:01`. Además, los últimos bytes traen registros de julio y
  agosto de 2024 **después** de los de octubre: el archivo no está ordenado al final. Hay
  que normalizar antes de parsear, y no suponer orden.

- **El portal dice «se actualiza mensualmente» y el último dato es de ~~julio de 2024:
  veintiséis meses~~ enero de 2025: unos veinte meses de atraso** al 2026-09-13. No hay
  archivos anuales de 2025 ni de 2026; el único dato de 2025 es el enero que trae el
  acumulado. El dataset gemelo de víctimas tiene acumulado
  `victimasFGJ_acumulado_2024_09.csv`; su cobertura real no se ha medido, y después de lo
  de arriba no conviene creerle a la etiqueta. Los metadatos sí se tocaron el 2026-08-31,
  lo que hace la trampa peor: el dataset *parece* vivo. **Cualquier promesa de análisis
  «actual» hay que retirarla, y la fecha de corte hay que declararla en el escrito.**
- **Columnas duplicadas `_hecho` / `_catalogo`** para colonia y alcaldía: una es el texto
  capturado, otra la normalizada contra catálogo. `municipio_hecho` viene vacío en las
  primeras filas. Hay que medir cuánto difieren antes de escoger.
  **Medido el 2026-09-14: `alcaldia_catalogo` está vacía en el 97 al 99.9 % de los
  registros de cada año** (2016: 195,610 de 195,651; 2023: 230,296 de 237,440). No sirve;
  se usa `alcaldia_hecho`, que trae dos valores sin alcaldía: «CDMX (indeterminada)» y
  vacío. Entre julio de 2019 y diciembre de 2024 son 32,352 de 1.25 millones de carpetas
  (2.6 %). `colonia_catalogo` no se ha medido.
- **Numerador sin denominador.** Son carpetas, no tasas. Sin población por alcaldía o
  colonia, un mapa de conteos es un mapa de dónde vive la gente.
- **Y el sesgo que define el caso: esto mide denuncias, no delitos.** El subregistro es
  el objeto de estudio, no un defecto que se limpia.
- **Robo a transeúnte en vía pública, medido el 2026-09-14** para el problema acotado, por
  fecha del hecho entre julio de 2019 y diciembre de 2024: **44,958 carpetas con violencia
  y 10,458 sin violencia**. Por alcaldía y trimestre, de unas 13 en Milpa Alta a unas 435
  en Iztapalapa; solo el 1.3 % sin alcaldía (201 «indeterminada» y 532 vacías). Para
  comparar, el robo en transporte público suma 25,328, con menos de 12 por trimestre en
  Milpa Alta, Cuajimalpa y Magdalena Contreras y el 7 % sin alcaldía.
  **Recontado el 2026-09-17 sobre el CSV descargado** (2,098,743 registros): mismas cifras.
  Aparecen además 13 carpetas de «ROBO A TRANSEUNTE EN VIA PUBLICA (NOMINA)» (11 con
  violencia, 2 sin); falta decidir si se suman y declararlo como supuesto.

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
  cuarenta trimestres es un panel~~. ~~**La serie por alcaldía empieza en 2021-T3, no
  antes.**~~ **Corregido el 2026-09-13: empieza en 2019-T3**, dos años antes. La historia
  de cobertura que traza el diseño muestral sigue en pie —la ENSU nace en 2013 con 32
  ciudades; en 2016 se reformula a 35 **con la CDMX partida en cuatro regiones**—; lo que
  estaba mal es cuándo entran las dieciséis. Los boletines trimestrales del INEGI lo fijan
  sin ambigüedad:
  - **2019-T2** ([boletín de julio de 2019](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2019/ensu/ensu2019_07.pdf)):
    la CDMX todavía sale en cuatro regiones —Norte, Sur, Oriente, Poniente—, con notas
    que dicen qué alcaldías incluye cada una.
  - **2019-T3** ([boletín de octubre de 2019](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2019/ensu/ensu2019_10.pdf)):
    ya salen las alcaldías, con el trimestre anterior marcado como no disponible
    (Iztapalapa ND → 85.8 %; Benito Juárez ND → 53.7 %). La nota metodológica dice que
    desde el tercer levantamiento de 2019 la CDMX va dividida en 16 demarcaciones, y el
    boletín de abril de 2021 precisa que son 300 viviendas por demarcación desde
    septiembre de 2019.
  - **2020-T2 no existe:** la contingencia sanitaria impidió ese levantamiento. En 2020
    solo hubo marzo, septiembre y diciembre ([boletín de enero de 2021](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2021/ensu/ensu2021_01.pdf)).
  - Las cuatro regiones se siguen publicando junto a las alcaldías después de 2019-T3.

  La presentación ejecutiva de septiembre de 2021 («75 ciudades, con la CDMX en 16
  demarcaciones territoriales») probablemente es de donde salió el error: marcaba cuántas
  ciudades había ese trimestre, no cuándo entraron las alcaldías.
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
- **Percepción por lugar: verificado el 2026-09-14 en el diccionario de microdatos**
  ([2021-T1](https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu_fd_2021_marzo.pdf)).
  La pregunta 1.2 —*«En términos de delincuencia, dígame si en (LUGAR) se siente seguro(a)
  o inseguro(a)»*— se hace para doce lugares, `BP1_2_01` a `BP1_2_12`. Los que importan
  aquí: `BP1_2_03` = «las calles que habitualmente usa» y `BP1_2_09` = «el transporte
  público». Respuestas: 1 Seguro(a), 2 Inseguro(a), 3 No aplica, 9 No sabe / no responde.
  La base trae `CD` y `NOM_CD` (cada alcaldía es una ciudad de interés: 76 Iztapalapa, 78
  Milpa Alta, 81 Tlalpan, 83 Benito Juárez, 84 Cuauhtémoc…), `CVE_MUN`, los factores
  `FAC_VIV` y `FAC_SEL`, y las variables de diseño `UPM_DIS` y `EST_DIS`, con las que se
  calcula el error estándar. Las mismas columnas aparecen en diciembre de 2024, según el
  encabezado de una copia pública de los microdatos (ver «Qué hay que bajar»).
  **La percepción en las calles por alcaldía no está en los boletines: se calcula de los
  microdatos.** Con eso, los CV dejan de buscarse en tabulados: se calculan.

**Consecuencia sobre el encuadre:**

- **Cruzar ENSU con carpetas a nivel COLONIA queda descartado.** No es que sea difícil: la
  encuesta no estima ahí. Sería falacia ecológica, y del tipo caro — la heterogeneidad
  intraalcaldía en la CDMX es enorme.
- **A nivel ALCALDÍA el cruce es legítimo y la unidad natural es la alcaldía-trimestre**,
  con efectos fijos por alcaldía y por trimestre. ~~Pero el panel es corto: doce
  trimestres.~~ **Corregido el 2026-09-13: son 21 trimestres**, ver «Preguntas» al final.
  ~~Y la reclasificación de julio de 2020 deja de ser el quiebre a modelar: cae fuera de
  la ventana.~~ ~~**La reclasificación de julio de 2020 vuelve a caer dentro de la
  ventana**, en 2020-T3, con tres trimestres de la ENSU antes de ella (2019-T3, 2019-T4 y
  2020-T1). Los efectos fijos de trimestre absorben el salto si el catálogo cambió parejo
  en todas las alcaldías; si no, hay que tratarlo aparte. Es trabajo de D2, no un
  estorbo.~~ **Corregido el 2026-09-14: no hay reclasificación en julio de 2020** (ver la
  sección 1). El cambio de catálogo es de 2019 y queda fuera de la ventana. Lo que sí queda
  dentro es la pandemia.
- **La colonia sigue viva para lo que no necesita ENSU:** las carpetas traen colonia y
  coordenadas, y el censo da denominadores a nivel AGEB. Un encuadre de priorización
  operativa puede vivir a nivel colonia sin tocar la encuesta.
- Complemento a considerar: **ENVIPE** (<https://www.inegi.org.mx/programas/envipe/2025/>),
  que estima la **cifra negra** directamente — el porcentaje de delitos no denunciados.
  Es la pieza que permite hablar de subregistro con un número en vez de con un adjetivo.
  Anual y de menor desagregación geográfica que la ENSU. *(El encabezado de este punto se
  perdió en el commit `7b57566` y quedaron sueltas las líneas de abajo; restituido el
  2026-09-13.)*
  **Leído en la fuente primaria el 2026-09-13**, en el [descriptor de microdatos 2025](https://www.inegi.org.mx/contenidos/programas/envipe/2025/doc/fd_envipe2025.pdf)
  y el [diseño muestral 2025](https://www.inegi.org.mx/contenidos/programas/envipe/2025/doc/889463926689.pdf):
  - **Los microdatos sí traen la alcaldía donde ocurrió cada delito** (`BP1_3C`, en la
    tabla de delitos `TMod_Vic`), y si se denunció y si se abrió carpeta. Las demás
    tablas traen la alcaldía de residencia (`CVE_MUN`).
  - **Pero la encuesta no es representativa por alcaldía:** solo nacional, por entidad y
    por 34 áreas urbanas, con la CDMX en las mismas cuatro regiones. Muestra de la CDMX:
    6,400 viviendas. No hay producto oficial con cifra negra por alcaldía; la de la CDMX
    completa es de 93 % en la ENVIPE 2024.
  - Para el encuadre elegido (A, ver `docs/entrega-2026-09-14.md`) la ENVIPE no entra al
    panel —es anual y no llega a alcaldía—: da el contexto del subregistro, no una variable.

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
  **Para el problema acotado basta con menos** (2026-09-14): la población por alcaldía del
  ITER de la CDMX y los límites de las alcaldías del portal de la Ciudad. Ver «Qué hay que
  bajar», al final. AGEB y colonias quedan para trabajo futuro.
- Sirve para las dos cosas que el caso pide: convertir conteos en tasas, y sostener la
  afirmación de que distintos grupos viven la inseguridad distinto.

---

## Preguntas que las fuentes no contestan

~~1. ¿A qué unidad geográfica se puede llegar de verdad con todas las fuentes a la vez?~~
**Contestado el 2026-09-08 y confirmado contra el diseño muestral el 2026-09-09: alcaldía.**

~~2. ¿Qué período común cubren las cuatro?~~ ~~Contestado el 2026-09-09: doce
trimestres, de 2021-T3 a 2024-T2, 192 observaciones.~~ **Corregido el 2026-09-13.** La
ENSU por alcaldía empieza en **2019-T3** y le falta **2020-T2**; las carpetas llegan a
**enero de 2025**. La intersección son **21 trimestres completos** —2019-T3 y T4; 2020-T1,
T3 y T4; 2021 a 2024 completos— por 16 alcaldías: **336 observaciones**, más un enero de
2025 suelto que no completa trimestre. Con efectos fijos de alcaldía y de trimestre se van
36 parámetros y quedan unos 300 grados de libertad. Sigue siendo un panel chico, pero ya no
uno en que los efectos fijos se coman la muestra.

3. ¿La percepción de la ENSU se puede pegar a la incidencia sin cometer falacia ecológica?
   A nivel alcaldía el cruce es legítimo. **A nivel colonia no**, y eso cierra esa puerta.
4. **La que sigue sin respuesta:** ¿~~doce~~ veintiún trimestres alcanzan para sostener
   una afirmación causal, o solo descriptiva? Ahora la pandemia queda *dentro* de la
   ventana —con un trimestre faltante y una caída de 18 % en las carpetas de 2020— en vez
   de detrás. El encuadre elegido promete asociación dentro de cada alcaldía, no
   causalidad, y se pregunta a los sinodales si eso basta para D4. **Contestada el
   2026-09-14: los sinodales no esperan causalidad.**

---

## Qué hay que bajar para el problema acotado

*Para `docs/problema.md`: percepción en las calles contra robo a transeúnte. Verificado el
2026-09-14: cada liga se probó leyendo sus primeros bytes, y entrega el archivo, no una
página de «no encontrado». Las ligas de la ENSU salen de la pestaña «Microdatos» del
programa, que se arma con JavaScript; por eso no aparecían al pedir la página con curl.*

| # | Qué | Para qué | Liga | Formato |
|---|---|---|---|---|
| 1 | Carpetas de la FGJ, acumulado | Robo a transeúnte en vía pública, por fecha del hecho y `alcaldia_hecho`, con coordenadas | <https://archivo.datos.cdmx.gob.mx/FGJ/carpetas/carpetasFGJ_acumulado_2025_01.csv> | CSV, 560 MB. Ya lo baja `src/descarga.py --fuente fgj` |
| 2 | ENSU, microdatos 2019 | 2019-T3 y 2019-T4 (el zip trae el año completo) | <https://www.inegi.org.mx/contenidos/programas/ensu/microdatos/ensu_bd_2019_dbf.zip> | **Solo DBF**, 10.5 MB |
| 3 | ENSU, microdatos 2020 | 2020-T1, T3 y T4; junio no existe | <https://www.inegi.org.mx/contenidos/programas/ensu/microdatos/ensu_bd_2020_dbf.zip> | **Solo DBF**, 9.5 MB |
| 4 | ENSU, microdatos 2021 a 2024 | Los dieciséis trimestres restantes | `https://www.inegi.org.mx/contenidos/programas/ensu/microdatos/ensu_bd_{2021,2022,2023,2024}_csv.zip` | CSV, de 10 a 15 MB por año |
| 5 | ENSU, descripción de archivos (FD) | Confirmar que `BP1_2_03`, `CD`, `FAC_SEL`, `UPM_DIS` y `EST_DIS` no cambian de nombre ni de códigos entre años | `https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu_fd_{2019,…,2024}_pdf.zip` | PDF en zip, de 5 a 11 MB por año |
| 6 | ENSU, catálogo de ciudades de interés | Las claves `CD` de las dieciséis alcaldías | <https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu2024_catalogo_ciudades_interes.pdf> | PDF |
| 7 | Censo 2020, ITER de la CDMX | Población por alcaldía, para la tasa por 100 mil | <https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_09_cpv2020_csv.zip> | CSV en zip, 175 KB |
| 8 | Límite de alcaldías | Los polígonos del mapa del dashboard | <https://datos.cdmx.gob.mx/dataset/bae265a8-d1f6-4614-b399-4184bc93e027/resource/deb5c583-84e2-4e07-a706-1b3a0dbc99b0/download/deb5c583-84e2-4e07-a706-1b3a0dbc99b0.json> | GeoJSON; metadatos al 2026-09-01. También en SHP en el mismo dataset |
| 9 | Las tres notas técnicas de la FGJ | Documentar los datos (D2): catálogo, correcciones retroactivas, diferencia con el SESNSP | Ligas en la sección 1 | PDF |

**Detalles que hay que manejar al bajarlos:**
- **2019 y 2020 solo vienen en DBF.** Hace falta un lector de DBF (por ejemplo, `dbfread`)
  además de pandas.
- Cada zip de la ENSU trae los trimestres del año en tablas separadas; la que importa es la
  del cuestionario básico (`CB`). En una copia pública de los microdatos
  (<https://github.com/cartodev09014/ENSU_datos>, no oficial) septiembre de 2020 viene
  partido en dos tablas; hay que ver por qué en el zip oficial antes de juntarlas.
- El INEGI avisa en la misma pestaña dos cambios de nombres de campos: `ENT` y `MUN` pasaron
  a `CVE_ENT` y `CVE_MUN` en diciembre de 2016, y `LOC` pasó a `CVE_LOC` en el tercer
  trimestre de 2025. Los dos quedan fuera de la ventana.
- **Para validar el cálculo**: la percepción general por alcaldía que salga de los
  microdatos (`BP1_1`) tiene que coincidir con la que publican los boletines trimestrales
  (Iztapalapa: 85.8 % en septiembre de 2019).

**Lo que ya no hace falta bajar:** los anuales de la FGJ (el acumulado los contiene), el C5,
la ENVIPE (basta con citar su 93 % de cifra negra), AGEB, colonias y proyecciones de
población (con efectos fijos de alcaldía, el cambio de población en cinco años pesa poco).
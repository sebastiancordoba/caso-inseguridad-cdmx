# Fase 1 — Cinco encuadres candidatos, con factibilidad verificada

*Hecho el 2026-09-20. Solo factibilidad: nada de esto es análisis ni resultado. Toda cifra
de abajo salió hoy de un archivo descargado hoy (o del CSV de la FGJ ya bajado el 17 de
septiembre, hash en `datos/crudos/MANIFIESTO.md`); donde algo no se pudo verificar, se dice.
Restricciones con las que se evaluó: terminado y demostrable el 15 de octubre de 2026, una
sola persona, datos públicos descargables hoy, app estática en GitHub Pages con datos
precomputados, ámbito CDMX y por debajo de alcaldía cuando se pueda.*

*Relación con lo ya decidido: el encuadre vigente (`problema.md`, percepción en la calle
contra robo a transeúnte) entra aquí como el candidato 3 y compite con los demás bajo los
criterios nuevos. Dos cosas de `problema.md` chocan con las restricciones de esta fase y
habría que actualizarlas si se mantiene: el dashboard está pensado en Streamlit, y la
unidad es la alcaldía.*

## Qué se verificó hoy

| Fuente | URL | Formato y tamaño | Granularidad | Cobertura real | Estado |
|---|---|---|---|---|---|
| Carpetas FGJ, acumulado | <https://archivo.datos.cdmx.gob.mx/FGJ/carpetas/carpetasFGJ_acumulado_2025_01.csv> | CSV, 560 MB | Punto (lat/lon), colonia, alcaldía; fecha y hora del hecho | 2016 – 31 ene 2025 | Responde hoy (206); archivo completo ya en disco |
| Víctimas FGJ, acumulado | <https://archivo.datos.cdmx.gob.mx/FGJ/victimas/victimasFGJ_acumulado_2024_09.csv> | CSV, 373 MB | Igual, más `sexo` y `edad` | 2019 – sep 2024 (etiqueta; no medida) | Responde hoy; en disco |
| Llamadas al 911 (C5) | `https://archivo.datos.cdmx.gob.mx/911/llamadas_911_{2019_s1 … 2022_s1}.csv` | 7 CSV, de 32 a 124 MB | Centroide de manzana, colonia, alcaldía; fecha y hora | ago 2019 – jun 2022, con huecos (ver encuadre 4) | Los siete responden; bajados completos 2019-S2 y 2021-S2 |
| Cuadrantes SSC | <https://datos.cdmx.gob.mx/dataset/cuadrantes> | SHP 450 KB, CSV 1.4 MB | 847 polígonos con sector, zona y alcaldía | Shapefile de mayo de 2021 | Bajado y leído |
| Estado de fuerza por cuadrantes | <https://datos.cdmx.gob.mx/dataset/programa-de-cuadrantes-estructura-y-estado-de-fuerza-inicial> | CSV, 1.3 KB | **Solo cinco zonas × tres turnos**, no por cuadrante | «Inicial», sin fecha | Bajado; no sirve por debajo de zona |
| Afluencia diaria del Metro | <https://datos.cdmx.gob.mx/dataset/afluencia-diaria-del-metro-cdmx> | CSV, 60 MB, 1.18 M filas | Estación × línea × día | 1 ene 2010 – 31 jul 2026 | Bajado completo |
| Estaciones del Metro | <https://datos.cdmx.gob.mx/dataset/lineas-y-estaciones-del-metro> | SHP, 42 KB | 195 puntos estación-línea (163 nombres) | — | Bajado y usado |
| Catálogo de colonias | <https://datos.cdmx.gob.mx/dataset/catalogo-de-colonias-datos-abiertos> | GeoJSON, 10 MB | 1,543 polígonos | — | Bajado y leído |
| «Postes del C5» | <https://datos.cdmx.gob.mx/dataset/wifi-gratuito-en-postes-del-c5> | XLSX, 0.5 MB | 13,714 puntos | Corte de julio de 2025 | En disco. **No es un inventario de cámaras** (ver encuadre 5) |
| ENSU, microdatos | `https://www.inegi.org.mx/contenidos/programas/ensu/microdatos/ensu_bd_{año}_{csv,dbf}.zip` | ZIP, 10 a 15 MB por año | Alcaldía × trimestre | 2019-T3 – 2024-T4 sin 2020-T2 | Responden hoy; ya procesados en `panel.csv` |
| Censo 2020, ITER CDMX | <https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_09_cpv2020_csv.zip> | ZIP, 175 KB | Alcaldía | 2020 | Responde hoy; en disco |

**Límite que cruza a todos:** las carpetas de la FGJ terminan el 31 de enero de 2025. Ningún
encuadre que las use puede prometer un diagnóstico «actual»; la prensa de este mes reporta
cambios fuertes en 2025–2026 (por ejemplo, el robo con violencia en el Metro) que los datos
abiertos no permiten ver. La fecha de corte se declara en la app.

---

## 1. Robo en el Metro: ¿qué estaciones son peligrosas por pasajero y no por volumen?

**Pregunta.** Entre 2019 y 2024, ¿cuántos robos a pasajero se denuncian por cada millón de
entradas en cada estación del Metro, y qué estaciones cambian de lugar cuando se ordena por
esa tasa en vez de por conteo?

**Quién decide qué.** La SSC (Policía Bancaria e Industrial y Auxiliar, que custodian el
Metro) y la gerencia de seguridad del STC deciden en qué estaciones y en qué franja horaria
poner elementos. Hoy la lista pública —la de la FGJ que reproduce la prensa:
~~Pantitlán, Hidalgo, Pino Suárez, Tacubaya~~ **Pantitlán, Hidalgo, Tacuba, Guerrero, Pino
Suárez, Tacubaya, Balderas, Universidad, Indios Verdes, Cuatro Caminos y Constitución de
1917**— es un ordenamiento por conteo, que en buena parte es un ordenamiento por afluencia.

> **Corregido el 2026-10-13.** Los cuatro nombres tachados no son los de ninguna nota: son
> las cuatro primeras por conteo de este repo. La lista de Infobae del 11 de enero de 2024,
> abierta y capturada ese día, trae once estaciones y en otro orden. La captura y lo que
> dice, literal, se capturaron como registro (capturas no publicadas); el error y su corrección, en la
> decisión 55. Si la tasa señala estaciones medianas que el conteo esconde, el
despliegue por conteo está sobreatendiendo las terminales y dejando sin cubrir estaciones
donde el riesgo por usuario es mayor.

**Hipótesis.** El orden por tasa difiere materialmente del orden por conteo: correlación de
rangos de Spearman menor a 0.8 y al menos tres de las diez primeras por tasa fuera de las
diez primeras por conteo. *Se rechaza si* ρ ≥ 0.9 y los dos top-10 coinciden en nueve o
más: entonces el conteo basta y la app no aporta decisión.

**Datos, medidos hoy.** «ROBO A PASAJERO A BORDO DE METRO» con y sin violencia: 8,366
carpetas por fecha del hecho en 2019–2024 (7,704 sin violencia y 662 con violencia; 2019
es el año más alto y 2020 cae por la pandemia). Traen coordenadas 7,325 (88 %); de esas,
**el 92.4 % cae a 150 m o menos de una estación** (mediana 31 m), así que la asignación a
estación es factible por distancia. Cincuenta y cuatro estaciones tienen 30 robos o más en el periodo; Pantitlán 491,
Hidalgo 483, Pino Suárez 288. Trae hora del hecho. La afluencia cubre todo el periodo por
estación y línea, a diario.

**Método y por qué aquí.** Tasa por millón de entradas con suavizado bayesiano empírico
(Poisson-gamma), porque en las estaciones chicas cinco robos sobre poca afluencia dan tasas
extremas que son ruido: el suavizado encoge cada estación hacia la media de su línea en
proporción a lo poco que se sabe de ella, y el intervalo de credibilidad se enseña. Sobre
eso, un perfil hora × día de la semana por estación. No hace falta más modelo: la decisión
es un ordenamiento con su incertidumbre, y un modelo más rico no la cambiaría.

**Dashboard.** Mapa esquemático de la red con cada estación coloreada por tasa suavizada y
dimensionada por conteo —las dos lecturas a la vez, que es justo la tensión—; un control
conteo/tasa que reordena una lista lateral y marca las estaciones que suben o bajan más de
diez lugares; al elegir una estación, su serie anual con intervalo y su mapa de calor hora ×
día. Quien despliega policías ve dónde y a qué hora. Todo son JSON de pocos cientos de KB.

**Riesgo principal.** Dos sesgos de medición del mismo lado. (i) La afluencia cuenta
entradas por torniquete: los transbordos no se ven, así que en Hidalgo o Pantitlán el
denominador subestima a quien pasa por ahí y la tasa sale inflada. (ii) «A bordo» no dice
dónde ocurrió el robo sino dónde se ubicó la carpeta —probablemente donde el pasajero se
bajó o donde está la agencia—. *Detección temprana, en el primer día:* comparar la tasa de
estaciones de transbordo contra las de paso de la misma línea; si todas las de transbordo
encabezan la lista por tasa, el denominador no sirve tal cual y hay que ponderar con la
matriz de transbordos de la EOD 2017 (el shapefile trae `CVE_EOD17`) o restringir el
ordenamiento a estaciones sin transbordo. Un tercer detalle, ya visto: los nombres de
estación en el CSV de afluencia vienen con la codificación rota («Isabel la CatÃ³lica») y
son 168 contra 163 en el shapefile; el cruce pide una tabla de equivalencias a mano.

**Antecedentes.** García-Tejeda (2023), «A veces lo que brilla es oro: delitos racionales
alrededor del Metro de la CDMX», *Nexos*
(<https://seguridad.nexos.com.mx/a-veces-lo-que-brilla-es-oro-delitos-racionales-alrededor-del-metro-de-la-cdmx/>):
usa el cierre de la Línea 12 y zonas de 250 y 500 m alrededor de estaciones, con conteos,
sin tasa por pasajero — leído en resumen por herramienta. La serie «Radiografía del robo
violento en el transporte público», también en *Nexos*
(<https://seguridad.nexos.com.mx/radiografia-del-robo-violento-en-el-transporte-publico-parte-i/>),
no se abrió. Las listas de «estaciones más peligrosas según la Fiscalía» que publica la
prensa (por ejemplo Infobae, 12 de enero de 2024) son conteos. El problema del denominador
en el delito en transporte está en la literatura de criminología ambiental (población
ambiente; Andresen) pero **no se abrió ninguna obra hoy**: citar solo después de leer. No
se encontró una tasa por afluencia y estación para el Metro de la CDMX; «no se encontró» no
es «no existe».

---

## 2. Puntos calientes de robo a transeúnte: ¿cuánto del próximo trimestre se puede anticipar?

**Pregunta.** ¿Qué porcentaje de los robos a transeúnte de un trimestre cae en el 5 % de
celdas de 250 m que se habría elegido con los datos hasta el trimestre anterior, y cuánto
mejora eso frente a repartir la vigilancia por conteo de cuadrante?

**Quién decide qué.** El jefe de sector de la SSC reparte patrullaje a pie entre sus
cuadrantes (847 en la ciudad). El cuadrante es grande —unas decenas de manzanas— y la regla
de reparto no es pública; las «160 zonas prioritarias» de la SSC tampoco publican método. La
decisión que cambia: qué tramos dentro de cada sector reciben presencia fija el trimestre
siguiente, y con qué regla simple y auditable se eligen.

**Hipótesis.** Una regla que solo usa la historia de la celda (conteo con decaimiento
exponencial) captura al menos 3.5 veces más robos por área que el azar (PAI ≥ 3.5) de forma
estable en los ocho trimestres de prueba, y una regla más elaborada (densidad por kernel,
estacionalidad) no la mejora en más de dos puntos porcentuales. *Se rechaza si* la captura
cae por debajo del 12 % en algún trimestre de prueba o varía más de dos veces entre
trimestres: entonces la persistencia no alcanza para planear a un trimestre.

**Datos, medidos hoy.** 63,938 robos a transeúnte en vía pública con fecha del hecho en
2019–2024; **98.2 % con coordenadas** y 100 % con hora; 61,753 coordenadas distintas, así que
no están geocodificados a un centroide. En celdas de unos 250 m: la mitad de los robos
cae en el 16.6 % de las celdas que tuvieron alguno. Persistencia, prueba rápida: el 5 % de
celdas con más robos en 2023 (497 de 9,949) concentró el **21.3 % de los robos de 2024**
(23.2 % de 2022 a 2023); de trimestre a trimestre, entre 14.2 y 19.3 % con unos 2,000 robos
por trimestre. Hay señal, y es modesta.

**Método y por qué aquí.** Evaluación hacia adelante (se elige con datos hasta *t*, se mide
en *t*+1) de tres o cuatro reglas transparentes, con PAI y porcentaje capturado como
métrica. Es apropiado aquí porque la decisión es operativa y trimestral, porque con 2,000
eventos por trimestre en 10,000 celdas un modelo complejo sobreajusta, y porque la
evaluación fuera de muestra es exactamente la «verificación de supuestos» que pide D4. Todo
se precomputa: la app solo enseña las celdas elegidas y lo que habrían capturado.

**Dashboard.** Mapa de hexágonos con las celdas que la regla elige para el trimestre
seleccionado, y encima los robos que sí ocurrieron el trimestre siguiente (aciertos y
fallos a la vista); selector de sector SSC que recorta el mapa y da la lista de sus celdas;
un indicador de captura por trimestre y por regla. El usuario ve dónde patrullar y qué tan
en serio tomarse la recomendación.

**Riesgo principal.** Que mida dónde se denuncia y dónde patrulla ya la policía, no dónde
se roba: con 93 % de cifra negra, una celda con muchas carpetas puede ser una celda cerca de
una agencia o con más presencia policial. No se puede corregir con estos datos; se declara
y se comprueba una parte: si la captura se sostiene igual en robo con violencia (que se
denuncia más) que en robo sin violencia. Segundo riesgo, de calendario y de defensa: **es el
terreno más transitado** (ver abajo); un sinodal que conozca el trabajo de CentroGeo
preguntará qué hay de nuevo, y la respuesta honesta es «la evaluación fuera de muestra y la
app», no el mapa.

**Antecedentes.** Ya revisados en `revision-literatura.md`, encuadre C: Vilalta (2026),
«Focalización territorial del delito y gestión policial en la Ciudad de México», CrimRxiv
(resumen); Vilalta et al. (2026), *Area Development and Policy* (resumen); Flores-Gutiérrez
(2021), *Quivera* (completo): quince colonias concentran el 19 % del delito callejero de
2018; Prieto-Curiel (2021), concentración semanal de robos en la CDMX (completo); Weisburd
(2015), ley de concentración (resumen). Encontrados hoy y **no abiertos**: Jaitman y
Ajzenman, «Crime Concentration and Hot Spot Dynamics in Latin America», BID (el PDF devolvió
403; el buscador resume que el 50 % del delito cae en 3 a 7.5 % de los segmentos de calle);
Piña-García y Ramírez-Ramírez (2019), «Exploring crime patterns in Mexico City», *Journal of
Big Data*, que pronostica el total semanal con las carpetas y Twitter, no por lugar.

---

## 3. Percepción en la calle contra robo a transeúnte (el encuadre vigente)

**Pregunta.** ¿El porcentaje que se siente inseguro en las calles de cada alcaldía sigue a
la tasa de robo a transeúnte que ahí se denuncia, trimestre a trimestre, de 2019-T3 a
2024-T4?

**Quién decide qué.** La SSC y las alcaldías, que reportan desempeño con las dos cifras, y
quien lee esos reportes. La decisión es más blanda que en los encuadres 1 y 2: qué
indicador poner junto a la ENSU y si bajar el robo en la calle es una palanca sobre el
miedo. Es una decisión de medición y de comunicación, no de despliegue.

**Hipótesis.** H1 y H2 de `problema.md`: asociación positiva dentro de alcaldía, mayor para
el robo con violencia. Se rechaza H1 si la asociación es nula o negativa.

**Datos.** Los más verificados del repo: `datos/procesados/panel.csv`, 336 filas, con error
estándar de diseño, validado contra los boletines del INEGI (Iztapalapa 2019-T3 = 85.8 %).

**Método.** Panel con efectos fijos de alcaldía y de trimestre; robustez con rezago, sin
2020, dejando una alcaldía fuera y con el error muestral.

**Dashboard.** El de `problema.md`, que se puede hacer estático sin pérdida: 336 filas y un
GeoJSON de 0.7 MB.

**Riesgo principal.** Un resultado nulo con 336 observaciones y errores estándar de 2.4 a
5.3 puntos en la percepción: no se distinguiría «no hay relación» de «no hay potencia». Se
detecta en una tarde corriendo el modelo base; el panel ya existe.

**Antecedentes.** Prieto Curiel y Bishop (2016); Bastién Olvera y Grabinsky (2023); Innes
(2004). Detalle en `revision-literatura.md`.

**Contra las restricciones de esta fase:** no baja de alcaldía, y no puede: la ENSU no
estima por debajo. Es el único que toca la tensión percepción–incidencia que el caso nombra.

---

## 4. Disparos que se reportan al 911 y no llegan a la Fiscalía

**Pregunta.** Por colonia, ¿cuántas llamadas al 911 por disparos hay por cada carpeta de
investigación por arma de fuego, y en qué colonias esa razón es anómalamente alta?

**Quién decide qué.** La SSC y la FGJ focalizan la violencia armada con carpetas (homicidio
y lesiones por arma de fuego). Si hay colonias donde se oyen disparos de forma sostenida y
casi nada llega a carpeta, la focalización por carpetas no las ve. La decisión que cambia:
qué colonias entran a la lista de atención por violencia armada. Es el único candidato que
ataca el subregistro —la primera tensión del caso— con una fuente que no pasa por la
denuncia.

**Hipótesis.** La razón llamadas/carpetas no es pareja: varía más de tres veces entre el
cuartil alto y el bajo de colonias con volumen suficiente, y el orden de colonias por
llamadas difiere del orden por carpetas (Spearman < 0.6). *Se rechaza si* las llamadas son
proporcionales a las carpetas (ρ ≥ 0.8): entonces el 911 no añade información y las
carpetas ordenan bien el territorio, que es lo que Brunton-Smith et al. (2024) esperarían.

**Datos, medidos hoy.** Las llamadas abiertas **no traen robo a transeúnte** —la categoría
«Robo» solo tiene automovilista, cable, escuela y «otros», 4,401 folios en un semestre—, así
que el cruce 911–carpetas para robo callejero es imposible. Sí traen «Disturbio / Disparos»:
13,989 llamadas en julio–diciembre de 2021, con coordenadas al 100 % (centroide de manzana),
en 1,369 colonias, 478 de ellas con diez o más. En el mismo semestre la FGJ abrió 440
carpetas por lesiones y 312 por homicidio con arma de fuego, más 48 por disparos. Por
alcaldía la razón va de 7.6 (Cuauhtémoc) a 25.8 (Álvaro Obregón): hay variación.
Inconsistencias ya vistas, todas de D2: el archivo «2021-S2» trae folios desde marzo de
2020; el de «2019-S2» empieza en agosto y trae noviembre a la mitad; `codigo_cierre` cambia
de codificación entre años (Afirmativo/Negativo/Duplicado/Informativo en 2019; «A»/«Otros»
en 2021); en 2021-S2 solo el 10 % de las llamadas por disparos tiene cierre afirmativo; y la
serie termina en junio de 2022, sin actualización desde noviembre de 2022.

**Método y por qué aquí.** Razón por colonia con suavizado bayesiano empírico —muchas
colonias tienen cero o una carpeta y la razón cruda explota— y un modelo de conteos
(binomial negativa de carpetas sobre llamadas, con población o viviendas de exposición) cuyo
residuo marca las colonias con menos carpetas de las esperadas. Se excluyen las semanas de
pirotecnia (15 de septiembre, 12 y 24–31 de diciembre), como hacen Carr y Doleac con el 4 de
julio. Se corre dos veces: con todas las llamadas y solo con las de cierre afirmativo.

**Dashboard.** Mapa de colonias en dos colores —más disparos reportados de los que explican
las carpetas, y menos—, con filtro de cierre afirmativo y ficha por colonia con las dos
series. Sirve a la decisión porque entrega una lista corta de colonias que hoy no aparecen.

**Riesgo principal.** Que la llamada mida otra cosa: pirotecnia, llamadas múltiples por un
mismo hecho (hay folios «Duplicado» en 2019, pero no en 2021), propensión a llamar distinta
por colonia. *Detección temprana:* si el resultado con cierre afirmativo (1,420 llamadas en
el semestre) contradice al de todas las llamadas, no hay hallazgo defendible; con 1,420
eventos en 1,500 colonias, además, el análisis por colonia se queda sin potencia y hay que
subir a cuadrante o sector. Y los datos son viejos: tres años, de 2019 a 2022.

**Antecedentes.** Carr y Doleac (2016), «The Geography, Incidence, and Underreporting of Gun
Violence: New Evidence Using ShotSpotter Data», Brookings
(<https://www.brookings.edu/wp-content/uploads/2016/07/Carr_Doleac_gunfire_underreporting.pdf>):
en Washington y Oakland solo el 12 % de los disparos detectados por sensores genera una
llamada al 911 y del 2 al 7 % un delito registrado — resumen del buscador, PDF no abierto.
México Evalúa propone usar el 911 y los reportes policiales como estadística criminal
(<https://mexicoevalua.org/mexico-evalua-propone-que-los-reportes-policiales-y-el-911-se-conviertan-en-fuentes-de-estadistica-criminal/>,
no abierto). Riascos Villegas et al. (2023) modelan subregistro espacial en Bogotá y
Brunton-Smith et al. (2024) dan el contraargumento; ambos ya están en
`revision-literatura.md`. No se encontró un cruce de llamadas por disparos con carpetas para
la CDMX.

---

## 5. Cobertura de videovigilancia: ¿dónde pondría los próximos postes?

**Pregunta.** ¿Qué porcentaje de los robos a transeúnte ocurre a menos de 100 m de un poste
del C5, y en qué 500 ubicaciones nuevas se cubriría el mayor número de robos hoy sin
cobertura?

**Quién decide qué.** El C5 y la Jefatura de Gobierno, que anuncian ampliaciones de la red;
la decisión es la ubicación de los postes nuevos.

**Hipótesis.** La cobertura es desigual respecto al delito: al menos una de cada tres
colonias del decil más alto de robo a transeúnte tiene una cobertura por debajo de la
mediana de la ciudad. *Se rechaza si* la cobertura crece de forma monótona con el robo.

**Datos — y aquí se cae.** El archivo que el repo llama `postes_c5_cdmx.xlsx` es el conjunto
**«WiFi gratuito en postes del C5»**: 13,714 puntos con `id`, `programa`, latitud, longitud
y alcaldía, corte de julio de 2025. Es la lista de postes con punto de acceso WiFi, no el
inventario de cámaras: la prensa habla de más de 43 mil cámaras, y no hay fecha de
instalación ni tipo de equipo. El otro conjunto relacionado, `programa-mi-calle-shapes`, se
vio en el catálogo pero **no se descargó ni se inspeccionó hoy**. No encontré un inventario
público y descargable de las cámaras del C5.

**Método.** Cobertura por radio y un problema de máxima cobertura resuelto de forma voraz
sobre las celdas del encuadre 2. Adecuado porque la decisión es literalmente de ubicación;
sin fechas de instalación no se puede decir nada sobre efecto, solo sobre cobertura.

**Dashboard.** Mapa de cobertura actual, robos sin cubrir y las N ubicaciones propuestas
con la ganancia marginal de cada una.

**Riesgo principal.** Ya materializado: el numerador de la cobertura no es el que la
pregunta necesita. Cualquier porcentaje de cobertura sería un artefacto de qué postes
tienen WiFi.

**Antecedentes.** Piza et al. (2019), metaanálisis de 76 evaluaciones: reducción de 13 %,
sin efecto en delitos violentos — leído a través de la columna de Vilalta en *El Universal*
(<https://www.eluniversal.com.mx/opinion/carlos-vilalta/las-camaras-de-videovigilancia-si-sirven/>),
no en el original. «Videovigilancia en la Ciudad de México y su efecto en la disminución de
la incidencia delictiva», *Revista Científica General José María Córdova* 23(51)
(<http://www.scielo.org.co/pdf/recig/v23n51/2500-7645-recig-23-51-682.pdf>): no abrió; el
buscador resume resultados mixtos y una evaluación de MiCalle sin efecto en robo.

---

## Lo que se miró y no llegó a candidato

- **Demora entre el hecho y la denuncia** (la H2 de la entrega del 14). Medido hoy: en robo
  a transeúnte la mediana es de **0 días** y el percentil 90 de 8; no hay variación que
  explicar. Sí la hay en violación (mediana 3, p75 34, p90 227 días; 12,743 carpetas) y en
  fraude (mediana 13). Un encuadre sobre demora en delitos sexuales sería factible por
  alcaldía, con Klemmer, Neill y Jarvis (2021) de antecedente, pero la decisión que cambia
  no quedó nombrada con precisión, y por la regla del punto 2 se descarta.
- **Delitos contra mujeres en el espacio público y el programa Senderos Seguros.** Las
  víctimas de la FGJ traen sexo, edad, hora y coordenadas, pero el trazo de los senderos no
  está en el portal (la búsqueda solo devuelve `programa-mi-calle-shapes`). Sin ese dato no
  hay decisión que evaluar.
- **Cifra negra por alcaldía con la ENVIPE.** Descartado desde el 13 de septiembre: la
  encuesta no es representativa por alcaldía.
- **Estado de fuerza por cuadrante.** El conjunto abierto solo llega a zona y turno; no se
  puede comparar policías contra delito por cuadrante.

---

## Orden, de más a menos viable

Criterios en el orden pedido: (a) la decisión existe y hoy se toma a ciegas; (b) datos
verificados; (c) recorte estrecho.

1. **Metro por estación (encuadre 1).** La decisión es la más concreta de las cinco y hoy
   se comunica con conteos; todos los datos están bajados y el cruce espacial ya funcionó
   (92.4 % a menos de 150 m); el recorte es el más estrecho —un delito, 163 estaciones, una
   tasa—; baja de alcaldía; y la app estática es trivial. Su riesgo (transbordos en el
   denominador) se detecta el primer día y tiene salida.
2. **Puntos calientes con evaluación hacia adelante (encuadre 2).** Decisión real, datos
   impecables (98.2 % con coordenadas), señal ya confirmada. Baja al segundo lugar porque
   la cifra negra contamina justo lo que ordena y porque es el terreno más transitado: se
   defiende con rigor, no con novedad.
3. **Percepción contra robo (encuadre 3, el vigente).** Es el que tiene los datos más
   trabajados y el único ya presentado a los sinodales, pero por el criterio (a) queda
   detrás: la decisión que cambia es de medición, no de acción, y no puede bajar de
   alcaldía. Si el costo de cambiar de encuadre ante los sinodales pesa más que estos
   criterios, es el que menos riesgo de calendario tiene: el panel existe.
4. **Disparos al 911 (encuadre 4).** El más cercano a la tensión central del caso y el más
   original, pero con la fuente más sucia, tres años de antigüedad y solo 10 % de llamadas
   confirmadas. Alto riesgo de terminar sin hallazgo defendible.
5. **Cobertura de videovigilancia (encuadre 5).** Sin inventario de cámaras no hay pregunta.

**Cuál descartaría yo: el 5, sin duda**, porque falla el criterio (b) de raíz: el dato
público no mide lo que la pregunta necesita, y eso no se arregla con trabajo. Descartaría
también el 4 salvo que se quiera jugar la carta del subregistro a sabiendas del riesgo.

**Una combinación que no infla el alcance:** los encuadres 1 y 3 comparten casi todo el
pipeline de carpetas y son independientes entre sí. Si el cambio de encuadre hay que
justificarlo ante los sinodales, el 1 se puede presentar como el acotamiento que pidieron el
14 de septiembre llevado un paso más lejos —un delito, un lugar, una unidad por debajo de
alcaldía—, y el 3 queda como contexto ya hecho. Eso es una decisión de Sebas y, en su caso,
una pregunta para los sinodales; no se adivina aquí.

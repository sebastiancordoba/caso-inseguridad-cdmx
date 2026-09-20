# Fase 2 — Datos y pruebas de viabilidad del encuadre del Metro

*Corrido el 2026-09-20 con `python src/metro/correr.py`. **Resultado: C1 pasa, C2 falla.
Se paró ahí, como estaba acordado:** no se corrió C3, no se hizo el EDA y no existe
`docs/hipotesis.md`. No se intentó arreglar nada. El numerador son DENUNCIAS (carpetas de
la FGJ), por fecha del hecho, 2019-01 a 2024-12. Decisiones y su porqué:
[`decisiones.md`](decisiones.md).*

## A. Llave de estaciones — `datos/procesados/llave_estaciones.csv`

395 grafías crudas (nombre, línea) del archivo de afluencia → 195 puntos estación-línea →
163 estaciones. Cruce por igualdad exacta tras normalizar, dentro de la misma línea; nada
aproximado. Todo punto del shapefile tiene afluencia y toda grafía de la afluencia tiene
punto.

Lo que no casó 1 a 1, completo:

- **Resueltos a mano (3):** L3 «Niños Héroes» → «Niños Héroes/Poder Judicial CDMX» (el
  shapefile trae el nombre oficial nuevo); L6 «UAM-Azcapotzalco» → «UAM Azcapotzalco»
  (guion); L9 «Mixiuhca» → «Mixhiuca» (la errata es del shapefile).
- **Un mismo punto con dos grafías crudas (5):** Gómez Farías (L1), Villa de Cortés (L2),
  Peñón Viejo (LA) y Olímpica (LB) cambian de grafía el 1 de junio de 2023; Miguel Ángel
  de Quevedo (L3), en julio de 2026.
- **Casan al normalizar pero difieren en acentos o mayúsculas (6):** Gomez Farías, Isabel
  La Católica, Periferico Oriente, San Andres Tomatlán, San Pedro de Los Pinos, Peñón viejo.
- **La columna `linea` también viene rota:** 24 grafías para 12 líneas («Linea 1» y
  «LÃ­nea 1»); la segunda cubre del 1 de enero de 2021 al 31 de mayo de 2023 y es
  complementaria de la primera, no duplicada. 57 de los 168 nombres crudos de estación
  traen la doble codificación.
- **Correspondencias:** la lista escrita a mano (28 estaciones, 60 puntos) coincide
  exactamente con el campo `TIPO` del shapefile.
- **Encontrado y no previsto:** 11 estaciones están en el Estado de México (Cuatro Caminos,
  La Paz, Los Reyes y ocho de la Línea B). Sus robos se denuncian ante otra fiscalía; van
  marcadas con `fuera_cdmx`.
- **El shapefile se llama «utm14n» pero declara EPSG:4326 y trae grados.** Se reproyecta
  antes de medir distancias; sin eso, toda carpeta queda «a 0 m».

## B. Panel — `datos/procesados/panel_estacion.csv`

163 estaciones × 72 meses = 11,736 filas. Columnas: `estacion`, `anio_mes`, `anio`, `mes`,
`lineas`, `n_lineas`, `es_correspondencia`, `fuera_cdmx`, `robos_denunciados_total`,
`robos_denunciados_con_violencia`, `robos_denunciados_sin_violencia`, `entradas`,
`dias_con_dato`, `dias_sin_entradas`, `entradas_dudosas`. A nivel carpeta, con la distancia
de todas: `datos/procesados/denuncias_metro_asignadas.csv`.

| Carpetas | |
|---|---|
| Del delito, todos los años | 15,760 |
| Sin fecha del hecho | 1 |
| En la ventana 2019–2024 por fecha del hecho | 8,366 |
| Sin coordenadas | 1,041 |
| Con coordenadas, a más de 150 m de toda estación | 559 (277 entre 150 y 250 m; 184 entre 250 y 500; 75 entre 500 m y 1 km; 23 a más de 1 km) |
| **Asignadas a una estación** | **6,766** |
| **Sin asignar** | **1,600 (19.1 %)** |

**La falta de coordenadas no es aleatoria.** Por año: 47, 26, 111, 211, **455** y 191 de
2019 a 2024. Solo el 0.8 % de las que no traen coordenadas son con violencia, contra 8.9 %
de las que sí traen. No se imputan. Esto sesga cualquier tendencia por estación de 2022 en
adelante y el contraste con y sin violencia.

**Entradas:** 6,600 millones en la ventana. 648 estaciones-mes con cero entradas
(estaciones cerradas: L12, L1, pandemia), con 9 robos denunciados que no tienen
denominador. **Dos estaciones-mes sin entradas conocidas:** Oceanía y Deportivo Oceanía en
diciembre de 2020, porque en la Línea B «Oceanía» viene duplicada (62 filas, 383,196
entradas entre las dos series) y «Deportivo Oceanía» no viene; no hay forma de saber qué
serie es de cuál y no se repartió.

## C1. Aritmética del titular — **pasa**

Tasa de la red: **1.02 robos denunciados por millón de entradas** (6,756 / 6,600 M).
Mediana entre estaciones: 0.74.

| Universo | Estaciones | Spearman conteo–tasa | Coincidencias en top-10 | ¿Falla? |
|---|---|---|---|---|
| Todas | 163 | 0.693 | 8 | No |
| Solo CDMX | 152 | 0.621 | 8 | No |
| 30 o más robos denunciados | 53 | 0.684 | 8 | No |

Pasa por el criterio (hacía falta ρ ≥ 0.9 **y** 9 coincidencias), pero no con holgura en
la cabeza: ocho de las diez primeras son las mismas. **Pantitlán no sale cerca del promedio
de la red:** baja del lugar 1 al 20, pero con 1.60 sigue 57 % arriba de la tasa de la red.
Lo que el conteo sí esconde está más abajo: Indios Verdes (14 → 99) y Constitución de 1917
(17 → 108) son terminales de mucha afluencia con tasa por debajo de la red.

Las 20 primeras por conteo (entradas en millones; cambio positivo = sube al ordenar por tasa):

| Pos. conteo | Estación | Líneas | Corresp. | Robos denunciados | Entradas (M) | `tasa_denuncias_mm` | Pos. tasa | Cambio |
|---|---|---|---|---|---|---|---|---|
| 1 | Pantitlán | 1·5·9·A | sí | 491 | 306.5 | 1.60 | 20 | −19 |
| 2 | Hidalgo | 2·3 | sí | 483 | 75.7 | 6.38 | 1 | +1 |
| 3 | Pino Suárez | 1·2 | sí | 288 | 93.7 | 3.07 | 7 | −4 |
| 4 | Chabacano | 2·8·9 | sí | 254 | 68.8 | 3.69 | 4 | 0 |
| 5 | Tacubaya | 1·7·9 | sí | 228 | 142.7 | 1.60 | 21 | −16 |
| 6 | Balderas | 1·3 | sí | 207 | 58.1 | 3.56 | 5 | +1 |
| 7 | Zapata | 3·12 | sí | 180 | 60.7 | 2.96 | 8 | −1 |
| 8 | Centro Médico | 3·9 | sí | 177 | 55.8 | 3.17 | 6 | +2 |
| 9 | Guerrero | 3·B | sí | 163 | 28.1 | 5.79 | 2 | +7 |
| 10 | Tacuba | 2·7 | sí | 158 | 71.7 | 2.20 | 9 | +1 |
| 11 | Bellas Artes | 2·8 | sí | 130 | 79.9 | 1.63 | 17 | −6 |
| 12 | Oceanía | 5·B | sí | 128 | 33.3 | 3.84 | 3 | +9 |
| 13 | San Lázaro | 1·B | sí | 121 | 62.3 | 1.94 | 14 | −1 |
| 14 | Indios Verdes | 3 | no | 114 | 180.4 | 0.63 | 99 | −85 |
| 15 | Zócalo/Tenochtitlan | 2 | no | 108 | 83.5 | 1.29 | 29 | −14 |
| 16 | Mixcoac | 7·12 | sí | 101 | 56.9 | 1.78 | 16 | 0 |
| 17 | Constitución de 1917 | 8 | no | 94 | 170.6 | 0.55 | 108 | −91 |
| 18 | Merced | 1 | no | 90 | 56.8 | 1.59 | 22 | −4 |
| 19 | Garibaldi/Lagunilla | 8·B | sí | 89 | 45.2 | 1.97 | 12 | +7 |
| 20 | Buenavista | B | no | 88 | 97.6 | 0.90 | 60 | −40 |

Ya aquí se ve el problema de C2: **las trece primeras por conteo son correspondencias.**

## C2. Contaminación del denominador — **FALLA**

Criterio fijado antes de correr: falla con 7 o más correspondencias entre las 10 primeras
por tasa, o 12 o más entre las 20 primeras.

| | Todas | Solo CDMX | 30 o más robos denunciados |
|---|---|---|---|
| Estaciones / de correspondencia | 163 / 28 | 152 / 28 | 53 / 24 |
| **Correspondencias en el top-10 por tasa** (esperadas por azar) | **9** (1.7) | **9** (1.8) | **10** (4.5) |
| **Correspondencias en el top-20 por tasa** (esperadas por azar) | **17** (3.4) | **17** (3.7) | **18** (9.1) |
| Mediana de `tasa_denuncias_mm`: con / sin correspondencia | 1.70 / 0.66 | 1.70 / 0.72 | 1.90 / 0.97 |
| Tasa conjunta: con / sin correspondencia | 2.10 / 0.62 | 2.10 / 0.71 | 2.21 / 0.88 |

Las diez primeras por tasa: Hidalgo, Guerrero, Oceanía, Chabacano, Balderas, Centro Médico,
Pino Suárez, Zapata, Tacuba —todas correspondencias— y Bosque de Aragón (20 robos
denunciados, 9.6 M de entradas). Las 20 primeras completas están en
`datos/procesados/metro_tablas/c1_top20_por_tasa.csv`.

Por número de líneas que pasan por la estación:

| Líneas | Estaciones | Robos denunciados | Entradas (M) | Mediana de tasa | Tasa conjunta |
|---|---|---|---|---|---|
| 1 | 135 | 2,945 | 4,787 | 0.66 | 0.62 |
| 2 | 25 | 2,838 | 1,295 | 1.78 | 2.19 |
| 3 | 2 | 482 | 211 | 2.64 | 2.28 |
| 4 | 1 | 491 | 306 | 1.60 | 1.60 |

**Lectura.** El orden por tasa es, en la cabeza, una lista de correspondencias: la tasa
conjunta de las correspondencias es 3.4 veces la del resto. Eso es lo que se esperaría si
el denominador deja fuera a quien transborda: esa gente está expuesta en la estación y
puede ser robada y denunciar ahí, pero no pasó por su torniquete. Con estos datos no se
puede separar ese artefacto de un riesgo real mayor en las correspondencias (aglomeración,
pasillos largos), ni de un tercer mecanismo que tampoco se ha verificado: que la carpeta
se ubique donde se denunció o donde el pasajero se bajó, y no donde ocurrió el robo. Las
tres explicaciones empujan en la misma dirección. La tasa no es monótona en el número de
líneas (Pantitlán, con cuatro, tiene 1.60), pero Pantitlán es además terminal, con las
entradas más altas de la red; eso no rescata la prueba.

**C3, el EDA y `hipotesis.md` no se hicieron**: la regla era parar en la primera prueba
que fallara.

## Supuestos que quedaron sin verificar

1. **Dónde ubica la FGJ una carpeta «a bordo del Metro»**: ¿donde ocurrió, donde se bajó
   la víctima o donde denunció? No está documentado en el diccionario ni en las notas
   técnicas leídas. Es el supuesto que más pesa y afecta a numerador y a C2 por igual.
2. **Que las 1,041 carpetas sin coordenadas falten al azar entre estaciones.** No faltan al
   azar en el tiempo ni por tipo (2022–2024, casi todas sin violencia); entre estaciones
   no se sabe.
3. **Que las 559 carpetas a más de 150 m no sean de una estación.** La sensibilidad al
   umbral (100, 150, 250 m) se puede hacer con `distancia_m`, pero no se hizo: no cambia C2.
4. **Que la afluencia mida entradas por torniquete y nada más.** El diccionario dice
   «afluencia en número de personas» y no aclara si incluye cortesías, transbordos o
   accesos gratuitos; la lectura «entradas» es la habitual, no una verificada hoy.
5. **Que la propensión a denunciar sea pareja entre estaciones.** Si en unas estaciones hay
   agencia del Ministerio Público o módulo de denuncia y en otras no, el numerador mide en
   parte eso. No se buscó el dato.
6. **Exposición lineal (C3):** sin correr.
7. **Cobertura temporal:** las carpetas terminan en enero de 2025; la afluencia sigue hasta
   julio de 2026. La ventana de análisis la fija la fuente más corta.

## ¿Sigue de pie el encuadre?

Tal como está escrito, **no**. La pregunta promete un orden de estaciones por riesgo por
pasajero, y lo que el orden por tasa entrega en la cabeza es la lista de correspondencias
—las mismas estaciones que ya encabezan el conteo—, por una razón que no se puede
distinguir de un defecto del denominador. Una app con ese ranking le diría a la SSC lo que
ya sabe y por la razón equivocada.

Lo que sí sobrevive, como observación y no como arreglo (no se probó nada de esto):

- **Entre las 135 estaciones sin correspondencia el denominador no tiene ese problema**, y
  ahí el conteo sí esconde cosas: Indios Verdes y Constitución de 1917 caen unos noventa
  lugares; Bosque de Aragón y Ciudad Deportiva suben más de sesenta. Un encuadre acotado a
  estaciones de paso y terminales sería defendible, pero deja fuera las trece estaciones
  con más denuncias, que son las que más le importan a quien decide.
- **Un denominador que incluya transbordos** existe en principio (la EOD 2017 del INEGI
  trae viajes con transbordo y el shapefile trae `CVE_EOD17`), pero es de 2017, es de una
  encuesta y no se verificó hoy que sea descargable ni que llegue a estación. Es trabajo de
  otra fase y una decisión de Sebas, no de esta sesión.
- **El perfil hora × día por estación no depende del denominador** y sigue siendo útil para
  decidir la franja horaria del despliegue, que es la mitad de la decisión original.

## Cómo reproducir

```bash
python src/descarga.py --fuente estaciones   # carpetas FGJ + afluencia + estaciones
python src/metro/correr.py                   # 01 llave → 02 panel → 03 pruebas; sale con 2 si falla C1 o C2
```

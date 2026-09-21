# Fase 2b — ¿El orden por tasa mide dónde se puede denunciar?

*Corrido el 2026-09-20 con `python src/metro/correr.py` (paso `04_agencias.py`). Sin modelo:
tasas, razones y tablas. El numerador son DENUNCIAS (carpetas de la FGJ) por fecha del
hecho, 2019–2024. Siguen vigentes las advertencias de [`fase2-pruebas.md`](fase2-pruebas.md):
19.1 % de carpetas sin asignar y coordenadas que no faltan al azar.*

**Resultado: el efecto agencia NO queda establecido. Se paró en el punto de paro 1.** No se
corrieron T5 ni T6, no se hizo el EDA ni C3, y no existe `docs/hipotesis.md`. Sí se
corrieron T3, T4 y T7, que son de la misma tarea de diagnóstico o pura aritmética, y la
Tarea 5 ([`fuentes-conteo.md`](fuentes-conteo.md)), que no dependía del paro.

La hipótesis de trabajo era razonable y tenía un par llamativo a favor (Hidalgo 6.38
contra Bellas Artes 1.63). Lo que la tumba no es ese par, que se confirma, sino cuatro
cosas que los propios datos de la FGJ permiten ver y que en la fase 2 no se habían mirado:
la carpeta trae **la agencia que la abrió**.

## T0. Las agencias, con fechas — `datos/procesados/agencias_mp_metro.csv`

**Qué agencias existen sale de dos fuentes oficiales**, abiertas hoy: la página de la
Fiscalía de Investigación en Agencias de Atención Especializada de la FGJ, y el catálogo de
agencias de Denuncia Digital, que da la clave con la que cada agencia aparece en las
carpetas. **Ninguna de las dos da fechas** de apertura o cierre; no se usó prensa. Las
fechas salen de la actividad de cada clave en las carpetas (campo `agencia`, cualquier
delito, 2016 a enero de 2025).

| Clave | Nombre oficial | Estación | Ubicación | Vigencia en la ventana | Carpetas de cualquier delito, 2016 → 2024 | Robos a bordo del Metro que abrió, 2019–2024 |
|---|---|---|---|---|---|---|
| `STCMH` | Metro Hidalgo | Hidalgo | dentro de la estación | todo el periodo | 380, 713, 1,451, **559, 57, 30, 54, 61, 82** | 734 |
| `STCMP` | Metro Pantitlán | Pantitlán | dentro de la estación | todo el periodo | 374, 496, 929, 487, 129, 149, 116, 152, 139 | 441 |
| `STCMOB` | Metro Observatorio | Observatorio | dentro de la estación | **2019-01 a 2019-08** | 49, 276, 373, 101, 0, 0, 0, 0, 0 | 88 |
| `STCMZV` | Zarco y Violeta | (Guerrero) | **fuera de toda estación**, colonia Guerrero | todo el periodo | 548, 909, 1,212, 1,327, 549, 314, 274, 326, 237 | 1,211 |
| `STCMTS` | Tren Suburbano Buenavista | Buenavista | estación del Suburbano | todo el periodo | 20, 0, 0, 1, 37, 13, 18, 30, 30 | 18 (no cuenta como agencia del Metro) |
| — | Metro Pino Suárez | Pino Suárez | salida de la estación | **desconocida** | sin clave `STCM*` en las carpetas | — |

Tres correcciones a la lista de la que partía el encargo:

1. **La «agencia de Guerrero» no está en la estación Guerrero.** Es `STCMZV`, «Zarco y
   Violeta»: una esquina de la colonia Guerrero, entre las estaciones Guerrero e Hidalgo.
   La distancia a cada una no se midió. Es, además, la agencia del Metro que más carpetas
   abre.
2. **La agencia de Observatorio dejó de operar a mitad del periodo:** su última carpeta, de
   cualquier delito, es del 2 de agosto de 2019, y ya no está en la página de la FGJ. Es la
   variación temporal que se buscaba. `tiene_agencia` vale para Observatorio solo de
   2019-01 a 2019-08.
3. **Pino Suárez aparece hoy en la página de la FGJ** como agencia del Metro, pero ninguna
   clave de las carpetas le corresponde hasta enero de 2025. No se sabe desde cuándo opera
   ni cómo registra. No se marcó; es control de Hidalgo en T2 y podría estar contaminado.

**Denuncia Digital:** presentada por la ADIP y la entonces PGJ el 11 de noviembre de 2019,
**en operación desde el 6 de diciembre de 2019**, e incluye el robo sin violencia
(<https://adip.cdmx.gob.mx/comunicacion/nota/presentacion-de-nuevo-sistema-de-denuncia-digital>,
abierto hoy). En las carpetas se ve como la fiscalía «AGENCIA DE DENUNCIA DIGITAL».

Por dónde entraron los 8,366 robos denunciados de la ventana:

| Canal | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| Denuncia Digital | 4 | 179 | 542 | 955 | 887 | 686 | 3,253 |
| Agencias del Metro (`STCM*`) | 1,586 | 207 | 151 | 147 | 204 | 197 | 2,492 |
| Otra agencia | 1,183 | 391 | 243 | 243 | 265 | 296 | 2,621 |
| **% digital / % agencias del Metro** | 0 / 57 | 23 / 27 | 58 / 16 | 71 / 11 | 65 / 15 | 58 / 17 | 39 / 30 |

Las agencias del Metro abrían el 57 % de estas carpetas en 2019 y el 11 a 17 % desde 2021.
De las 1,041 carpetas sin coordenadas, 715 son digitales: **el faltante no aleatorio de
coordenadas de la fase 2 es, en buena parte, la Denuncia Digital.**

## La coordenada es el lugar del hecho, no la agencia

Era el supuesto sin verificar número 1 de la fase 2. Las carpetas que abrió cada agencia
del Metro, según la estación donde cae su coordenada:

| Agencia | Estación sede | Robos denunciados asignados | En la estación sede | % | Estaciones distintas |
|---|---|---|---|---|---|
| `STCMH` | Hidalgo | 658 | 91 | 13.8 | 97 |
| `STCMP` | Pantitlán | 381 | 85 | 22.3 | 89 |
| `STCMOB` | Observatorio | 86 | 2 | 2.3 | 38 |
| `STCMZV` | (Guerrero) | 1,147 | 43 | 3.7 | 124 |

La agencia de Hidalgo abre carpetas de robos ubicados en 97 estaciones. Las carpetas no se
geolocalizan donde se denuncia.

## T1. Observatorio — **sin anomalía**

Observatorio tuvo agencia y no es correspondencia. Su afluencia cae a cero desde diciembre
de 2023 (cierre del tramo poniente de la Línea 1); las tres ventanas la esquivan.
Referencia: 123 estaciones sin correspondencia dentro de la CDMX.

| Ventana | Robos denunciados | Entradas (M) | `tasa_denuncias_mm` | IC 95 % (Poisson, Byar) | Percentil | Mediana / p90 de referencia |
|---|---|---|---|---|---|---|
| (a) 2019-01 a 2019-08, **con agencia** | 6 | 17.6 | 0.34 | 0.12 a 0.74 | **14.6** | 1.11 / 2.55 |
| (b) 2019-09 a 2021-12, **sin agencia** | 12 | 34.3 | 0.35 | 0.18 a 0.61 | 13.0 | 0.71 / 1.36 |
| (c) 2019 a 2021, la del encargo | 18 | 51.9 | 0.35 | 0.21 a 0.55 | 5.7 | 0.87 / 1.68 |

Con la agencia dentro de la estación, Observatorio está en el percentil 15; al cerrar la
agencia su tasa no se mueve (0.34 → 0.35). El caso que aislaba el efecto agencia del efecto
transbordo no muestra efecto. *Advertencia:* son 6 y 12 carpetas; los intervalos son anchos,
pero su techo (0.74) queda por debajo de la mediana de referencia (1.11).

## T2. Comparaciones emparejadas — anomalía en Hidalgo y Guerrero, **que no es de la agencia**

Criterio fijado antes de correr (decisión 19): hay anomalía si la tasa es al menos el doble
de la mediana de sus controles; se atribuye a la agencia solo si **no** persiste cuando el
numerador son únicamente denuncias digitales (2020–2024), que se hacen desde un teléfono y
no dependen de tener una agencia a la mano.

| Grupo | Rol | Estación | Robos denunciados | Entradas (M) | `tasa_denuncias_mm` | IC 95 % | Solo digital: robos denunciados / tasa |
|---|---|---|---|---|---|---|---|
| Hidalgo | **con agencia** | Hidalgo | 483 | 75.7 | **6.38** | 5.82 a 6.97 | 182 / **3.07** |
| | control | Bellas Artes | 130 | 79.9 | 1.63 | 1.36 a 1.93 | 37 / 0.60 |
| | control | Balderas | 207 | 58.1 | 3.56 | 3.10 a 4.08 | 71 / 1.50 |
| | control | Salto del Agua | 61 | 51.0 | 1.20 | 0.92 a 1.54 | 17 / 0.45 |
| | control | Pino Suárez (¿agencia?) | 288 | 93.7 | 3.07 | 2.73 a 3.45 | 83 / 1.14 |
| Guerrero | **con agencia** (adyacente) | Guerrero | 163 | 28.1 | **5.79** | 4.94 a 6.76 | 50 / **2.26** |
| | control | Garibaldi/Lagunilla | 89 | 45.2 | 1.97 | 1.58 a 2.42 | 23 / 0.64 |
| | control | Morelos | 43 | 23.2 | 1.86 | 1.34 a 2.50 | 12 / 0.66 |
| | control | Oceanía | 128 | 33.3 | 3.84 | 3.21 a 4.57 | 36 / 1.36 |
| | control | Jamaica | 40 | 32.7 | 1.22 | 0.87 a 1.67 | 10 / 0.40 |
| Pantitlán | **con agencia** | Pantitlán | 491 | 306.5 | **1.60** | 1.46 a 1.75 | 145 / 0.62 |
| | control | Tacubaya | 228 | 142.7 | 1.60 | 1.40 a 1.82 | 93 / 0.83 |
| | control | Chabacano | 254 | 68.8 | 3.69 | 3.25 a 4.17 | 105 / 1.99 |
| | control | San Lázaro | 121 | 62.3 | 1.94 | 1.61 a 2.32 | 42 / 0.92 |
| Observatorio (2019-01 a 08) | **con agencia** | Observatorio | 6 | 17.6 | **0.34** | 0.12 a 0.74 | — |
| | control | Tasqueña | 13 | 18.0 | 0.72 | 0.38 a 1.23 | — |
| | control | Universidad | 2 | 17.6 | 0.11 | 0.01 a 0.41 | — |
| | control | Barranca del Muerto | 5 | 11.1 | 0.45 | 0.15 a 1.05 | — |

Por qué cada control: está escrito en `PARES`, en `src/metro/04_agencias.py`, y en
`datos/procesados/metro_tablas/t2_pares_detalle.csv`. Pantitlán no tiene par real (única
con cuatro líneas y 306 M de entradas); sus controles son los menos malos y dos de tres se
salen de la regla de entradas.

| Estación con agencia | Tasa | Mediana de controles | **Razón, todos los canales** | Tasa solo digital | Mediana de controles, solo digital | **Razón, solo digital** |
|---|---|---|---|---|---|---|
| Hidalgo | 6.38 | 2.35 | **2.71** | 3.07 | 0.87 | **3.53** |
| Guerrero | 5.79 | 1.92 | **3.02** | 2.26 | 0.65 | **3.48** |
| Pantitlán | 1.60 | 1.94 | 0.82 | 0.62 | 0.92 | 0.67 |
| Observatorio | 0.34 | 0.45 | 0.76 | — | — | — |

Hidalgo y Guerrero sí son anómalas. Pero **el exceso es igual o mayor en el canal
digital**: quien denuncia desde su teléfono un robo en Hidalgo no lo hace porque haya una
agencia en Hidalgo. Y dos de las cuatro estaciones con agencia (Pantitlán, con la agencia
adentro, y Observatorio) no muestran exceso alguno.

Una tercera comprobación, en la misma dirección. Si tener la agencia a la mano hiciera
denunciar más, en la estación sede pesaría más el canal «agencia del Metro». No pesa más:

| Estación | Rol | % por agencia del Metro | % digital | % otra agencia | Total |
|---|---|---|---|---|---|
| Hidalgo | **con agencia** | 46.0 | 37.9 | 16.1 | 483 |
| Bellas Artes | control | 48.5 | 28.5 | 23.1 | 130 |
| Pino Suárez | control | 49.7 | 28.8 | 21.5 | 288 |
| Balderas | control | 39.1 | 34.3 | 26.6 | 207 |
| Guerrero | **con agencia** | 43.6 | 30.7 | 25.8 | 163 |
| Garibaldi/Lagunilla | control | 44.9 | 25.8 | 29.2 | 89 |
| Oceanía | control | 47.3 | 27.9 | 24.8 | 129 |
| Pantitlán | **con agencia** | 45.8 | 29.5 | 24.6 | 491 |
| Chabacano | control | 40.9 | 41.3 | 17.7 | 254 |
| Toda la red | | 33.8 | 33.6 | 32.6 | 6,766 |

Hidalgo y Bellas Artes reciben por agencias del Metro la misma proporción de sus denuncias
(46 y 48.5 %). La tabla completa está en `metro_tablas/agencias_canal_por_estacion.csv`.

## T3. Estratificación 2 × 2

| Agencia | Correspondencia | Estaciones | Robos denunciados | % de los robos denunciados | % de las entradas | Tasa conjunta | Mediana de tasas |
|---|---|---|---|---|---|---|---|
| no | no | 134 (123 en la CDMX) | 2,919 | 43.2 | 71.4 | 0.62 (0.71 solo CDMX) | 0.66 (0.72) |
| no | sí | 25 | 2,674 | 39.6 | 21.3 | 1.91 | 1.63 |
| sí | no | 1 (Observatorio) | 26 | 0.4 | 1.2 | 0.34 | 0.34 |
| sí | sí | 3 (Guerrero, Hidalgo, Pantitlán) | 1,137 | 16.8 | 6.2 | 2.77 | 5.79 |

Observatorio cuenta aquí como «con agencia» aunque solo la tuvo ocho meses. Lo que la
tabla dice: **el salto grande está en la correspondencia (0.62 → 1.91, sin agencia de por
medio), no en la agencia.** La celda con agencia y correspondencia (2.77) es mayor que la de
correspondencia sola, pero son tres estaciones y la diferencia la ponen Hidalgo y Guerrero:
Pantitlán tiene 1.60, por debajo de 1.91. La primera fila es, de paso, lo que T6 iba a
medir: las estaciones sin correspondencia ni agencia concentran el 43 % de los robos
denunciados y el 71 % de las entradas.

## T4. ¿El exceso se diluye con los años? — **no: crece**

Si la agencia inflara el numerador, el exceso debería bajar conforme la denuncia se muda al
canal digital. Razón de tasas contra las otras 25 correspondencias:

| Año | Hidalgo y Guerrero | Pantitlán | Otras correspondencias | Sin correspondencia | **Razón Hidalgo+Guerrero / otras corresp.** | Razón Pantitlán / otras corresp. | Razón corresp. / sin corresp. | % digital | % agencias del Metro |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | 8.91 | 2.54 | 3.40 | 0.95 | **2.62** | 0.75 | 3.75 | 0 | 57 |
| 2020 | 4.21 | 1.42 | 1.33 | 0.51 | **3.16** | 1.07 | 2.95 | 23 | 27 |
| 2021 | 5.31 | 1.20 | 1.91 | 0.62 | **2.78** | 0.63 | 3.10 | 58 | 16 |
| 2022 | 6.90 | 1.47 | 1.71 | 0.64 | **4.03** | 0.86 | 3.06 | 71 | 11 |
| 2023 | 4.93 | 1.59 | 1.29 | 0.42 | **3.82** | 1.23 | 3.73 | 65 | 15 |
| 2024 | 5.73 | 0.79 | 1.23 | 0.40 | **4.67** | 0.65 | 3.70 | 58 | 17 |

Figura: `docs/figuras/metro/t4_razon_agencia_por_anio.png`. El exceso de Hidalgo y Guerrero
pasa de 2.6 a 4.7 mientras las agencias del Metro pasan de abrir el 57 % de las carpetas al
17 %. Es evidencia **en contra** del mecanismo. La razón correspondencia / sin
correspondencia, en cambio, es estable (3.0 a 3.8): lo que sea que infla a las
correspondencias no depende del canal de denuncia. *Advertencia:* desde 2022 faltan más
coordenadas, sobre todo en el canal digital; si faltaran más en unas estaciones que en
otras, estas razones se moverían. No se sabe.

## T7. Cota: cuántos transbordos harían falta

Aritmética, no estimación: `denuncias / (entradas + T) = tasa de las estaciones de paso`.
Tasa de las estaciones sin correspondencia dentro de la CDMX: 0.71.

**Para las 28 correspondencias en conjunto harían falta 3,583 millones de transbordos en
seis años: 1.98 veces sus propias entradas, el 60 % de las entradas de toda la red.**

| Estación | Tasa | Transbordos necesarios (M) | Como múltiplo de sus entradas |
|---|---|---|---|
| Hidalgo | 6.38 | 608 | **8.0** |
| Guerrero | 5.79 | 203 | **7.2** |
| Oceanía | 3.84 | 148 | 4.4 |
| Chabacano | 3.69 | 291 | 4.2 |
| Balderas | 3.56 | 235 | 4.0 |
| Centro Médico | 3.17 | 195 | 3.5 |
| Pino Suárez | 3.07 | 314 | 3.4 |
| Zapata | 2.96 | 194 | 3.2 |
| Tacuba | 2.20 | 152 | 2.1 |
| Pantitlán | 1.60 | 389 | 1.3 |
| Tacubaya | 1.60 | 180 | 1.3 |
| Bellas Artes | 1.63 | 104 | 1.3 |
| Mediana de las 28 | | | 1.4 |
| El Rosario / Martín Carrera | 0.49 / 0.23 | negativos | ya están por debajo de la tasa de paso |

Completa en `metro_tablas/t7_transbordos_necesarios.csv`. **Lectura, con el criterio del
encargo:** no es «más transbordos que entradas de toda la red» ni es «un 20 % más». Para el
conjunto, y para la mayoría de las correspondencias (entre 0.5 y 2 veces sus entradas), un
flujo de transbordo de ese tamaño **es verosímil** —en una correspondencia es normal que
transborde más gente de la que entra—, así que el defecto del denominador alcanza, él solo,
para explicar el grueso de C2. Para Hidalgo y Guerrero (ocho y siete veces sus entradas) no
parece verosímil: ahí hay algo más que el torniquete. No hay dato de transbordos en el repo
contra el cual comprobar ninguna de las dos afirmaciones; «verosímil» es juicio, no
medición.

## Punto de paro 1

- **T1:** sin anomalía en Observatorio (percentil 15 con agencia; igual sin ella).
- **T2:** anomalía en Hidalgo (2.7×) y Guerrero (3.0×); ninguna en Pantitlán (0.8×) ni en
  Observatorio (0.8×). La anomalía de Hidalgo y Guerrero **persiste en el canal digital**
  (3.5×), así que no es atribuible a la agencia.
- Además: las carpetas de cada agencia se reparten por toda la red; la mezcla de canales es
  igual en las estaciones sede que en sus controles; y el exceso crece cuando las agencias
  pierden peso.

Por el criterio fijado antes de correr, **el efecto agencia no queda establecido** y se
paró. La letra del encargo decía parar «si T1 y T2 no muestran anomalía», y T2 sí la
muestra en dos estaciones; se paró de todos modos porque la Tarea 2 estaba condicionada a
que «el efecto agencia quede establecido», y definir un «estrato limpio» quitando estaciones
con agencia sería corregir por un efecto que los datos no respaldan.

## Lectura: qué queda de pie

**El encuadre corregido, tal como está escrito —«el ranking oficial mide volumen y lugar de
denuncia, no riesgo»— no queda de pie en su segunda mitad.** El lugar de denuncia no deja
huella en los datos: ni en dónde caen las coordenadas, ni en la mezcla de canales, ni en
el único caso limpio (Observatorio), ni en el tiempo.

Lo que sí queda establecido, con estos datos y sin modelo:

1. **El ranking oficial mide volumen.** C1 lo mostró (Pantitlán 1 → 20; Indios Verdes 14 →
   99; Constitución de 1917 17 → 108) y las fuentes lo confirman: todas las listas
   publicadas son conteos, ninguna declara método y ninguna normaliza
   ([`fuentes-conteo.md`](fuentes-conteo.md)).
2. **La tasa por entradas no sirve para comparar correspondencias con estaciones de paso**,
   y T7 dice que un flujo de transbordo de tamaño verosímil basta para explicar la mayor
   parte de esa diferencia. Eso es un resultado sobre el denominador, no sobre el riesgo.
3. **Hidalgo y Guerrero son anómalas de verdad**: entre tres y cuatro veces sus pares, en
   todos los canales, todos los años, y más de lo que un transbordo verosímil explica. Son
   contiguas por la Línea 3. Con estos datos no se sabe si es riesgo real o algo de cómo se
   registra el lugar del hecho en esa zona; lo que ya se sabe es que no es la agencia.
4. **El subconjunto donde el encuadre original sí se sostiene existe y es grande**: las 123
   estaciones sin correspondencia de la CDMX tienen el 43 % de los robos denunciados y el
   71 % de las entradas, y ahí el denominador es lo que el torniquete mide. No se probó si
   dentro de ese subconjunto el conteo basta (era T5, que no se corrió).

Alcance honesto: hay material para una tesis sobre **qué se puede y qué no se puede decir
del riesgo por estación con datos abiertos** —el ranking oficial es volumen; la corrección
obvia falla en las correspondencias por una razón cuantificable; el mecanismo de denuncia,
que era la sospecha natural, se descarta con los propios datos de la FGJ—, pero no para un
ranking de riesgo de toda la red. Si ese alcance vale como tesis, y si se corre T5 sobre las
estaciones sin correspondencia (ya sin el filtro de agencia, que no se justifica), es
decisión de Sebas.

## Supuestos sin verificar

1. Que el lugar que captura la Denuncia Digital sea el del hecho y no, por ejemplo, el
   domicilio del denunciante. Las 2,273 digitales asignadas caen a 150 m o menos de una
   estación, lo que sugiere que sí; no está documentado.
2. La distancia real de la agencia de Zarco y Violeta a Guerrero y a Hidalgo.
3. Desde cuándo opera la agencia de Pino Suárez y con qué clave registra.
4. Que las coordenadas faltantes (715 de 1,041 son digitales) falten parejo entre
   estaciones. Afecta sobre todo a T4 y a las tasas solo-digitales.
5. Que «verosímil» en T7 sea correcto: no hay dato de transbordos por estación en el repo.
6. C3 (exposición lineal) sigue sin correr.

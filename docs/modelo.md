# El modelo: tasa de denuncias por entrada, encogida

*Corrido el 2026-09-20 con `python src/metro/08_modelo.py`, **después** de congelar las
hipótesis M1 a M7 en [`hipotesis.md`](hipotesis.md) (commit `ccb6aa2`, 19:43, que no contiene
ningún modelo). El numerador son DENUNCIAS. Tabla final para la app:
`datos/procesados/modelo_estaciones.csv`. Diagnósticos: `metro_tablas/modelo_*.csv` y
`modelo_diagnostico.json`.*

```
y_st ~ NB(mu_st, phi)      log mu_st = log E_st + alpha + v_s + gamma_t      v_s ~ N(0, sigma²)
```

`y_st` robos denunciados asignados a la estación *s* en el año *t*; `E_st` millones de
entradas en los meses en que estuvo abierta; `gamma_t` suma cero. Cantidad de interés:
`exp(alpha + v_s)`, la tasa de denuncias por millón de entradas de la estación en un año
«promedio», **encogida** hacia la del estrato en proporción a la poca evidencia que tenga.

**Datos:** 124 estaciones × hasta 6 años = **715 celdas**, 2,919 robos denunciados, 4,096 M
de entradas; 14.5 % de las celdas en cero. Excluye abril–junio de 2020 (ver b).

**Cómo se ajustó.** Máxima verosimilitud marginal, escrita a mano (`scipy` para optimizar):
la integral sobre `v_s` se hace por estación con cuadratura de Gauss–Hermite adaptativa,
centrada en la moda de cada estación. La Poisson es el caso límite `phi → ∞` del mismo
código. No se usó una librería de modelos mixtos porque ninguna de las instaladas ajusta una
binomial negativa con efecto aleatorio, y son 9 parámetros.

**Advertencias vigentes.** 19.1 % de las carpetas sin asignar a estación; 715 de las 1,041
sin coordenadas son Denuncia Digital, concentradas en 2022–2024. El modelo supone que lo que
falta, falta parejo entre estaciones: el efecto de año absorbe el nivel, no un sesgo por
estación.

## Veredictos de las hipótesis congeladas

| # | Hipótesis | Resultado | Veredicto |
|---|---|---|---|
| M1 | Queda sobredispersión: hace falta la NB | LR = 21.44, p < 0.0001; ΔAIC = −19.4 a favor de la NB; `phi` = 16.5 | **Se sostiene.** La expectativa escrita de antemano era que podía fallar; no falló |
| M2 | La heterogeneidad entre estaciones es real | LR contra `sigma_v = 0`: 91.3, p ≈ 10⁻²¹; `sigma_v` = 0.40 | **Se sostiene** |
| M3 | El encogimiento conserva el orden (ρ ≥ 0.9) **y** saca del top-10 a las de menos de 15 denuncias | ρ = 0.985, pero **Hangares (12 denuncias) sigue en el top-10** | ❌ **Se rechaza** |
| M4 | Menos de 39 distinguibles, y conserva 12 o más de las 19 robustas | **25** distinguibles; conserva **19 de 19** | **Se sostiene** |
| M5 | El orden de 2019–2023 predice el de 2024, mejor que la tasa cruda y que el conteo | ρ = **0.303** contra 0.261 (cruda) y 0.289 (conteo); umbral 0.30 | **Se sostiene, por 0.003.** Ver d: frente al conteo no se distingue |
| M6 | El top-10 por tasa predicha cubre más denuncias de 2024 por millón de entradas que el top-10 por conteo | **0.77 contra 0.57**; en absoluto, 41 contra 92 denuncias | **Se sostiene**, con la salvedad anunciada |
| M7 | Excluir abril–junio de 2020 no cambia el orden (ρ ≥ 0.98) | ρ = 0.9985; mayor cambio, 8 lugares | **Se sostiene** |

## a. Poisson contra binomial negativa

| Modelo | Parámetros | log-verosimilitud | AIC | `sigma_v` | `phi` | Tasa base |
|---|---|---|---|---|---|---|
| Poisson, sin efecto de estación | 6 | −1,649.81 | 3,311.6 | — | — | 0.654 |
| NB, sin efecto de estación | 7 | −1,527.83 | 3,069.7 | — | 4.5 | 0.671 |
| Poisson + efecto de estación | 7 | −1,492.89 | 2,999.8 | 0.427 | — | 0.630 |
| **NB + efecto de estación** | 8 | **−1,482.17** | **2,980.3** | 0.402 | 16.5 | 0.633 |

- **Razón de verosimilitudes NB contra Poisson** (las dos con efecto de estación y de año):
  LR = 21.44. `phi → ∞` está en la frontera del espacio de parámetros, así que el valor p es
  la mitad del de χ²₁: **p < 0.0001**. **ΔAIC = −19.4.**
- **Dispersión de Pearson de la Poisson**, condicional a los efectos de estación: 738.3
  sobre 585 grados de libertad (conservadores: cada `v_s` contado como un parámetro) =
  **1.26**; p < 0.0001.
- **Resultado, declarado tal cual:** gana la NB. **Pero la sobredispersión que queda es
  leve.** Sin efecto de estación `phi` es 4.5; con él sube a 16.5 (IC 95 %: 9.2 a 29.5): con
  una media de 4 denuncias por celda, la varianza es 4 + 4²/16.5 ≈ 5, un 24 % sobre la
  Poisson. Casi toda la «sobredispersión» del panel era heterogeneidad entre estaciones y el
  salto de 2019, como sugería el EDA. El EDA acertó en el diagnóstico y erró en el
  pronóstico: a nivel mensual, quitando R1 y R2, la varianza era igual a la media, pero
  agregado por año queda un residuo que la Poisson no explica.
- **Para qué sirve la diferencia:** el orden casi no cambia entre Poisson y NB (Spearman
  0.997), pero los intervalos de la Poisson son más estrechos y **«distinguiría» 37
  estaciones contra 25 de la NB**. Ignorar esa sobredispersión leve habría dejado casi
  las mismas 39 de las pruebas una por una. La NB es el modelo final.

**Parámetros del modelo final.** Tasa base `exp(alpha)` = **0.633** denuncias por millón de
entradas (IC 95 %: 0.580 a 0.691). `sigma_v` = **0.402** (0.333 a 0.486): una estación a una
desviación por arriba tiene 1.5 veces la tasa de la estación típica; el 95 % de las
estaciones cae entre 0.45 y 2.2 veces. Efecto de año, `exp(gamma_t)`: **2019: 1.67**, 2020:
0.96, 2021: 1.11, 2022: 1.11, **2023: 0.73, 2024: 0.70**. El 1.67 de 2019 es el régimen R1;
la caída de 2023–2024 mezcla una baja real con las coordenadas que faltan, y el modelo no
las separa.

**Diagnósticos.** Convergencia: norma del gradiente ≈ 0.001 en los cuatro modelos.
Cuadratura: la log-verosimilitud con 25 y con 45 nodos coincide hasta la cuarta decimal.
Ceros: **104 celdas observadas en cero, 103.0 esperadas** por el modelo.

**Lo que los intervalos NO incluyen.** Son de Bayes empírico: la posterior de `v_s` dados
los hiperparámetros estimados. No propagan la incertidumbre de `alpha`, `gamma`, `sigma_v` y
`phi`, así que son algo estrechos. Con `sigma_v` estimada entre 0.33 y 0.49 el efecto es
menor, pero existe: una estación cuyo intervalo roza 1 no debe leerse como distinguible.

## b. Por qué se excluye abril–junio de 2020, y qué pasa si no

Se excluye porque es **otro régimen** (C3, EDA 3): con el confinamiento la tasa del estrato
cae a 0.35 denuncias por millón de entradas contra 0.61 del resto, con el 28 % de la
afluencia. El modelo supone exposición lineal —que el doble de entradas trae el doble de
denuncias esperadas—, y ese supuesto se sostiene en operación normal pero no con los vagones
vacíos: en un delito que vive de la aglomeración, la tasa por pasajero depende de cuánta
gente hay. Incluir esos meses metería al denominador de 2020 exposición que no «cuenta»
igual. Son 26 denuncias y 74 M de entradas.

**Robustez, incluyéndolos:** `sigma_v` = 0.393 (contra 0.402); `exp(gamma_2020)` baja de 0.96
a 0.92, que es donde tenía que notarse; **Spearman del orden con y sin: 0.9985**; la estación
que más se mueve cambia 8 lugares. La decisión no afecta el resultado (M7).

R1 (enero–agosto de 2019) **no** se excluyó, como quedó fijado de antemano: es un cambio de
nivel común que `gamma_2019` absorbe. Limitación: si ese quiebre pegó distinto entre
estaciones, el modelo no lo ve, y 2019 aporta el 38 % de las denuncias del estrato (R1 solo, el 29 %).

## c. El orden encogido contra el crudo

| Comparación | Spearman |
|---|---|
| Tasa encogida – tasa cruda | **0.985** |
| Tasa encogida – razón observadas ÷ esperadas | 0.990 |
| Tasa encogida – conteo | 0.461 |

**El encogimiento casi no cambia el orden, y eso es un resultado.** Nueve de las diez
primeras son las mismas: sale Tlaltenco (5 denuncias; del lugar 8 al 28) y entra Etiopía.
**Lo que cambia son los valores, no los lugares:** Bosque de Aragón pasa de una tasa cruda de
2.08 a una encogida de 1.40; Obrera, de 0.04 a 0.28. El factor de encogimiento (1 = no
encoge) tiene mediana de 0.60 con menos de 15 denuncias, 0.77 con 15 a 39, y 0.83 con 40 o
más.

Las que más se mueven, todas por poca evidencia: Talismán (3 denuncias) sube 20 lugares
hacia el centro, Tlaltenco (5) baja 20, Bondojito (4) sube 18, Velódromo (20) sube 17,
Tezozómoc (3) sube 15.

**Por qué se rechaza M3.** La hipótesis era que el encogimiento bastaría para sacar de la
cabeza a las estaciones con poca evidencia. No basta: **Hangares, con 12 denuncias, sigue en
el lugar 10.** Con `sigma_v` = 0.40 y 12 denuncias donde se esperaban 5.8, la posterior se
queda a medio camino (razón 1.59) y eso alcanza para el décimo lugar —aunque su intervalo,
0.90 a 2.52, incluye 1—. **Consecuencia práctica:** la regla de la app de no recomendar con
menos de 15 denuncias **no es redundante con el modelo**; hay que ordenar por la tasa
encogida *y* mirar el intervalo. El orden solo, aun encogido, no protege de la poca
evidencia.

## d. Validación fuera de muestra: ajustar con 2019–2023, predecir 2024

Entrenamiento: 2,578 denuncias. Prueba: **118 estaciones abiertas en 2024, 341 robos
denunciados** —mediana de **2 por estación**, 20 estaciones con cero—. El orden observado de
2024 es, en buena parte, ruido: ese es el contexto de todo lo que sigue.

| Orden de 2019–2023 usado para predecir | Spearman contra la tasa de denuncias de 2024 |
|---|---|
| **Tasa predicha por el modelo** | **0.303** (bootstrap sobre estaciones, IC 95 %: 0.117 a 0.464) |
| Tasa cruda | 0.261 |
| Conteo | 0.289 |
| *Techo por ruido* | *0.376 (0.219 a 0.527)* |

- **El techo.** Si la tasa predicha fuera la verdad exacta, el Spearman contra un 2024
  simulado con ruido de Poisson sería de 0.376 en promedio. **El 0.303 observado está dentro
  de ese rango: el modelo predice casi todo lo que se puede predecir de un año con 341
  denuncias.** Un Spearman bajo aquí no es un modelo malo; es un año chico.
- **Modelo contra tasa cruda:** diferencia de +0.042, con intervalo bootstrap de **+0.008 a
  +0.079**. El encogimiento mejora la predicción de forma consistente, aunque poco.
- **Modelo contra conteo:** diferencia de +0.014, intervalo de **−0.170 a +0.192**. **No se
  distinguen.** M5 «se sostiene» por la letra del criterio (0.303 > 0.30 y mayor que los
  otros dos), pero **por tres milésimas** y sin poder decir que el modelo ordene la tasa de
  2024 mejor que el simple conteo. Dicho sin adorno: fuera de muestra, la ventaja del modelo
  sobre el conteo no está demostrada como *predicción del orden*; lo que sí está demostrado
  es lo de abajo.

**La métrica de decisión: ¿qué cubre cada regla en 2024?**

| Regla para elegir 10 estaciones | Robos denunciados de 2024 cubiertos | % del estrato | Entradas de 2024 (M) | % de las entradas | **Denuncias por millón de entradas** |
|---|---|---|---|---|---|
| **Tasa predicha (modelo)** | **41** | 12.0 | 53.1 | 7.1 | **0.77** |
| Tasa cruda 2019–2023 | 28 | 8.2 | 40.3 | 5.4 | 0.69 |
| Conteo 2019–2023 | **92** | 27.0 | 160.1 | 21.4 | 0.57 |
| *Oráculo: conteo real de 2024* | *100* | *29.3* | *146.1* | *19.6* | *0.68* |
| Estrato completo | 341 | 100 | 747.2 | 100 | 0.46 |

Con 20 estaciones: modelo 73 denuncias (0.61 por millón), tasa cruda 72 (0.63), conteo 135
(0.58), oráculo 163 (0.72).

**Lectura, en las dos direcciones:**

- **Si lo que se quiere es cubrir denuncias, el conteo gana, y por mucho: 92 contra 41.**
  Esto estaba anunciado antes de correr y hay que decirlo igual de claro: las diez primeras
  por conteo son estaciones grandes (Indios Verdes, Constitución de 1917, Tasqueña,
  Buenavista…) y concentran el 27 % de las denuncias del estrato. El conteo de 2019–2023
  cubre casi lo mismo que el oráculo (92 contra 100): **para cubrir volumen, el conteo es una
  regla excelente y el modelo no la mejora.**
- **Si lo que se quiere es poner los elementos donde un pasajero tiene más probabilidad de
  acabar en una denuncia, el modelo gana: 0.77 contra 0.57 por millón de entradas**, un 35 %
  más, con un tercio de la afluencia que vigilar (53 M de entradas contra 160 M). Y supera a
  la tasa cruda en las dos métricas (41 contra 28 denuncias; 0.77 contra 0.69): ahí es donde
  el encogimiento paga, porque la tasa cruda elige estaciones chicas con suerte.
- **Las dos reglas responden preguntas distintas**, y la decisión de cuál usar es de quien
  despliega: volumen de denuncias o riesgo por usuario. Lo que el trabajo aporta es que hoy
  solo existe la primera lista, y que la segunda es estable fuera de muestra. Con 20
  estaciones la ventaja por millón de entradas casi desaparece (0.61 contra 0.58): la señal
  está en la cabeza.

Top-10 por tasa predicha: Bosque de Aragón, Camarones, Ciudad Deportiva, Constituyentes,
Hangares, Merced, Nativitas, Portales, Villa de Aragón, Zócalo/Tenochtitlan. Top-10 por
conteo: Buenavista, Constitución de 1917, Etiopía, Indios Verdes, Merced, Polanco, Portales,
Revolución, Tasqueña, Zócalo/Tenochtitlan. Comparten tres: Merced, Portales y Zócalo.

## e. La multiplicidad

**El problema.** En la fase 3 se hicieron 124 pruebas una por una al 95 %: salieron 42
estaciones «distinguibles» con la tasa cruda y 39 al descontar el año, cuando por puro azar
se esperarían unas 6. La señal era real, pero no se podía defender estación por estación.

**Por qué el encogimiento jerárquico es la respuesta correcta, y no una corrección tipo
Bonferroni.** Una corrección por comparaciones múltiples ensancha todos los intervalos por
igual, sin mirar los datos: protege del falso positivo a costa de quedarse sin potencia, y
trata igual a Merced (90 denuncias) que a Hangares (12). El modelo jerárquico hace otra cosa:
**estima de los propios datos cuánto varían de verdad las estaciones** (`sigma_v` = 0.40) y
usa esa distribución como punto de partida para cada una. Una estación con pocas denuncias y
una tasa extrema es, con mucha probabilidad, una estación corriente con suerte —porque
estaciones corrientes hay muchas y extremas pocas—, y su estimación se jala al centro; una
con muchas denuncias casi no se mueve. El problema de la multiplicidad es justo que entre
124 estaciones algunas salen extremas por azar, y el encogimiento corrige *ese* error en
proporción a la evidencia de cada una, en vez de castigar a todas. No hace falta corregir
después: los intervalos ya son de la tasa encogida (Gelman, Hill y Yajima, 2012, es el
argumento estándar; **no se abrió el artículo en esta sesión**: citar después de leerlo).

**Cuántas sobreviven.**

| | Pruebas una por una (fase 3) | **Modelo** |
|---|---|---|
| Distinguibles | 39 | **25** (14 arriba, 11 abajo) |
| De las 19 que el EDA encontró robustas | 19 | **19: las conserva todas** |
| De las 20 firmes pero no robustas | 20 | **6** |
| Nuevas que el descriptivo no había visto | — | **0** |

El modelo y el EDA llegan por caminos distintos casi a la misma lista: las 19 que aguantaban
quitar cualquier año y los tres umbrales de distancia están todas entre las 25 del modelo,
y de las 20 frágiles el modelo descarta 14. **Las 25:** por arriba, Bosque de Aragón, Ciudad
Deportiva, Villa de Aragón, Portales, Nativitas, Merced, Zócalo/Tenochtitlan, Etiopía,
Camarones, Moctezuma, Insurgentes, Revolución, Niños Héroes y Polanco; por abajo, Obrera, Autobuses del Norte, Politécnico, Universidad, Aculco,
Observatorio, Santa Marta, Ferrería, Escuadrón 201, Tláhuac y Chapultepec. **Tasqueña,
Indios Verdes y Constitución de 1917 no quedan como distinguibles por abajo** (razones
encogidas de 0.83, 1.01 y 0.88, con intervalos que incluyen 1; lugares 93, 67 y 82 de 124): son
terminales con tasa en la media del estrato o apenas por debajo. Lo que sigue siendo cierto de ellas es
lo de C1 y T5: están primeras por conteo y en media tabla por tasa.

Salvedad: «distinguible» es respecto de la estación *típica* (`exp(v_s)` = 1, la mediana),
no de la tasa conjunta del estrato, que pesa más a las estaciones grandes; y los intervalos
son de Bayes empírico. 25 es un número más honesto que 39, no un número exacto.

## La tabla final

`datos/procesados/modelo_estaciones.csv`, 124 filas ordenadas por tasa encogida, con:
`posicion_encogida`, `estacion`, `lineas`, `robos_denunciados`, `entradas`,
`tasa_denuncias_mm` (cruda), `tasa_encogida_mm` con `tasa_ic95_inf` y `tasa_ic95_sup`,
`razon_observadas_esperadas`, `razon_encogida` con su intervalo, `prob_arriba_del_estrato`,
`distinguible_modelo`, `firme_fase3`, `robusta_eda`, las tres posiciones anteriores
(`posicion_conteo`, `posicion_tasa`, `posicion_razon`), `cambio_cruda_a_encogida`,
`factor_de_encogimiento`, `evidencia_insuficiente` (menos de 15 denuncias) y
`sensible_al_umbral_de_asignacion` (Hangares, Juárez, Villa de Cortés y Tasqueña).

Las 20 primeras (tasas en denuncias por millón de entradas; razón respecto de la estación típica):

| # | Estación | Robos denunciados | Tasa cruda | **Tasa encogida (IC 95 %)** | Razón encogida (IC 95 %) | ¿Distinguible? | Pos. conteo |
|---|---|---|---|---|---|---|---|
| 1 | Bosque de Aragón | 20 | 2.08 | **1.40** (0.85–2.10) | 2.21 (1.35–3.33) | arriba | 55 |
| 2 | Ciudad Deportiva | 21 | 1.95 | **1.33** (0.82–1.99) | 2.10 (1.30–3.15) | arriba | 51 |
| 3 | Villa de Aragón | 40 | 1.61 | **1.26** (0.87–1.75) | 1.99 (1.37–2.77) | arriba | 15 |
| 4 | Portales | 52 | 1.51 | **1.24** (0.88–1.68) | 1.95 (1.38–2.65) | arriba | 10 |
| 5 | Nativitas | 48 | 1.52 | **1.23** (0.86–1.68) | 1.95 (1.36–2.66) | arriba | 13 |
| 6 | Merced | 90 | 1.59 | **1.21** (0.89–1.59) | 1.91 (1.41–2.52) | arriba | 4 |
| 7 | Zócalo/Tenochtitlan | 108 | 1.29 | **1.08** (0.81–1.41) | 1.71 (1.28–2.22) | arriba | 2 |
| 8 | Ricardo Flores Magón | 15 | 1.30 | 1.02 (0.61–1.58) | 1.62 (0.96–2.50) | no | 77 |
| 9 | Etiopía/Plaza de la Transparencia | 53 | 1.20 | **1.00** (0.71–1.36) | 1.59 (1.13–2.15) | arriba | 9 |
| 10 | Hangares | 12 | 1.41 | 1.00 (0.57–1.59) | 1.59 (0.90–2.52) | no · <15 | 91 |
| 11 | Constituyentes | 16 | 1.17 | 1.00 (0.60–1.53) | 1.58 (0.95–2.42) | no | 74 |
| 12 | Camarones | 31 | 1.29 | **1.00** (0.66–1.42) | 1.58 (1.05–2.24) | arriba | 25 |
| 13 | Moctezuma | 32 | 1.23 | **0.98** (0.65–1.40) | 1.55 (1.03–2.20) | arriba | 22 |
| 14 | Insurgentes | 69 | 1.18 | **0.96** (0.69–1.29) | 1.52 (1.09–2.04) | arriba | 6 |
| 15 | Revolución | 52 | 1.14 | **0.94** (0.67–1.28) | 1.49 (1.06–2.02) | arriba | 10 |
| 16 | Parque de los Venados | 15 | 1.20 | 0.94 (0.55–1.46) | 1.49 (0.88–2.31) | no | 77 |
| 17 | Niños Héroes/Poder Judicial CDMX | 37 | 1.10 | **0.94** (0.64–1.31) | 1.49 (1.02–2.07) | arriba | 16 |
| 18 | Juárez | 30 | 1.10 | 0.94 (0.62–1.33) | 1.48 (0.99–2.10) | no | 26 |
| 19 | Agrícola Oriental | 21 | 1.02 | 0.91 (0.57–1.33) | 1.43 (0.91–2.11) | no | 51 |
| 20 | Hospital 20 de Noviembre | 17 | 1.28 | 0.90 (0.53–1.39) | 1.42 (0.84–2.20) | no | 67 |

Las últimas: Obrera 0.28 (0.15–0.46), Autobuses del Norte 0.30, Politécnico 0.31,
Universidad 0.32 (0.21–0.45), Aculco 0.35, Observatorio 0.35 (0.23–0.50), Santa Marta 0.37,
Ferrería 0.37, Zapotitlán 0.40, Lindavista 0.41, Escuadrón 201 0.41, Tláhuac 0.42,
Chapultepec 0.42 (0.28–0.61).

## Lo que el modelo NO arregla

- Son denuncias, no robos. Una tasa encogida alta puede ser más robo o más disposición a
  denunciar; el modelo no distingue.
- No toca las 28 correspondencias ni a Hidalgo y Guerrero: ahí la exposición no es
  identificable y ningún modelo sobre estos datos la identifica.
- No explica el quiebre de 2019: lo absorbe.
- No corrige las carpetas sin coordenadas: supone que faltan parejo entre estaciones.
- Los intervalos no propagan la incertidumbre de los hiperparámetros.
- El efecto de estación se supone constante en los seis años: una estación que cambió (una
  obra, un operativo) queda promediada.
- **Más información sobre cada estación no lo mejora** (añadido el 2026-10-20): con línea,
  entorno de delitos a 500 m, tamaño o una tendencia por estación como covariables, la
  predicción del año siguiente no mejora fuera de muestra con el criterio escrito antes de
  correrlo (decisiones 66 y 67; detalle en [`covariables.md`](covariables.md)). El límite
  está en el ruido del fenómeno medido con denuncias, no en lo que se sabe de la estación.

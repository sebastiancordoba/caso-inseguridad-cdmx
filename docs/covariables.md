# ¿Más información mejora la predicción? Covariables de estación y tendencia

*Protocolo prerregistrado en la decisión 66 (commit `ac09e27`, 2026-10-20, antes de correr
nada); resultado y lectura en la decisión 67. Código: `src/metro/10_covariables.py` (el
entorno) y `src/metro/11_modelo_covariables.py` (modelos, evaluación, bootstrap). Todas las
cifras de esta página salen de las tablas `covariables_*.csv` que escribe el segundo script;
corre en unos 100 segundos. Verificado el 2026-10-20.*

## La pregunta

La lista por tasa del modelo predice la tasa del año siguiente con ρ ≈ 0.3 (M5), y la
tercera lista de la decisión 65 hereda esa debilidad. Sebas preguntó si no se puede hacer
algo mejor. La hipótesis a probar: el cuello de botella es la **predicción**, no la regla
que combina conteo y tasa; si al modelo se le da más información sobre cada estación, la
tasa predicha debería acercarse más a la observada y el top-k por tasa cubrir más denuncias
por millón de entradas.

## Qué se probó

Siete modelos, todos la misma binomial negativa con efecto aleatorio de estación y efecto de
año de `08_modelo.py`, a la que se añaden covariables de estación (el efecto aleatorio encoge
entonces hacia lo que predicen las covariables, no hacia la media del estrato):

| Modelo | Qué añade | Parámetros (ajuste 2019–2023) |
|---|---|---|
| base | nada: el modelo de M5 y M6 | 7 |
| línea | un efecto fijo por línea (12 líneas entre las 124; referencia la línea 1) | 18 |
| entorno | carpetas de la FGJ de **cualquier delito** (menos el robo a bordo del Metro) con coordenadas a ≤ 500 m de la estación, promedio anual del entrenamiento, en log y estandarizado; y lo mismo solo con **robo a transeúnte en vía pública** | 9 |
| tamaño | log de las entradas anuales promedio del entrenamiento, estandarizado | 8 |
| todas las fijas | línea + entorno + tamaño | 21 |
| tendencia | una pendiente aleatoria por estación sobre el año centrado, b(s) ~ N(0, τ²); predice el año de prueba extrapolando un año | 8 |
| todas + tendencia | todo lo anterior | 22 |

Las covariables se calculan **solo con los años de entrenamiento**: lo que se sabría al armar
la lista. Quedaron fuera, con la razón en la decisión 66: transbordo (constante en las 124),
agencia del MP (solo Observatorio), afluencia por hora (no existe), mes (panel anual),
alcaldía (16 niveles) y los postes del C5 (son WiFi, no cámaras).

El entorno se mide con las 1,295,353 carpetas de 2019–2024 con coordenadas válidas (94.9 %
de las 1,365,100 que no son el propio delito). Por estación y en los seis años: mediana
2,118 carpetas de cualquier delito a 500 m (de 493 a 11,322; la mayor, San Juan de Letrán) y
121 de robo a transeúnte en vía pública (de 17 a 1,103). Tiene el mismo defecto que el
numerador: las carpetas sin coordenadas no se cuentan.

**Años de prueba rodantes**: 2022 (ajuste 2019–2021), 2023 (2019–2022) y 2024 (2019–2023),
siempre sin abril–junio de 2020. El base reproduce exactamente M5 (ρ = 0.303 en 2024) y las
coberturas de 2024 de la decisión 65 (41 · 92 · 59 denuncias en k = 10; 73 · 135 · 99 en
k = 20); el script lo comprueba con `assert`.

## Métrica primaria: denuncias por millón cubiertas por el top-k por tasa predicha

| modelo | 2022, k=10 | 2022, k=20 | 2023, k=10 | 2023, k=20 | 2024, k=10 | 2024, k=20 |
|---|---|---|---|---|---|---|
| base | 1.220 | 1.017 | 0.634 | 0.597 | 0.773 | 0.610 |
| línea | 0.988 | 0.993 | 0.561 | 0.625 | 0.799 | 0.607 |
| entorno | 1.150 | 1.011 | 0.557 | 0.568 | 0.773 | 0.658 |
| tamaño | 1.107 | 1.006 | 0.674 | 0.586 | 0.731 | 0.627 |
| todas las fijas | 0.995 | 0.956 | 0.665 | 0.590 | 0.731 | 0.619 |
| tendencia | 1.080 | 1.027 | 0.630 | 0.617 | 0.560 | 0.636 |
| todas + tendencia | 1.055 | 0.900 | 0.632 | 0.618 | 0.466 | 0.599 |

Las denuncias cubiertas por esas mismas listas:

| modelo | 2022, k=10 | 2022, k=20 | 2023, k=10 | 2023, k=20 | 2024, k=10 | 2024, k=20 |
|---|---|---|---|---|---|---|
| base | 56.000 | 101.000 | 30.000 | 60.000 | 41.000 | 73.000 |
| línea | 50.000 | 102.000 | 31.000 | 63.000 | 43.000 | 78.000 |
| entorno | 59.000 | 104.000 | 29.000 | 55.000 | 41.000 | 81.000 |
| tamaño | 37.000 | 89.000 | 31.000 | 55.000 | 28.000 | 73.000 |
| todas las fijas | 39.000 | 84.000 | 34.000 | 53.000 | 30.000 | 73.000 |
| tendencia | 42.000 | 99.000 | 39.000 | 70.000 | 48.000 | 88.000 |
| todas + tendencia | 33.000 | 79.000 | 36.000 | 66.000 | 35.000 | 78.000 |

Ningún modelo le gana al base de forma consistente: en casi cada columna hay alguno que lo
supera por poco, pero es uno distinto cada vez (la tendencia en 2022 con k = 20, el tamaño en
2023 con k = 10, la línea en 2023 con k = 20 y en 2024 con k = 10, el entorno en 2024 con
k = 20), y cada uno de ellos pierde en los demás casos. Es el mismo patrón que la decisión
65 vio entre reglas: la mejor cambia de año y de k. La tendencia
extrapolada hace daño en 2024 (0.560 contra 0.773 en k = 10): las pendientes ajustadas con
cuatro o cinco puntos por estación no se sostienen un año más.

## ρ de Spearman, tasa predicha contra tasa observada

| modelo | ρ 2022 | ρ 2023 | ρ 2024 |
|---|---|---|---|
| base | 0.354 | 0.189 | 0.303 |
| línea | 0.354 | 0.218 | 0.304 |
| entorno | 0.357 | 0.198 | 0.324 |
| tamaño | 0.255 | 0.173 | 0.294 |
| todas las fijas | 0.296 | 0.233 | 0.284 |
| tendencia | 0.301 | 0.154 | 0.363 |
| todas + tendencia | 0.226 | 0.181 | 0.352 |

El techo por ruido calculado en M5 —si la tasa predicha fuera la verdad exacta, ρ contra un
2024 simulado— es 0.376. El base está en 0.303; el mejor modelo (entorno) llega a
0.324. Todo el espacio que hay para ganar está dentro del ruido de un año.

## Métrica secundaria: log-verosimilitud multinomial (diferencia contra el base)

Qué tan bien predice cada modelo cómo se reparten las denuncias del año de prueba entre las
estaciones, con p(s) ∝ tasa(s) · E(s). Positivo es mejor que el base.

| modelo | Δ log-ver. 2022 | Δ log-ver. 2023 | Δ log-ver. 2024 |
|---|---|---|---|
| base | +0.00 | +0.00 | +0.00 |
| línea | -3.74 | -0.64 | -1.79 |
| entorno | -0.03 | +0.53 | +1.29 |
| tamaño | -4.52 | -1.08 | -0.56 |
| todas las fijas | -11.17 | -1.58 | -1.57 |
| tendencia | +4.10 | -7.95 | -5.18 |
| todas + tendencia | -6.90 | -6.90 | -4.21 |

Solo el entorno mejora, y por poco (+0.5 y +1.3 unidades de log-verosimilitud en 2023 y
2024, −0.03 en 2022). Los modelos grandes empeoran: sobreajustan.

## Bootstrap pareado sobre estaciones (2,000 remuestras, semilla 20261020)

Las mismas remuestras para el base y para cada modelo; las predicciones quedan fijas y se
remuestrean las estaciones del año de prueba, como en M5.

| modelo | anio_prueba | k | dif_por_millon_media | ic95_inf | ic95_sup | p_mejor_que_base | dif_rho_media | p_rho_mejor |
|---|---|---|---|---|---|---|---|---|
| línea | 2022 | 10 | -0.060 | -0.157 | 0.021 | 0.089 | 0.000 | 0.498 |
| línea | 2022 | 20 | -0.021 | -0.089 | 0.068 | 0.231 | 0.000 | 0.498 |
| línea | 2023 | 10 | -0.011 | -0.090 | 0.070 | 0.356 | 0.030 | 0.855 |
| línea | 2023 | 20 | -0.015 | -0.075 | 0.029 | 0.254 | 0.030 | 0.855 |
| línea | 2024 | 10 | -0.014 | -0.088 | 0.052 | 0.295 | 0.000 | 0.507 |
| línea | 2024 | 20 | -0.013 | -0.081 | 0.044 | 0.385 | 0.000 | 0.507 |
| entorno | 2022 | 10 | -0.010 | -0.082 | 0.087 | 0.228 | 0.004 | 0.633 |
| entorno | 2022 | 20 | -0.006 | -0.043 | 0.014 | 0.170 | 0.004 | 0.633 |
| entorno | 2023 | 10 | -0.000 | -0.061 | 0.072 | 0.246 | 0.009 | 0.863 |
| entorno | 2023 | 20 | -0.005 | -0.034 | 0.012 | 0.290 | 0.009 | 0.863 |
| entorno | 2024 | 10 | 0.015 | -0.028 | 0.094 | 0.450 | 0.020 | 0.958 |
| entorno | 2024 | 20 | 0.021 | -0.045 | 0.100 | 0.620 | 0.020 | 0.958 |
| tamaño | 2022 | 10 | -0.047 | -0.240 | 0.094 | 0.340 | -0.097 | 0.000 |
| tamaño | 2022 | 20 | -0.032 | -0.103 | 0.024 | 0.157 | -0.097 | 0.000 |
| tamaño | 2023 | 10 | -0.005 | -0.085 | 0.073 | 0.253 | -0.015 | 0.214 |
| tamaño | 2023 | 20 | -0.007 | -0.088 | 0.028 | 0.425 | -0.015 | 0.214 |
| tamaño | 2024 | 10 | -0.003 | -0.080 | 0.059 | 0.340 | -0.010 | 0.271 |
| tamaño | 2024 | 20 | 0.003 | -0.079 | 0.044 | 0.643 | -0.010 | 0.271 |
| todas las fijas | 2022 | 10 | -0.092 | -0.266 | 0.067 | 0.136 | -0.057 | 0.084 |
| todas las fijas | 2022 | 20 | -0.039 | -0.143 | 0.055 | 0.238 | -0.057 | 0.084 |
| todas las fijas | 2023 | 10 | 0.011 | -0.081 | 0.101 | 0.629 | 0.046 | 0.878 |
| todas las fijas | 2023 | 20 | -0.060 | -0.134 | 0.026 | 0.097 | 0.046 | 0.878 |
| todas las fijas | 2024 | 10 | -0.051 | -0.171 | 0.075 | 0.163 | -0.020 | 0.311 |
| todas las fijas | 2024 | 20 | -0.006 | -0.094 | 0.065 | 0.501 | -0.020 | 0.311 |
| tendencia | 2022 | 10 | -0.039 | -0.260 | 0.171 | 0.368 | -0.052 | 0.177 |
| tendencia | 2022 | 20 | 0.012 | -0.086 | 0.102 | 0.622 | -0.052 | 0.177 |
| tendencia | 2023 | 10 | 0.001 | -0.139 | 0.128 | 0.507 | -0.037 | 0.292 |
| tendencia | 2023 | 20 | -0.028 | -0.136 | 0.075 | 0.308 | -0.037 | 0.292 |
| tendencia | 2024 | 10 | -0.040 | -0.224 | 0.181 | 0.339 | 0.061 | 0.898 |
| tendencia | 2024 | 20 | -0.005 | -0.102 | 0.106 | 0.432 | 0.061 | 0.898 |
| todas + tendencia | 2022 | 10 | -0.094 | -0.354 | 0.139 | 0.219 | -0.126 | 0.042 |
| todas + tendencia | 2022 | 20 | -0.097 | -0.238 | 0.027 | 0.071 | -0.126 | 0.042 |
| todas + tendencia | 2023 | 10 | 0.009 | -0.120 | 0.134 | 0.571 | -0.009 | 0.458 |
| todas + tendencia | 2023 | 20 | -0.058 | -0.156 | 0.045 | 0.146 | -0.009 | 0.458 |
| todas + tendencia | 2024 | 10 | -0.091 | -0.300 | 0.150 | 0.233 | 0.049 | 0.824 |
| todas + tendencia | 2024 | 20 | -0.015 | -0.112 | 0.096 | 0.377 | 0.049 | 0.824 |

## Veredicto, con el criterio de la decisión 66

Mejora = (a) mayor por millón en ≥ 4 de los 6 casos y mediana de las diferencias > 0, **y**
(b) mayor ρ en ≥ 2 de 3 años, **y** (c) P(Δρ promedio > 0) ≥ 0.90 en el bootstrap.

| modelo | parám. | (a) casos mejor, de 6 | (a) mediana Δ por millón | (a) | (b) años con ρ mejor, de 3 | (b) Δρ medio | (b) | (c) P(Δρ̄ > 0) | (c) | mejora |
|---|---|---|---|---|---|---|---|---|---|---|
| línea | 18 | 2 | -0.013 | False | 3 | 0.010 | True | 0.702 | False | False |
| entorno | 9 | 1 | -0.018 | False | 3 | 0.011 | True | 0.976 | True | False |
| tamaño | 8 | 2 | -0.011 | False | 0 | -0.041 | False | 0.001 | False | False |
| todas las fijas | 21 | 2 | -0.025 | False | 1 | -0.011 | False | 0.327 | False | False |
| tendencia | 8 | 3 | 0.003 | False | 1 | -0.009 | False | 0.394 | False | False |
| todas + tendencia | 22 | 1 | -0.064 | False | 1 | -0.029 | False | 0.224 | False | False |

**Ningún modelo cumple.** El entorno cumple (b) y (c) —mejora ρ en los tres años, en
promedio +0.011, y la mejora promedio es positiva en el 97.6 % de las remuestras— pero
falla la métrica que importa para la decisión: su top-k cubre menos denuncias por millón
que el base en cuatro de los seis casos, empata en uno (2024, k = 10) y gana en uno (2024,
k = 20). Una ganancia de una centésima de ρ no se traduce en una
lista mejor.

## Lo que sí explican las covariables (ajuste completo 2019–2024)

| modelo | parametros | loglik | AIC | LR_vs_base | gl | p_LR | sigma_v | tau | phi |
|---|---|---|---|---|---|---|---|---|---|
| base | 8 | -1482.17 | 2980.33 | 0.00 | 0 | — | 0.402 | — | 16.46 |
| línea | 19 | -1469.31 | 2976.62 | 25.71 | 11 | 0.01 | 0.346 | — | 16.37 |
| entorno | 10 | -1479.28 | 2978.56 | 5.77 | 2 | 0.06 | 0.385 | — | 16.39 |
| tamaño | 9 | -1479.18 | 2976.36 | 5.97 | 1 | 0.01 | 0.386 | — | 16.76 |
| todas las fijas | 22 | -1455.11 | 2954.23 | 54.10 | 14 | 0.00 | 0.282 | — | 17.02 |
| tendencia | 9 | -1477.97 | 2973.93 | 8.40 | 1 | 0.00 | 0.409 | 0.093 | 39.68 |
| todas + tendencia | 23 | -1451.16 | 2948.33 | 62.00 | 15 | 0.00 | 0.292 | 0.091 | 39.95 |

Las covariables fijas **sí** explican diferencias entre estaciones: con todas, σ_v baja de
0.402 a 0.282, el 51 % de la varianza entre estaciones en
escala log, con LR = 54.1 en 14 grados de libertad y el AIC 26 puntos más bajo.
Coeficientes del modelo con todas las fijas (log de la razón de tasas por desviación
estándar de la covariable, o contra la línea 1):

| coeficiente | beta | ee | exp_beta |
|---|---|---|---|
| línea_12 | -0.173 | 0.158 | 0.841 |
| línea_2 | 0.121 | 0.134 | 1.129 |
| línea_3 | 0.065 | 0.143 | 1.067 |
| línea_4 | -0.433 | 0.269 | 0.649 |
| línea_5 | -0.475 | 0.201 | 0.622 |
| línea_6 | -0.597 | 0.214 | 0.550 |
| línea_7 | 0.043 | 0.158 | 1.044 |
| línea_8 | -0.385 | 0.151 | 0.680 |
| línea_9 | 0.021 | 0.175 | 1.021 |
| línea_A | -0.177 | 0.181 | 0.838 |
| línea_B | 0.264 | 0.168 | 1.302 |
| entorno_todos | 0.022 | 0.061 | 1.022 |
| entorno_transeunte | 0.113 | 0.066 | 1.119 |
| tamaño | -0.225 | 0.043 | 0.798 |

Lo que dicen: a igual entradas, más robo a transeúnte alrededor va con más denuncias a bordo
(+12 % por desviación estándar, al borde de la significancia), las estaciones grandes tienen
**menos** denuncias por entrada (−20 % por desviación estándar del log de entradas), y las
líneas 5, 6 y 8 quedan por debajo de la 1 (la 4 y la B se mueven en el mismo sentido, por
debajo y por encima, sin alcanzar la significancia). Nada de eso es
sorprendente, y nada de eso ayuda a predecir el año siguiente.

## Por qué no ayuda, y qué significa

El modelo base ya aprende el nivel de cada estación de su propia historia: con cuatro o cinco
años de datos por estación, la covariable solo aporta donde la estación tiene pocas
denuncias, y ahí la lista por tasa de todos modos no la elige. Lo que cambia de un año al
siguiente —lo que ningún modelo de estos captura, con ρ ≈ 0.3 contra un techo de 0.38— es
ruido de conteos pequeños (la mediana de denuncias por estación y año es 3, con
cuartiles 1 y 5, en las 715 celdas) y cambios de un año que ninguna covariable fija
anticipa. La tendencia, que es la
única covariable que mira el tiempo, sobreajusta: con tan pocos puntos la pendiente absorbe
la sobredispersión (φ se dispara de 16 a varios cientos o miles en los ajustes cortos) y
extrapolar la empeora.

**Hallazgo**: con más información sobre cada estación, la señal de un año al siguiente sigue
igual de débil. El cuello de botella no es la información sobre las estaciones sino el ruido
del propio fenómeno medido con denuncias. Eso refuerza, no debilita, la conclusión del caso:
una lista para el año que viene debe armarse con la evidencia acumulada y con intervalos a
la vista, y la regla que combina conteo y tasa sigue siendo la combinada de la decisión 65.

## Las tres listas, de nuevo, con el modelo base (no hay ganador)

Como no hubo modelo ganador, las tres listas no cambian. Este cuadro añade 2022 como tercer
año de prueba, que la decisión 65 no tenía:

| anio_prueba | k | conteo_denuncias | conteo_por_millon | tasa_denuncias | tasa_por_millon | combinada_denuncias | combinada_por_millon |
|---|---|---|---|---|---|---|---|
| 2022.000 | 10.000 | 134.000 | 0.999 | 56.000 | 1.220 | 70.000 | 0.996 |
| 2022.000 | 20.000 | 192.000 | 0.909 | 101.000 | 1.017 | 126.000 | 1.011 |
| 2023.000 | 10.000 | 84.000 | 0.553 | 30.000 | 0.634 | 44.000 | 0.666 |
| 2023.000 | 20.000 | 125.000 | 0.584 | 60.000 | 0.597 | 78.000 | 0.623 |
| 2024.000 | 10.000 | 92.000 | 0.574 | 41.000 | 0.773 | 59.000 | 0.747 |
| 2024.000 | 20.000 | 135.000 | 0.579 | 73.000 | 0.610 | 99.000 | 0.680 |

Lo que agrega 2022, y hay que decir: con solo tres años de entrenamiento, la combinada empata
con el conteo en k = 10 (0.996 contra 0.999 por millón, con 70 denuncias contra 134) y le gana
en k = 20 (1.011 contra 0.909). La afirmación de la decisión 65 —la combinada supera al conteo
en denuncias por millón en los cuatro casos de 2023 y 2024— sigue siendo cierta; en 2022, con
menos historia, la ventaja en k = 10 desaparece.

## Qué cambia en la entrega

- **Listas y app**: nada. La combinada sigue; `tres_listas*.csv` no se tocan.
- **Deck**: una lámina, «Más información no mejora la predicción», con la tabla antes/después
  de la métrica primaria y el ρ, dentro del bloque de límites (especificación en
  `flujo-propuesto-2026-10-15.md`).
- **Escrito**: un párrafo en la conclusión y esta página como anexo del método; la decisión
  66 (protocolo) y la 67 (resultado) van en la sección de supuestos y decisiones.

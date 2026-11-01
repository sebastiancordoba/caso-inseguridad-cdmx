# Registro de hipótesis

*Escrito el 2026-09-20. Tiene dos partes con estatus distinto.*

*La **parte A** es una reconstrucción: recoge las hipótesis que YA se probaron en las fases
2, 2b y 3, tal como quedaron escritas en `decisiones.md` y en los documentos de fase. No
se reformulan para que suenen mejor; donde una estuvo mal planteada, se dice.*

*La **parte B** son las hipótesis que el modelo va a probar. Se escribieron después del EDA
(`eda.md`) y **antes de ajustar ningún modelo**, y entraron a git en un commit propio,
anterior al del modelo. Esas se congelan: no se les agrega ni se les quita nada después de
ver resultados.*

**Sobre las fechas de la parte A, con honestidad.** Todo el trabajo es del 2026-09-20. En
cada fase, el criterio de falla y el resultado entraron a git **en el mismo commit**, así
que git no prueba que el criterio se fijó antes: lo que lo afirma es el texto de
`decisiones.md` («fijado antes de correr») y el orden de la sesión de trabajo, que quedó en
el registro por sesión de `uso-ia.md` (versión de `135889b`; desde el 2026-10-31 ese archivo
resume el uso por tipo). Donde el criterio venía del encargo de Sebas, era anterior a cualquier
cómputo. Donde un criterio se fijó habiendo visto ya algo del resultado, está marcado. La
parte B sí tiene prueba en git.

El numerador de todo es DENUNCIAS (carpetas de la FGJ por fecha del hecho), no robos.

## Parte A — Lo que ya se probó

| # | Qué se afirmó | Criterio de falla | Cuándo se fijó | Resultado | Veredicto |
|---|---|---|---|---|---|
| **C1** | El orden de las estaciones por tasa de denuncias por millón de entradas difiere del orden por conteo: el conteo no basta | Falla si Spearman(conteo, tasa) ≥ 0.9 **y** nueve o más coincidencias en los top-10, sobre las 163 estaciones | 2026-09-20, en el encargo de la fase 2, antes de cualquier cómputo. Decisión 12; commit `56c4bf0` (17:55) | Spearman 0.693; 8 coincidencias. Igual solo en la CDMX (0.621; 8) y con 30 o más denuncias (0.684; 8) | **Se sostiene** (no falla), sin holgura en la cabeza: ocho de las diez primeras son las mismas |
| **C2** | La tasa por entradas es comparable entre estaciones con y sin correspondencia: el denominador no está contaminado por el transbordo | Falla si 7 o más de las 10 primeras por tasa son correspondencias, o 12 o más de las 20 primeras (por azar: 1.7 y 3.4) | 2026-09-20. El encargo decía «falla si las correspondencias copan la cabeza de la lista», sin número; el umbral lo puso la decisión 13, escrita antes de correr `03_pruebas.py`. Commit `56c4bf0` | 9 de las 10 y 17 de las 20. Tasa conjunta 2.10 contra 0.62 | ❌ **RECHAZADA.** Ver abajo |
| **T1** | Tener una agencia del Ministerio Público del Metro infla las denuncias de la estación: Observatorio (agencia, sin correspondencia) debe salir anómala | Hay anomalía si Observatorio queda arriba del percentil 90 de las estaciones sin correspondencia mientras operó su agencia (2019-01 a 2019-08) | 2026-09-20, decisión 19, antes de correr `04_agencias.py`. **Con advertencia escrita entonces:** en la exploración previa ya se había visto la tasa global de Observatorio (0.34). Commit `d17fa62` (18:15) | Percentil 14.6 con agencia (tasa 0.34, IC 0.12–0.74); 0.35 después de que la agencia cerró | ❌ **RECHAZADA** (parte del efecto agencia) |
| **T2** | Las estaciones con agencia tienen tasas de denuncias mayores que correspondencias comparables, **y ese exceso se debe a la agencia** | Anomalía si la tasa es al menos el doble de la mediana de sus controles. Se atribuye a la agencia solo si el exceso **no** persiste con el numerador restringido a Denuncia Digital (razón < 2) | 2026-09-20, decisiones 19 y 21, antes de correr. **Con advertencia:** el par Hidalgo–Bellas Artes lo traía el encargo. Commit `d17fa62` | Hidalgo 2.71× y Guerrero 3.02× sus controles; Pantitlán 0.82× y Observatorio 0.76×. En el canal digital el exceso persiste y crece: 3.53× y 3.48× | ❌ **RECHAZADA** la atribución. La anomalía de Hidalgo y Guerrero es real; la agencia no la explica |
| **T4** | Si la agencia inflara las denuncias, el exceso de las estaciones con agencia debería diluirse al crecer la Denuncia Digital | No se fijó umbral numérico: el encargo decía «es evidencia a favor del mecanismo si baja». Prueba de dirección | 2026-09-20, en el encargo de la fase 2b. Commit `d17fa62` | El exceso de Hidalgo y Guerrero sube de 2.62 (2019) a 4.67 (2024) mientras las agencias del Metro pasan de abrir el 57 % de las carpetas al 17 % | ❌ **RECHAZADA**: va en la dirección contraria |
| **T5** | En las 124 estaciones sin correspondencia de la CDMX, conteo y tasa ordenan distinto: hay recomendación que dar | Falla si Spearman ≥ 0.9 **y** nueve o más coincidencias en los top-10 | 2026-09-20, en el encargo de la compuerta («criterio de falla, fijado ahora»). Decisión 25; commit `313e66c` (18:52) | Spearman 0.454; 3 coincidencias. No falla en ninguna de nueve combinaciones de umbral de distancia (100, 150, 250 m) y mínimo de denuncias (0, 20, 30) | **Se sostiene**, con holgura |
| **C3** | La exposición es lineal en las entradas: cuando la afluencia se desplomó, la tasa de denuncias se mantuvo | **Como se fijó:** se sostiene si la tasa anual de 2020 y de 2021 queda dentro de ±25 % de la de 2019 | 2026-09-20, decisión 28, antes de correr. **Con advertencia escrita entonces:** la tabla T4 ya dejaba ver que la tasa anual cae después de 2019. Commit `313e66c` | 0.50× y 0.68× en la red; 0.55× y 0.67× en el estrato (a) | **Por el criterio fijado: no se sostiene. Pero el criterio estaba MAL PLANTEADO.** Ver abajo |

### Las dos rechazadas, que son el activo del trabajo

**❌ La comparabilidad de las correspondencias (C2).** Era la hipótesis implícita del
encuadre original: que bastaba dividir entre entradas para obtener un ranking de riesgo de
toda la red. Se rechazó con claridad, y el rechazo tiene tamaño: para que las 28
correspondencias bajaran a la tasa de las estaciones de paso harían falta 3,583 millones de
transbordos en seis años, 1.98 veces sus entradas (T7, aritmética; mediana por estación
1.4×). Un flujo así es verosímil, de modo que el defecto del denominador alcanza para
explicar el grueso de la diferencia. **Consecuencia:** el trabajo dejó de prometer un
ranking de toda la red y se acotó a donde el denominador es identificable. Sin este rechazo
la app publicaría una lista de correspondencias presentada como lista de riesgo.

**❌ El efecto agencia (T1, T2, T4).** Era la sospecha natural tras C2: que el ranking mide
dónde se puede denunciar. Se rechazó por cuatro vías independientes que salen de los
propios datos de la FGJ (la carpeta trae la agencia que la abrió): las carpetas de cada
agencia se reparten por toda la red (la de Hidalgo, en 97 estaciones; solo el 13.8 % cae en
Hidalgo); el único caso limpio, Observatorio, no muestra efecto ni con la agencia abierta
ni al cerrarla; el exceso de Hidalgo y Guerrero persiste en el canal digital; y crece cuando
las agencias pierden peso. **Consecuencia:** se eliminó el filtro de agencia (decisión 24),
y Hidalgo y Guerrero quedaron como hallazgo aparte, sin explicación.

### C3: mal planteada, con su corrección aparte

- **Lo que se fijó** (decisión 28, antes de correr): comparar la tasa anual de 2020 y 2021
  contra la de 2019. Con ese criterio la exposición lineal **no se sostiene**, y así se
  reportó en `fase3-t5.md`.
- **Por qué estaba mal planteada:** la base de comparación era mala. La gráfica mostró que
  las denuncias caen de unas 330 al mes a unas 135 entre enero y agosto de 2019, con la
  afluencia plana. 2019 no es un año base: contiene un quiebre propio, anterior a la
  pandemia, y compararlo entero contra 2020 mezcla las dos cosas.
- **La corrección** (decisión 30, 2026-09-20, **tomada después de ver la gráfica**; mismo
  commit `313e66c`; la figura se rehízo en `2d12f98`): contra la base de septiembre de 2019
  a febrero de 2020, con la afluencia a la mitad (julio de 2020 a diciembre de 2021) la tasa
  de la red es 1.06 × la base. La exposición lineal se sostiene en operación normal y falla
  solo en el confinamiento estricto (abril–junio de 2020: 0.55 ×).
- **Estatus honesto:** la lectura corregida es posterior a los datos. No es una hipótesis
  confirmada; es una descripción que el modelo de la parte B tiene que respetar (M7) y que
  deja tres regímenes: R1, enero–agosto de 2019; R2, abril–junio de 2020; R0, el resto. **El
  quiebre de 2019 sigue sin explicación.**

### Lo que NO fue hipótesis

T3 (la tabla 2 × 2), T6 (el tamaño del estrato) y T7 (la cota de transbordos) son
descripción y aritmética; no tenían criterio de falla y no se registran como pruebas. La
comprobación «descontando el año» de la fase 3 (decisión 29) se decidió después de ver C3;
es una prueba de robustez posterior a los datos, no una hipótesis previa.

---

## Parte B — Lo que el modelo va a probar. CONGELADO el 2026-09-20, antes de ajustar

Modelo: binomial negativa sobre el panel estación × año del estrato (a),
`y_st ~ NB(mu_st, phi)`, `log mu_st = log E_st + alpha + v_s + gamma_t`, con `E_st` entradas,
`v_s` efecto aleatorio de estación y `gamma_t` efecto de año. Cantidad de interés:
`exp(alpha + v_s)`, la tasa de denuncias por entrada, encogida.

Lo que el EDA sugiere y de dónde sale cada hipótesis está en `eda.md`. Varias pueden salir
«mal» para el modelo elegante; se reportan igual.

| # | Hipótesis | De qué hallazgo del EDA sale | Qué la rechazaría |
|---|---|---|---|
| **M1** | Con efecto de estación y de año ya en el modelo, **queda sobredispersión**: hace falta la binomial negativa y no basta la Poisson | EDA 2: entre años la varianza es 2.3 veces la media (mediana), pero entre meses, quitando R1 y R2, es 1.00. **La expectativa honesta es que esta hipótesis puede fallar** | Se rechaza si la prueba de razón de verosimilitudes NB contra Poisson (con la corrección de frontera: mitad del valor p de χ²₁) da p > 0.05, **o** si el AIC favorece a la Poisson. Si se rechaza, el orden final se reporta con la Poisson |
| **M2** | **La heterogeneidad entre estaciones es real**: la varianza del efecto de estación es mayor que cero | EDA 1 y 5: tasas crudas de 0.04 a 2.08; 19 estaciones firmes aun quitando cualquier año | Se rechaza si la razón de verosimilitudes contra `sigma_v = 0` (misma corrección de frontera) da p > 0.05 |
| **M3** | **El encogimiento no cambia el orden en lo grueso pero saca de la cabeza a las estaciones con poca evidencia**: Spearman(encogida, cruda) ≥ 0.9, y ninguna estación con menos de 15 denuncias queda en el top-10 encogido | EDA 1: 42 de 124 estaciones tienen menos de 15 denuncias, y fase 3: siete de las diez que más suben por tasa cruda son ruido | Se rechaza si Spearman < 0.9 (el encogimiento reordena más de lo previsto) **o** si alguna estación con menos de 15 denuncias queda en el top-10 encogido. Si el encogimiento no cambia nada, se dice: es un resultado |
| **M4** | **La multiplicidad importa**: el modelo deja menos de 39 estaciones con intervalo al 95 % de `exp(v_s)` fuera de 1, y conserva a la mayoría de las 19 que el EDA encontró robustas (firmes quitando cualquier año y con los tres umbrales de distancia) | Fase 3: 39 distinguibles contra ~6 esperadas por azar, sin corrección. EDA 5 y 6: solo 19 de las 39 son robustas | Se rechaza si el modelo deja 39 o más distinguibles (el encogimiento no hizo nada), **o** si conserva menos de 12 de las 19 robustas (el modelo y el descriptivo se contradicen) |
| **M5** | **El orden ajustado con 2019–2023 predice el orden de la tasa de 2024**, y lo predice mejor que la tasa cruda y mejor que el conteo | Es la verificación fuera de muestra; EDA 5 sugiere persistencia moderada (las razones anuales de una misma estación saltan mucho) | Se rechaza si Spearman(predicho, tasa observada en 2024) ≤ 0.30, **o** si es menor que el de la tasa cruda de 2019–2023 o que el del conteo de 2019–2023 contra esa misma tasa de 2024 |
| **M6** | **Desplegar en las diez primeras por tasa predicha cubre más denuncias de 2024 por millón de entradas que desplegar en las diez primeras por conteo.** Expectativa declarada de antemano: en denuncias ABSOLUTAS el conteo va a cubrir más, porque elige estaciones grandes; eso no es el criterio pero se reporta | EDA 1: las diez primeras por conteo concentran el 26.5 % de las denuncias del estrato | Se rechaza si las denuncias de 2024 por millón de entradas en el top-10 por tasa predicha no superan a las del top-10 por conteo |
| **M7** | **Excluir abril–junio de 2020 no cambia el orden**: Spearman ≥ 0.98 entre el orden con y sin esos meses | C3 y EDA 3: R2 es un régimen distinto, pero son 26 denuncias de 2,945 | Se rechaza si Spearman < 0.98 |

**Decisiones de especificación fijadas también ahora, para no elegirlas a conveniencia:**

- El modelo principal **excluye abril–junio de 2020** del numerador y del denominador de 2020
  (R2 es otro régimen: con los vagones vacíos la tasa cae a la mitad, y la exposición
  lineal ahí no vale). La versión que los incluye es robustez (M7).
- **R1 no se excluye.** Enero–agosto de 2019 tiene el 29 % de las denuncias del estrato; es
  un cambio de nivel común a la red, y el efecto de año `gamma_2019` lo absorbe. Se dice como
  limitación: si el quiebre de 2019 pegó distinto entre estaciones, el modelo no lo ve.
- Los efectos de año suman cero, de modo que `exp(alpha + v_s)` es la tasa de un año
  «promedio» (media geométrica). El orden no depende de esa elección.
- La unidad es estación × año, no estación × mes: a nivel mensual la mitad de las celdas son
  ceros y la sobredispersión que interesa (M1) es la que queda entre años.
- «Distinguible» = el intervalo al 95 % de `exp(v_s)` excluye 1.
- La validación fuera de muestra usa solo las estaciones abiertas en 2024.
- Si el modelo no converge, se entrega el EDA y el diagnóstico de sobredispersión y se para:
  el descriptivo ya sostiene el trabajo.

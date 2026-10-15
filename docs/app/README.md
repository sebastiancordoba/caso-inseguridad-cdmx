# La app

Página estática: `index.html`, `estilo.css`, `app.js`, `sw.js` y un solo archivo de datos,
`datos.json`. Sin backend, sin paso de compilación, sin framework y sin ninguna dependencia
externa: ni D3, ni teselas de mapa, ni tipografías de fuera. El mapa es un SVG que se
dibuja con las coordenadas de las estaciones y las polilíneas de las líneas. El día de la
demo no depende de que responda ningún servidor ajeno.

## Verla en tu máquina

```bash
cd docs/app
python3 -m http.server 8000      # y abre http://localhost:8000
```

Hace falta un servidor (aunque sea ese) porque el navegador no deja leer `datos.json` desde
`file://`.

## Rehacer los datos

```bash
python src/descarga.py --fuente estaciones   # una vez
python src/metro/correr.py                   # 01 a 06; el último escribe docs/app/datos.json
```

`datos.json` pesa unos 140 KB y se versiona: la página publicada no recalcula nada.

## Sin conexión

`sw.js` guarda los cinco archivos la primera vez que se abre la página; después abre y
recarga sin red. Probado el 2026-09-20: con el servidor apagado, la página recarga, dibuja
las 163 estaciones, el interruptor reordena y las fichas abren. **Al cambiar cualquier
archivo hay que subir `VERSION` en `sw.js`**, o los navegadores que ya la abrieron pueden
quedarse con la versión anterior cuando no tengan red.

**Ojo con la caché HTTP de GitHub Pages (`max-age=600`).** Encontrado el 2026-09-20 al
verificar una publicación: el servidor ya tenía el `app.js` nuevo y el navegador seguía
sirviendo el viejo desde su caché HTTP. Desde la versión 6, `sw.js` pide todo con
`cache: "no-cache"`, que revalida siempre contra el servidor. Aun así, **quien ya había
abierto la página puede tardar hasta diez minutos en recibir un `sw.js` nuevo**, porque ese
archivo también sale con `max-age=600`. Para la demo: publicar al menos diez minutos antes,
y abrirla una vez con red.

## Publicación

**Hoy (temporal):** <https://sebastiancordoba.github.io/metro-denuncias-cdmx/>, servida desde
un repositorio público aparte, `sebastiancordoba/metro-denuncias-cdmx` (rama `gh-pages`),
que es solo un espejo de esta carpeta. Existe porque este repo es privado y el plan de
GitHub no permite Pages en repos privados. Para volver a publicar después de un cambio:

```bash
bash src/metro/publica_espejo.sh     # antes, sube VERSION en docs/app/sw.js
```

En el espejo no se edita nada a mano: la fuente es siempre esta carpeta.

**Después (un solo repo con todo):** cuando este repo se abra, `.github/workflows/pages.yml`
publica **solo esta carpeta** al cambiar en `main`, y el espejo se borra. No se usa «Pages
sobre `docs/`» porque `docs/` trae material que no debe quedar público por accidente (el
texto del caso del ITAM, las notas de las reuniones). Pasos de ese día:

```bash
gh repo edit --visibility public
gh api -X POST repos/sebastiancordoba/caso-inseguridad-cdmx/pages -f build_type=workflow
gh workflow run "Publica la app"
gh repo delete sebastiancordoba/metro-denuncias-cdmx     # y actualizar la URL donde se cite
```

## Reglas de contenido que el código respeta

- El numerador son DENUNCIAS. Ningún eje, leyenda ni tooltip dice «robos» a secas.
- Ningún número puntual sin su intervalo (Poisson, aproximación de Byar, 95 %).
- Las estaciones con menos de 15 denuncias no se listan por defecto, van marcadas como
  «evidencia insuficiente» y nunca se resaltan como movimiento ni como «firmes».
- La fecha de corte va en el encabezado y en el plegable «¿Cómo se calcula?», no en el pie.
- Texto mínimo (pedido de Sebas, 2026-10-15): títulos cortos, una línea por bloque; lo explicativo va plegado en «¿Cómo se calcula?».

## Por año y por mes (2026-10-15, pedido de Sebas)

- **Selector de periodo** sobre la lista: «2019–2024» (por defecto) usa el modelo; un año suelto usa
  la serie anual que ya trae cada estación en `datos.json` (`serie`): conteo, o tasa **cruda** de
  ese año con intervalo de Byar. Lugares con empates compartidos. Los avisos de cambio y el mapa
  son siempre del periodo completo. Con 15 denuncias como mínimo, en un año casi nada alcanza
  (2019: 21 estaciones; 2020: 0; 2021: 2; 2022: 3; 2023: 1; 2024: 1).
- **Pestaña «En el tiempo»** (abre en «Estaciones», la de la demo): siete gráficas SVG a mano,
  interactivas (tooltip con valor e intervalo, leyenda que aísla, rango de fechas en la mensual).
  Datos en `datos.json` → `mensual`: `serie` (mes), `anual` (`c3_por_anio.csv` + Byar),
  `estacionalidad` (`eda_estacionalidad.csv`, régimen R0), `hora_dia` (`eda_hora_dia_estrato.csv`,
  conteos; filas lunes a domingo) y `spearman_conteo_tasa` (`t5_criterio.csv`, 150 m, sin mínimo).
- **Por mes** solo va la serie del estrato (a), `mensual.serie` en `datos.json`, que
  `06_app_datos.py` calcula del panel y compara contra `eda_serie_mensual_estrato.csv`. Por
  estación no se ordena: el 98 % de los 8,280 meses-estación tiene 0 a 2 denuncias (máximo 10).

## Dónde desplegar (decisión 65)

Pestaña con tres listas (conteo, tasa y la que proponemos), de `09_lista_propuesta.py`. Dos vistas que
**no se mezclan**: «Probadas en 2024» (`tres_listas_fuera_de_muestra.csv`: elegidas con 2019–2023, con
lo que cubrieron en 2024) y «Para desplegar hoy» (`tres_listas.csv`: 2019–2024, **sin** cifra de
cobertura, porque 2024 ya está dentro de la lista). `06_app_datos.py` compara las sumas contra
`tres_listas_cobertura_2024.csv` (10 y 20 estaciones) y la tercera fila del bloque «tres reglas».

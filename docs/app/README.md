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
- La fecha de corte va en el encabezado y en el panel «Qué mide esto», no en el pie.

# Robo denunciado por pasajero en el Metro de la CDMX: qué estaciones cambian de lugar al medir por millón de entradas

Caso 2 (inseguridad urbana en la Ciudad de México) de la titulación por caso de la
Licenciatura en Ciencia de Datos, ITAM. Autor: Sebastián Córdoba.

**La pregunta.** En las 124 estaciones de paso del Metro de la Ciudad de México, ¿cuáles
concentran más denuncias de robo a pasajero por millón de entradas —2019 a 2024, tasa
encogida— y cuánto cambia el orden frente al conteo?

Todo es sobre **denuncias** (carpetas de investigación de la Fiscalía), no sobre robos: la
mayoría de los delitos no se denuncia.

## Entregables

| Qué | Dónde |
|---|---|
| Escrito, formato IEEE | [`docs/escrito/escrito.pdf`](docs/escrito/escrito.pdf) (fuente: `escrito.tex` y `referencias.bib`) |
| Aplicación | [`docs/app/`](docs/app/): página estática, sin servidor ni dependencias. Publicada en <https://sebastiancordoba.github.io/metro-denuncias-cdmx/> |
| Presentación | [`docs/presentacion/`](docs/presentacion/): diapositivas en PDF y en PowerPoint, con el guion en las notas del orador |
| Código | [`src/`](src/) |

## Reconstruir todo desde cero

Python 3.13.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/descarga.py --fuente estaciones   # carpetas de la FGJ (534 MB), afluencia y estaciones del STC
python src/metro/correr.py                   # el pipeline completo; al final escribe docs/app/datos.json
bash docs/escrito/compila.sh                 # el escrito, con tectonic
```

`descarga.py` deja el hash de cada archivo en `datos/crudos/MANIFIESTO.md`. Los datos no se
versionan: se reconstruyen. `correr.py` corre los pasos en orden y cada uno trae sus
comprobaciones (`assert`); se detiene si una prueba manda parar.

Para ver la app en tu máquina:

```bash
cd docs/app && python3 -m http.server 8000   # y abrir http://localhost:8000
```

## Qué hay en cada lugar

| Archivo | Qué es |
|---|---|
| `datos/FUENTES.md` | Las fuentes: URL, qué trae cada una, sus defectos y cómo se verificó |
| `src/descarga.py` | Descarga reproducible, con manifiesto de hashes |
| `src/metro/01_*.py` a `11_*.py` | El pipeline: llave de estaciones, panel, pruebas de viabilidad, agencias, estrato de paso, EDA, modelo, tres listas, covariables y datos de la app |
| `docs/caso-2.md` | Resumen del caso entregado por el ITAM y su lectura |
| `docs/problema.md` | Pregunta, hipótesis, supuestos y objetivos |
| `docs/hipotesis.md` | Hipótesis con su criterio de rechazo; las del modelo, congeladas antes de ajustarlo |
| `docs/decisiones.md` | Cada decisión del método, con fecha, la alternativa descartada y por qué |
| `docs/fase*.md`, `eda.md`, `modelo.md`, `covariables.md` | Resultados de cada fase |
| `docs/revision-literatura.md`, `docs/fuentes-conteo.md` | Literatura y listas publicadas por la prensa |
| `docs/uso-ia.md` | Registro del uso de IA generativa |

## Historial

El historial de este repositorio se reescribió al hacerlo público, para quitar el texto del
caso (que es del ITAM) y archivos de trabajo que no son parte del método. Las fechas y el
orden de los commits se conservan. Detalle en la decisión 71 de `docs/decisiones.md`.

## Licencia

El código está bajo licencia MIT ([`LICENSE`](LICENSE)). Los datos son de sus fuentes
públicas (FGJ de la Ciudad de México, STC Metro, INEGI), con sus propias condiciones de uso.

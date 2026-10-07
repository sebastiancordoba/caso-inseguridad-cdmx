#!/usr/bin/env python3
"""Descarga las fuentes del caso y deja constancia de qué se bajó y cuándo.

Los datos no viven en git: viven aquí, reconstruibles. El manifiesto es lo que se
versiona, para que dentro de un mes se sepa exactamente sobre qué archivo se corrió el
análisis — y para que si el portal cambia el archivo por debajo, el hash lo delate en vez
de que el cambio pase en silencio.

Uso:
    python src/descarga.py --lista
    python src/descarga.py --fuente acotado      # todo lo del problema acotado
    python src/descarga.py --fuente fgj --fuente ensu
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import ssl
import sys
import time
import urllib.request
from pathlib import Path

import certifi

RAIZ = Path(__file__).resolve().parent.parent
CRUDOS = RAIZ / "datos" / "crudos"
MANIFIESTO = CRUDOS / "MANIFIESTO.md"

# URLs verificadas contra los portales el 2026-09-14 y comprobadas el 2026-09-17.
# Ver datos/FUENTES.md y docs/problema.md.
FUENTES: dict[str, list[tuple[str, str]]] = {
    # 1. Delito: Carpetas de investigación FGJ CDMX
    "fgj": [
        (
            "carpetasFGJ_acumulado_2025_01.csv",
            "https://archivo.datos.cdmx.gob.mx/FGJ/carpetas/carpetasFGJ_acumulado_2025_01.csv",
        ),
    ],
    # 2. Percepción: ENSU microdatos trimestrales (2019 a 2024), sus diccionarios de datos
    #    (descriptores FD, para confirmar que BP1_2_03 no cambia entre años) y el catálogo
    "ensu": [
        (
            "ensu_bd_2019_dbf.zip",
            "https://www.inegi.org.mx/contenidos/programas/ensu/microdatos/ensu_bd_2019_dbf.zip",
        ),
        (
            "ensu_bd_2020_dbf.zip",
            "https://www.inegi.org.mx/contenidos/programas/ensu/microdatos/ensu_bd_2020_dbf.zip",
        ),
        (
            "ensu_bd_2021_csv.zip",
            "https://www.inegi.org.mx/contenidos/programas/ensu/microdatos/ensu_bd_2021_csv.zip",
        ),
        (
            "ensu_bd_2022_csv.zip",
            "https://www.inegi.org.mx/contenidos/programas/ensu/microdatos/ensu_bd_2022_csv.zip",
        ),
        (
            "ensu_bd_2023_csv.zip",
            "https://www.inegi.org.mx/contenidos/programas/ensu/microdatos/ensu_bd_2023_csv.zip",
        ),
        (
            "ensu_bd_2024_csv.zip",
            "https://www.inegi.org.mx/contenidos/programas/ensu/microdatos/ensu_bd_2024_csv.zip",
        ),
        *[
            (
                f"ensu_fd_{anio}_pdf.zip",
                f"https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu_fd_{anio}_pdf.zip",
            )
            for anio in range(2019, 2025)
        ],
        (
            "ensu2024_catalogo_ciudades_interes.pdf",
            "https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu2024_catalogo_ciudades_interes.pdf",
        ),
    ],
    # 3. Denominadores: Población por alcaldía Censo 2020 (ITER CDMX)
    "censo": [
        (
            "iter_09_cpv2020_csv.zip",
            "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_09_cpv2020_csv.zip",
        ),
    ],
    # 4. Cartografía: Límites de alcaldías de la CDMX
    "geografia": [
        (
            "alcaldias_cdmx.geojson",
            "https://datos.cdmx.gob.mx/dataset/bae265a8-d1f6-4614-b399-4184bc93e027/resource/deb5c583-84e2-4e07-a706-1b3a0dbc99b0/download/deb5c583-84e2-4e07-a706-1b3a0dbc99b0.json",
        ),
    ],
    # 5. Documentación metodológica (D2): Notas técnicas oficiales de la FGJ
    "notas_fgj": [
        (
            "nota_fgj_reclasificacion_feb2020.pdf",
            "https://datos.cdmx.gob.mx/dataset/250f29c0-31c7-44dc-9d31-f7e6cc78b79e/resource/360e2aa0-77e0-463c-b20d-345ef1c1d95b/download/360e2aa0-77e0-463c-b20d-345ef1c1d95b.pdf",
        ),
        (
            "nota_fgj_actualizaciones_retroactivas_jul2020.pdf",
            "https://datos.cdmx.gob.mx/dataset/250f29c0-31c7-44dc-9d31-f7e6cc78b79e/resource/1128fb92-59af-452f-ae38-36b4d835d23e/download/1128fb92-59af-452f-ae38-36b4d835d23e.pdf",
        ),
        (
            "nota_fgj_diferencias_sesnsp_ene2020.pdf",
            "https://datos.cdmx.gob.mx/dataset/250f29c0-31c7-44dc-9d31-f7e6cc78b79e/resource/bcb29264-91fa-4cc6-8c7e-561d8eb771e9/download/bcb29264-91fa-4cc6-8c7e-561d8eb771e9.pdf",
        ),
    ],
    # 6. Desagregación por género y edad: Víctimas en carpetas de investigación FGJ
    "victimas": [
        (
            "victimasFGJ_acumulado_2024_09.csv",
            "https://archivo.datos.cdmx.gob.mx/FGJ/victimas/victimasFGJ_acumulado_2024_09.csv",
        ),
        (
            "nota_victimas_actualizacion_pgj.pdf",
            "https://datos.cdmx.gob.mx/dataset/7593b324-6010-44f7-8132-cb8b2276c842/resource/8ec51d06-b430-4722-a811-2cd396c4ba66/download/8ec51d06-b430-4722-a811-2cd396c4ba66.pdf",
        ),
    ],
    # 7. Infraestructura disuasiva: Postes y cámaras de videovigilancia C5
    "postes_c5": [
        (
            "postes_c5_cdmx.xlsx",
            "https://datos.cdmx.gob.mx/dataset/d5410ea3-dbdd-437d-9def-91f30ec9a390/resource/9bb1debb-15e9-4d48-baec-07c9edd87a23/download/9bb1debb-15e9-4d48-baec-07c9edd87a23.xlsx",
        ),
    ],
    # Fuentes complementarias / secundarias
    "c5": [
        (
            "c5_incidentes_viales_2022_2024.csv",
            "https://archivo.datos.cdmx.gob.mx/C5/incidentes_viales/inViales_2022_2024.csv",
        ),
        (
            "c5_incidentes_viales_2019_2021.csv",
            "https://archivo.datos.cdmx.gob.mx/C5/incidentes_viales/inViales_2019_2021.csv",
        ),
    ],
    "fgj_previo": [
        (
            "carpetasFGJ_previo_reclasificacion_jun2020.csv",
            "https://archivo.datos.cdmx.gob.mx/fiscalia-general-de-justicia/"
            "carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico/carpetas_ss_junio2020.csv",
        ),
    ],
    # Metro (docs/fase1-encuadres.md, encuadre 1): afluencia diaria por estación y línea,
    # su diccionario, y los puntos de las estaciones
    "metro": [
        (
            "afluencia_metro_simple.csv",
            "https://datos.cdmx.gob.mx/dataset/f2046fd5-51b5-4876-b008-bd65d95f9a02/resource/0e8ffe58-28bb-4dde-afcd-e5f5b4de4ccb/download/0e8ffe58-28bb-4dde-afcd-e5f5b4de4ccb.csv",
        ),
        (
            "afluencia_metro_simple_diccionario.csv",
            "https://datos.cdmx.gob.mx/dataset/f2046fd5-51b5-4876-b008-bd65d95f9a02/resource/7abf61db-a045-4b72-b5cd-c22ea0de6467/download/7abf61db-a045-4b72-b5cd-c22ea0de6467.csv",
        ),
        (
            "stc_metro_shp.zip",
            "https://datos.cdmx.gob.mx/dataset/1b014317-ddb1-46c7-ac79-7330c652abe3/resource/288b10dd-4f21-4338-b1ed-239487820512/download/288b10dd-4f21-4338-b1ed-239487820512.zip",
        ),
    ],
}

# Conjuntos predefinidos
GRUPOS = {
    # Todo lo necesario para el problema acotado (docs/problema.md)
    "acotado": ["fgj", "ensu", "censo", "geografia", "notas_fgj"],
    # El encuadre del Metro: carpetas de la FGJ más afluencia y estaciones
    "estaciones": ["fgj", "metro"],
    # Todas las fuentes disponibles
    "todas": list(FUENTES.keys()),
}


# INEGI responde 200 con una página HTML de «no encontrada» cuando el archivo no existe:
# el código de estado no basta, se revisan los primeros bytes.
FIRMAS = {".zip": b"PK", ".xlsx": b"PK", ".pdf": b"%PDF"}


def contenido_valido(ruta: Path) -> bool:
    with ruta.open("rb") as f:
        inicio = f.read(512)
    firma = FIRMAS.get(Path(ruta.name.removesuffix(".part")).suffix)
    if firma is not None:
        return inicio.startswith(firma)
    return not inicio.lstrip().lower().startswith((b"<!doctype", b"<html"))


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def descarga(nombre: str, url: str) -> tuple[Path, bool] | None:
    """Devuelve (ruta, recién_bajado), o None si falló."""
    destino = CRUDOS / nombre
    if destino.exists() and destino.stat().st_size > 0:
        mb = destino.stat().st_size / 1024 / 1024
        print(f"  ya existe, se respeta: {nombre} ({mb:.1f} MB)")
        return destino, False

    print(f"  bajando {nombre} …", flush=True)
    # El Python de python.org no trae certificados raíz; certifi los pone. Si aun así el
    # certificado no valida, se falla: nunca se baja sin verificar.
    ctx = ssl.create_default_context(cafile=certifi.where())
    tmp_destino = destino.with_suffix(destino.suffix + ".part")

    max_intentos = 15
    intentos = 0
    bloque_tam = 1024 * 1024  # 1 MB

    while intentos < max_intentos:
        intentos += 1
        bajados_iniciales = tmp_destino.stat().st_size if tmp_destino.exists() else 0

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            },
        )
        if bajados_iniciales > 0:
            req.add_header("Range", f"bytes={bajados_iniciales}-")
            print(f"    reanudando desde {bajados_iniciales / 1024 / 1024:.1f} MB …", flush=True)

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                status = resp.status
                # Si el servidor responde 206 (Partial Content), agregamos; si responde 200, empezamos de cero
                modo = "ab" if (status == 206 and bajados_iniciales > 0) else "wb"
                if modo == "wb":
                    bajados_iniciales = 0

                content_range = resp.headers.get("Content-Range")
                if content_range and "/" in content_range:
                    total = int(content_range.split("/")[-1])
                else:
                    len_header = resp.headers.get("Content-Length")
                    total = int(len_header) + bajados_iniciales if len_header else None

                bajados = bajados_iniciales
                with tmp_destino.open(modo) as f:
                    while True:
                        bloque = resp.read(bloque_tam)
                        if not bloque:
                            break
                        f.write(bloque)
                        bajados += len(bloque)
                        mb_bajados = bajados / 1024 / 1024
                        if total:
                            mb_total = total / 1024 / 1024
                            pct = (bajados / total) * 100
                            print(
                                f"\r    {mb_bajados:.1f} / {mb_total:.1f} MB ({pct:.1f}%)",
                                end="",
                                flush=True,
                            )
                        else:
                            print(f"\r    {mb_bajados:.1f} MB", end="", flush=True)

                if total is None:
                    # Sin tamaño declarado no hay forma de saber si llegó completo.
                    print(f"\n  FALLÓ {nombre}: el servidor no declaró el tamaño.", file=sys.stderr)
                    tmp_destino.unlink(missing_ok=True)
                    return None
                if bajados >= total:
                    print()
                    if not contenido_valido(tmp_destino):
                        print(f"  FALLÓ {nombre}: no es el archivo esperado (¿página de error?).", file=sys.stderr)
                        tmp_destino.unlink()
                        return None
                    tmp_destino.rename(destino)
                    return destino, True

        except Exception as e:
            if isinstance(e, ssl.SSLError) or isinstance(getattr(e, "reason", None), ssl.SSLError):
                raise  # un certificado inválido no se reintenta ni se ignora
            print(f"\n    [intento {intentos}/{max_intentos}] interrupción: {e}. Reconectando en 3s …", flush=True)
            time.sleep(3)

    print(f"\n  FALLÓ {nombre} tras {max_intentos} intentos.", file=sys.stderr)
    return None


def anota(entradas: list[tuple[str, str, Path]]) -> None:
    hoy = dt.date.today().isoformat()
    nuevas = [f"\n## {hoy}\n"]
    for nombre, url, ruta in entradas:
        mb = ruta.stat().st_size / 1024 / 1024
        nuevas.append(
            f"- `{nombre}` — {mb:.1f} MB — sha256 `{sha256(ruta)[:16]}…`\n"
            f"  origen: {url}\n"
        )
    if not MANIFIESTO.exists():
        MANIFIESTO.write_text(
            "# Manifiesto de descargas\n\n"
            "Append-only. Cada entrada dice qué archivo se bajó, de dónde y cuándo.\n"
            "Si el hash cambia entre dos descargas del mismo nombre, el portal movió el\n"
            "archivo por debajo y eso hay que decirlo en el escrito.\n",
            encoding="utf-8",
        )
    with MANIFIESTO.open("a", encoding="utf-8") as f:
        f.writelines(nuevas)
    print(f"\nManifiesto actualizado: {MANIFIESTO.relative_to(RAIZ)}")


def main() -> int:
    opciones_fuente = sorted(list(FUENTES.keys()) + list(GRUPOS.keys()))
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fuente",
        action="append",
        choices=opciones_fuente,
        default=None,
        help="Fuente o grupo a descargar (ej: acotado, fgj, ensu, censo, geografia, notas_fgj, todas)",
    )
    p.add_argument("--lista", action="store_true", help="muestra las fuentes y sale")
    args = p.parse_args()

    if args.lista or not args.fuente:
        print("Fuentes disponibles:\n")
        for clave, archivos in FUENTES.items():
            print(f"  [{clave}]:")
            for nombre, url in archivos:
                print(f"    - {nombre}\n        {url}")
        print("\nGrupos predefinidos:")
        for grp, fuentes in GRUPOS.items():
            print(f"  --fuente {grp} -> descarga: {', '.join(fuentes)}")
        return 0

    # Expandir grupos
    fuentes_a_bajar: list[str] = []
    for f in args.fuente:
        if f in GRUPOS:
            for sub_f in GRUPOS[f]:
                if sub_f not in fuentes_a_bajar:
                    fuentes_a_bajar.append(sub_f)
        else:
            if f not in fuentes_a_bajar:
                fuentes_a_bajar.append(f)

    CRUDOS.mkdir(parents=True, exist_ok=True)
    hechas: list[tuple[str, str, Path]] = []
    fallos = 0
    for clave in fuentes_a_bajar:
        print(f"\n[{clave}]")
        for nombre, url in FUENTES[clave]:
            resultado = descarga(nombre, url)
            if resultado is None:
                fallos += 1
            elif resultado[1]:  # al manifiesto solo va lo que se bajó en esta corrida
                hechas.append((nombre, url, resultado[0]))

    if hechas:
        anota(hechas)
    if fallos:
        print(f"\n{fallos} descarga(s) fallaron. No se sigue como si nada.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

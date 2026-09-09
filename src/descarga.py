#!/usr/bin/env python3
"""Descarga las fuentes del caso y deja constancia de qué se bajó y cuándo.

Los datos no viven en git: viven aquí, reconstruibles. El manifiesto es lo que se
versiona, para que dentro de un mes se sepa exactamente sobre qué archivo se corrió el
análisis — y para que si el portal cambia el archivo por debajo, el hash lo delate en vez
de que el cambio pase en silencio.

Uso:
    python src/descarga.py --lista
    python src/descarga.py --fuente fgj
    python src/descarga.py --fuente fgj --fuente c5
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CRUDOS = RAIZ / "datos" / "crudos"
MANIFIESTO = CRUDOS / "MANIFIESTO.md"

# URLs verificadas contra los portales el 2026-09-08. Ver datos/FUENTES.md.
FUENTES: dict[str, list[tuple[str, str]]] = {
    "fgj": [
        (
            "carpetasFGJ_acumulado_2016_2024.csv",
            "https://archivo.datos.cdmx.gob.mx/FGJ/carpetas/carpetasFGJ_acumulado_2025_01.csv",
        ),
        (
            "carpetasFGJ_previo_reclasificacion_jun2020.csv",
            "https://archivo.datos.cdmx.gob.mx/fiscalia-general-de-justicia/"
            "carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico/carpetas_ss_junio2020.csv",
        ),
    ],
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
}

# ENSU, ENVIPE y el marco geoestadístico del INEGI no tienen liga estable de descarga
# directa: se bajan a mano desde el portal. Cuando se bajen, se anotan igual en el
# manifiesto, con la fecha y el hash. Ver datos/FUENTES.md.


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def descarga(nombre: str, url: str) -> Path | None:
    destino = CRUDOS / nombre
    if destino.exists():
        print(f"  ya existe, se respeta: {nombre}")
        return destino
    print(f"  bajando {nombre} …", flush=True)
    try:
        urllib.request.urlretrieve(url, destino)
    except Exception as e:  # el fallo se grita, no se traga
        print(f"  FALLÓ {nombre}: {e}", file=sys.stderr)
        if destino.exists():
            destino.unlink()
        return None
    return destino


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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fuente", action="append", choices=sorted(FUENTES), default=None)
    p.add_argument("--lista", action="store_true", help="muestra las fuentes y sale")
    args = p.parse_args()

    if args.lista or not args.fuente:
        print("Fuentes con descarga automática:\n")
        for clave, archivos in FUENTES.items():
            print(f"  {clave}:")
            for nombre, url in archivos:
                print(f"    {nombre}\n      {url}")
        print("\nENSU, ENVIPE y marco geoestadístico: descarga manual, ver datos/FUENTES.md")
        return 0

    CRUDOS.mkdir(parents=True, exist_ok=True)
    hechas: list[tuple[str, str, Path]] = []
    fallos = 0
    for clave in args.fuente:
        print(f"\n[{clave}]")
        for nombre, url in FUENTES[clave]:
            ruta = descarga(nombre, url)
            if ruta is None:
                fallos += 1
            else:
                hechas.append((nombre, url, ruta))

    if hechas:
        anota(hechas)
    if fallos:
        print(f"\n{fallos} descarga(s) fallaron. No se sigue como si nada.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

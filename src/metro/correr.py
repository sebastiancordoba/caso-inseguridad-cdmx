#!/usr/bin/env python3
"""Corre el encuadre del Metro de punta a punta, en orden, y para donde las pruebas mandan parar.

    python src/descarga.py --fuente estaciones   # una vez: carpetas FGJ, afluencia, estaciones
    python src/metro/correr.py

Código 2 es «una prueba falló», no un error:
- 03_pruebas.py sale con 2 si falla C1 o C2. Con C2 fallada se sigue a 04_agencias.py, que
  es justo el diagnóstico de esa falla; con cualquier otro código distinto de cero, no.
- 04_agencias.py sale con 2 si el efecto agencia no queda establecido (punto de paro 1):
  ahí se para, y no hay estrato limpio, EDA ni hipótesis.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PASOS = ["01_llave_estaciones.py", "02_panel_estacion.py", "03_pruebas.py", "04_agencias.py"]
SIGUE_AUNQUE_FALLE_LA_PRUEBA = {"03_pruebas.py"}


def main() -> int:
    aqui = Path(__file__).resolve().parent
    for paso in PASOS:
        print(f"\n{'#' * 100}\n# {paso}\n{'#' * 100}", flush=True)
        r = subprocess.run([sys.executable, str(aqui / paso)])
        if r.returncode == 2 and paso in SIGUE_AUNQUE_FALLE_LA_PRUEBA:
            print(f"\n{paso}: una prueba falló (código 2). Se sigue con su diagnóstico.", flush=True)
            continue
        if r.returncode:
            print(f"\n{paso} terminó con código {r.returncode}. No se sigue.", file=sys.stderr)
            return r.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

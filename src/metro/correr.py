#!/usr/bin/env python3
"""Corre el encuadre del Metro de punta a punta, en orden, y para en el primer paso que falle.

    python src/descarga.py --fuente estaciones   # una vez: carpetas FGJ, afluencia, estaciones
    python src/metro/correr.py

03_pruebas.py sale con código 2 si falla C1 o C2: entonces no se sigue, a propósito.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PASOS = ["01_llave_estaciones.py", "02_panel_estacion.py", "03_pruebas.py"]


def main() -> int:
    aqui = Path(__file__).resolve().parent
    for paso in PASOS:
        print(f"\n{'#' * 100}\n# {paso}\n{'#' * 100}", flush=True)
        r = subprocess.run([sys.executable, str(aqui / paso)])
        if r.returncode:
            print(f"\n{paso} terminó con código {r.returncode}. No se sigue.", file=sys.stderr)
            return r.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

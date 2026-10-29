#!/usr/bin/env bash
# Compila el escrito IEEE con tectonic (trae su propio TeX Live; baja los paquetes la primera vez).
#   bash docs/escrito/compila.sh
set -euo pipefail
cd "$(dirname "$0")"
tectonic escrito.tex
# Cuenta de páginas, si hay pymupdf (no es parte de requirements.txt: solo sirve para esto).
"$(cd ../.. && pwd)/.venv/bin/python" -c "import pymupdf; d = pymupdf.open('escrito.pdf'); print('escrito.pdf:', len(d), 'páginas')" 2>/dev/null || true

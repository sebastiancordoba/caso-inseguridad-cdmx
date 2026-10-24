#!/usr/bin/env bash
# Compila el escrito IEEE con tectonic (trae su propio TeX Live; baja los paquetes la primera vez).
#   bash docs/escrito/compila.sh
set -euo pipefail
cd "$(dirname "$0")"
tectonic escrito.tex
"$(cd ../.. && pwd)/.venv/bin/python" -c "import pymupdf; d = pymupdf.open('escrito.pdf'); print('escrito.pdf:', len(d), 'páginas')"

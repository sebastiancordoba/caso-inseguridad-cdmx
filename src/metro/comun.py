"""Rutas, lectura y catálogos que comparten los scripts del encuadre del Metro.

El numerador de todo este encuadre son DENUNCIAS (carpetas de investigación), no robos:
toda columna, tabla y gráfica lo dice con «robos denunciados» o `tasa_denuncias_mm`.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent.parent
CRUDOS = RAIZ / "datos" / "crudos"
PROCESADOS = RAIZ / "datos" / "procesados"
FIGURAS = RAIZ / "docs" / "figuras" / "metro"

AFLUENCIA = CRUDOS / "afluencia_metro_simple.csv"
ESTACIONES_SHP = f"zip://{CRUDOS / 'stc_metro_shp.zip'}!stcmetro_shp/STC_Metro_estaciones_utm14n.shp"
CARPETAS = CRUDOS / "carpetasFGJ_acumulado_2025_01.csv"

LLAVE = PROCESADOS / "llave_estaciones.csv"
DENUNCIAS = PROCESADOS / "denuncias_metro_asignadas.csv"
PANEL = PROCESADOS / "panel_estacion.csv"
TABLAS = PROCESADOS / "metro_tablas"

INICIO, FIN = "2019-01-01", "2024-12-31"
UMBRAL_M = 150
DELITO = "ROBO A PASAJERO A BORDO DE METRO "  # con el espacio: deja fuera METROBUS
UTM = 32614

# Las 28 estaciones de correspondencia de la red y sus líneas, escritas a mano (por la
# herramienta de IA, de memoria del plano de la red); no se infieren de los datos.
# Falta que Sebas las coteje contra el plano oficial. 01_llave_estaciones.py las
# contrasta contra el campo TIPO del shapefile y avisa de cualquier diferencia.
CORRESPONDENCIAS: dict[str, list[str]] = {
    "Pantitlán": ["1", "5", "9", "A"],
    "Tacubaya": ["1", "7", "9"],
    "Chabacano": ["2", "8", "9"],
    "Balderas": ["1", "3"],
    "Salto del Agua": ["1", "8"],
    "Pino Suárez": ["1", "2"],
    "Candelaria": ["1", "4"],
    "San Lázaro": ["1", "B"],
    "Tacuba": ["2", "7"],
    "Hidalgo": ["2", "3"],
    "Bellas Artes": ["2", "8"],
    "Ermita": ["2", "12"],
    "Deportivo 18 de Marzo": ["3", "6"],
    "La Raza": ["3", "5"],
    "Guerrero": ["3", "B"],
    "Centro Médico": ["3", "9"],
    "Zapata": ["3", "12"],
    "Martín Carrera": ["4", "6"],
    "Consulado": ["4", "5"],
    "Morelos": ["4", "B"],
    "Jamaica": ["4", "9"],
    "Santa Anita": ["4", "8"],
    "Instituto del Petróleo": ["5", "6"],
    "Oceanía": ["5", "B"],
    "El Rosario": ["6", "7"],
    "Mixcoac": ["7", "12"],
    "Garibaldi/Lagunilla": ["8", "B"],
    "Atlalilco": ["8", "12"],
}

# Pares que no casan ni quitando acentos y mayúsculas. Resueltos a mano, uno por uno:
# (línea, nombre de afluencia normalizado) → nombre en el shapefile.
MANUALES: dict[tuple[str, str], tuple[str, str]] = {
    ("3", "ninos heroes"): (
        "Niños Héroes/Poder Judicial CDMX",
        "El shapefile trae el nombre oficial desde 2019; la afluencia conserva el anterior.",
    ),
    ("6", "uam-azcapotzalco"): ("UAM Azcapotzalco", "Solo cambia el guion."),
    ("9", "mixiuhca"): (
        "Mixhiuca",
        "El shapefile trae la errata «Mixhiuca»; el nombre de la estación es Mixiuhca.",
    ),
}

# Estaciones en el Estado de México: un robo ahí se denuncia ante la Fiscalía del Estado
# de México, no ante la FGJ de la CDMX, así que su numerador está subcontado por
# construcción. Se marcan con el campo ALCALDIAS del shapefile, no con esta lista; esta
# lista solo sirve para comprobar que el campo dice lo esperado.
FUERA_CDMX_ESPERADAS = {
    "Cuatro Caminos", "Los Reyes", "La Paz", "Nezahualcóyotl", "Impulsora",
    "Río de los Remedios", "Múzquiz", "Ecatepec", "Olímpica", "Plaza Aragón", "Ciudad Azteca",
}


def arregla(s: str) -> str:
    """Deshace la doble codificación («CatÃ³lica» → «Católica») donde la hay."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def normaliza(s: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(sin_acentos.lower().split())


def linea_corta(s: str) -> str:
    """«Linea 1», «LÃ­nea 1» y «01» → «1»."""
    return normaliza(arregla(s)).replace("linea", "").strip().lstrip("0").upper()


def lee_estaciones() -> gpd.GeoDataFrame:
    est = gpd.read_file(ESTACIONES_SHP)
    est["linea"] = est["LINEA"].map(linea_corta)
    # El archivo se llama «utm14n» pero declara EPSG:4326 y trae grados; se reproyecta.
    assert est.crs.to_epsg() == 4326 and est.geometry.x.between(-100, -98).all()
    return est.to_crs(UTM)


def lee_afluencia() -> pd.DataFrame:
    af = pd.read_csv(AFLUENCIA, dtype={"afluencia": "int64"})
    af = af[af["fecha"].between(INICIO, FIN)].copy()
    af["linea_corta"] = af["linea"].map(linea_corta)
    af["clave"] = af["estacion"].map(arregla).map(normaliza)
    return af

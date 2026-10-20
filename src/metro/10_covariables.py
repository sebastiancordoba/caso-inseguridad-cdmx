#!/usr/bin/env python3
"""Covariables de estación para la decisión 66: ¿más información mejora la predicción?

Calcula, para las 124 estaciones de paso de la CDMX y cada año 2019–2024, el ENTORNO:
cuántas carpetas de la FGJ de cualquier delito —menos el robo a pasajero a bordo del
Metro, que es el numerador— tienen coordenadas a 500 m o menos del punto de la estación,
y cuántas de ellas son robo a transeúnte en vía pública. Es la única covariable que hay
que construir desde el archivo crudo; línea y tamaño salen del panel.

El radio de 500 m y las dos variantes están fijados en la decisión 66 antes de correr
esto. Se cuenta por fecha del hecho, como todo el encuadre (decisión 4). Las carpetas sin
coordenadas (1,041 de las 8,366 del propio delito; una proporción parecida en el resto)
no se pueden contar: el entorno está medido con el mismo defecto que el numerador.

Salida: datos/procesados/covariables_estacion.csv (estacion, anio, linea, entorno_todos,
entorno_transeunte). Tarda ~1 minuto: lee el CSV de 534 MB de la FGJ.

    python src/metro/10_covariables.py
"""

from __future__ import annotations

import sys
import time

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from comun import CARPETAS, DELITO, FIN, INICIO, PANEL, PROCESADOS, UTM, lee_estaciones

RADIO_M = 500
TRANSEUNTE = "ROBO A TRANSEUNTE EN VIA PUBLICA"
SALIDA = PROCESADOS / "covariables_estacion.csv"


def estaciones_de_paso(panel: pd.DataFrame) -> pd.DataFrame:
    p = panel[~panel["es_correspondencia"] & ~panel["fuera_cdmx"]]
    e = p.groupby("estacion").agg(linea=("lineas", "first")).reset_index()
    assert len(e) == 124, len(e)
    est = lee_estaciones()
    pts = est[est["NOMBRE"].isin(e["estacion"])][["NOMBRE", "geometry"]].drop_duplicates("NOMBRE")
    faltan = set(e["estacion"]) - set(pts["NOMBRE"])
    assert not faltan, f"estaciones sin punto en el shapefile: {sorted(faltan)}"
    pts = pts.rename(columns={"NOMBRE": "estacion"})
    pts["x"], pts["y"] = pts.geometry.x, pts.geometry.y
    return e.merge(pts[["estacion", "x", "y"]], on="estacion")


def main() -> int:
    t0 = time.time()
    panel = pd.read_csv(PANEL, dtype={"lineas": str})
    est = estaciones_de_paso(panel)
    print(f"{len(est)} estaciones de paso con coordenadas.")

    df = pd.read_csv(CARPETAS, dtype=str, usecols=["fecha_hecho", "delito", "latitud", "longitud"])
    n0 = len(df)
    fecha = pd.to_datetime(df["fecha_hecho"].str[:10], format="%Y-%m-%d", errors="coerce")
    df = df[fecha.between(INICIO, FIN)].copy()
    df["anio"] = fecha[df.index].dt.year
    n1 = len(df)
    es_metro = df["delito"].str.startswith(DELITO, na=False)
    df = df[~es_metro]
    lat, lon = pd.to_numeric(df["latitud"], errors="coerce"), pd.to_numeric(df["longitud"], errors="coerce")
    con = lat.notna() & lon.notna() & lat.between(19.0, 19.7) & lon.between(-99.4, -98.9)
    print(f"Carpetas en el archivo: {n0:,}; con fecha del hecho en 2019–2024: {n1:,}; de ellas, del propio delito "
          f"(se excluyen): {int(es_metro.sum()):,}; del resto, con coordenadas válidas: {int(con.sum()):,} de {len(df):,} "
          f"({100 * con.mean():.1f} %).  [{time.time() - t0:.0f} s]")
    df = df[con]
    trans = df["delito"].str.startswith(TRANSEUNTE, na=False)
    print("Variantes de «robo a transeúnte» en el archivo (solo se cuenta la de vía pública):")
    print(df.loc[df["delito"].str.startswith("ROBO A TRANSEUNTE", na=False), "delito"].value_counts().to_string())

    pts = gpd.GeoSeries(gpd.points_from_xy(lon[df.index], lat[df.index]), crs=4326).to_crs(UTM)
    xy = np.column_stack([pts.x.to_numpy(), pts.y.to_numpy()])
    arbol = cKDTree(xy)
    vecinos = arbol.query_ball_point(est[["x", "y"]].to_numpy(), r=RADIO_M)
    anio = df["anio"].to_numpy()
    trans = trans.to_numpy()
    filas = []
    for (_, e), idx in zip(est.iterrows(), vecinos):
        idx = np.asarray(idx, dtype=int)
        for a in range(2019, 2025):
            en = idx[anio[idx] == a]
            filas.append({"estacion": e["estacion"], "anio": a, "linea": e["linea"],
                          "entorno_todos": int(len(en)), "entorno_transeunte": int(trans[en].sum())})
    cov = pd.DataFrame(filas)
    cov.to_csv(SALIDA, index=False)
    tot = cov.groupby("estacion")[["entorno_todos", "entorno_transeunte"]].sum()
    print(f"\nEntorno a {RADIO_M} m, suma 2019–2024 por estación: todos los delitos mediana {tot['entorno_todos'].median():.0f} "
          f"(mín {tot['entorno_todos'].min()}, máx {tot['entorno_todos'].max()}); robo a transeúnte en vía pública mediana "
          f"{tot['entorno_transeunte'].median():.0f} (mín {tot['entorno_transeunte'].min()}, máx {tot['entorno_transeunte'].max()}).")
    print("Las cinco de más entorno:", tot.sort_values("entorno_todos", ascending=False).head(5).to_dict("index"))
    print(f"{len(cov)} filas → {SALIDA.relative_to(SALIDA.parents[2])}  [{time.time() - t0:.0f} s]")
    return 0


if __name__ == "__main__":
    sys.exit(main())

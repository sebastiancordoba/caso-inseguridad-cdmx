#!/usr/bin/env python3
"""Entregable A: llave entre los nombres de estación de la afluencia y los del shapefile.

Regla de cruce, en este orden y sin coincidencia aproximada:
  1. misma línea y mismo nombre tras deshacer la doble codificación y quitar acentos,
     mayúsculas y espacios repetidos;
  2. si no, la tabla MANUALES de comun.py, resuelta a mano par por par.
Lo que no case por ninguna de las dos detiene el script.

Una fila por cada grafía cruda (nombre, línea) que aparece en TODO el archivo de
afluencia, no solo en la ventana, para que la llave sirva si la ventana cambia.
Escribe datos/procesados/llave_estaciones.csv e imprime cada caso que no casó 1 a 1.
"""

from __future__ import annotations

import sys

import pandas as pd

from comun import (
    AFLUENCIA, CORRESPONDENCIAS, FUERA_CDMX_ESPERADAS, LLAVE, MANUALES, PROCESADOS,
    arregla, lee_estaciones, linea_corta, normaliza,
)


def main() -> int:
    est = lee_estaciones()
    est["clave"] = est["NOMBRE"].map(normaliza)
    assert not est.duplicated(["linea", "clave"]).any()
    por_clave = est.set_index(["linea", "clave"])

    # --- correspondencias: lista escrita a mano contra el campo TIPO del shapefile
    a_mano = {(l, normaliza(n)) for n, ls in CORRESPONDENCIAS.items() for l in ls}
    del_shp = set(est[est["TIPO"].str.contains("Transbordo")].set_index(["linea", "clave"]).index)
    if a_mano != del_shp:
        print("La lista de correspondencias no coincide con el shapefile:", file=sys.stderr)
        print("  solo a mano:", sorted(a_mano - del_shp), file=sys.stderr)
        print("  solo en shp:", sorted(del_shp - a_mano), file=sys.stderr)
        return 1
    print(f"Correspondencias: {len(CORRESPONDENCIAS)} estaciones, {len(a_mano)} puntos "
          "estación-línea; la lista a mano y el campo TIPO del shapefile coinciden.")

    # --- grafías crudas de la afluencia
    af = pd.read_csv(AFLUENCIA, usecols=["fecha", "linea", "estacion"], dtype=str)
    crudas = af.groupby(["linea", "estacion"])["fecha"].agg(desde="min", hasta="max", dias="size").reset_index()
    crudas["linea_corta"] = crudas["linea"].map(linea_corta)
    crudas["clave"] = crudas["estacion"].map(arregla).map(normaliza)

    filas, sin_casar = [], []
    for r in crudas.itertuples():
        k = (r.linea_corta, r.clave)
        if k in por_clave.index:
            nombre_shp, como = por_clave.loc[k, "NOMBRE"], "normalizado"
            nota = ""
        elif k in MANUALES:
            nombre_shp, nota = MANUALES[k]
            como = "a mano"
        else:
            sin_casar.append(k)
            continue
        e = por_clave.loc[(r.linea_corta, normaliza(nombre_shp))]
        filas.append({
            "nombre_afluencia": r.estacion,
            "linea_afluencia": r.linea,
            "nombre_shp": nombre_shp,
            "linea": r.linea_corta,
            "es_correspondencia": nombre_shp in CORRESPONDENCIAS,
            "cve_eod17": e["CVE_EOD17"],
            "cve_est": e["CVE_EST"],
            "fuera_cdmx": "Estado de México" in (e["ALCALDIAS"] or "") or e["ALCALDIAS"] in (None, ""),
            "alcaldia_o_municipio": e["ALCALDIAS"],
            "cruce": como,
            "codificacion_rota": arregla(r.estacion) != r.estacion,
            "linea_codificacion_rota": arregla(r.linea) != r.linea,
            "desde": r.desde, "hasta": r.hasta, "dias": r.dias,
            "nota": nota,
        })
    if sin_casar:
        print("Sin casar, hay que resolverlos a mano en comun.MANUALES:", sin_casar, file=sys.stderr)
        return 1

    llave = pd.DataFrame(filas).sort_values(["linea", "nombre_shp", "desde"])
    cubiertos = set(zip(llave["linea"], llave["nombre_shp"].map(normaliza)))
    faltan = set(por_clave.index) - cubiertos
    assert not faltan, f"puntos del shapefile sin afluencia: {faltan}"

    PROCESADOS.mkdir(parents=True, exist_ok=True)
    llave.to_csv(LLAVE, index=False)

    # --- informe
    print(f"\n{len(llave)} grafías crudas (nombre, línea) → {len(cubiertos)} puntos estación-línea "
          f"→ {llave['nombre_shp'].nunique()} estaciones.")
    print(f"  nombres crudos distintos: {llave['nombre_afluencia'].nunique()}; "
          f"con codificación rota: {llave.loc[llave['codificacion_rota'], 'nombre_afluencia'].nunique()}")
    print(f"  grafías de línea: {sorted(llave['linea_afluencia'].unique())[:2]} … "
          f"({llave['linea_afluencia'].nunique()} para 12 líneas)")

    print("\nCasos que no casaron 1 a 1:")
    print("  a) resueltos a mano:")
    for r in llave[llave["cruce"] == "a mano"].drop_duplicates(["linea", "nombre_shp"]).itertuples():
        print(f"     L{r.linea}  «{arregla(r.nombre_afluencia)}» → «{r.nombre_shp}». {r.nota}")
    print("  b) un mismo punto con más de una grafía cruda de estación:")
    g = llave.groupby(["linea", "nombre_shp"])["nombre_afluencia"].nunique()
    for (l, n) in g[g > 1].index:
        for r in llave[(llave["linea"] == l) & (llave["nombre_shp"] == n)].drop_duplicates("nombre_afluencia").itertuples():
            print(f"     L{l}  {n}: «{r.nombre_afluencia}»")
    print("  c) casados por normalización, pero con el nombre distinto aun con la codificación arreglada:")
    d = llave[(llave["cruce"] == "normalizado")].copy()
    d["arreglado"] = d["nombre_afluencia"].map(arregla)
    for r in d[d["arreglado"] != d["nombre_shp"]].drop_duplicates(["linea", "arreglado"]).itertuples():
        print(f"     L{r.linea}  «{r.arreglado}» ↔ «{r.nombre_shp}»")

    fuera = set(llave.loc[llave["fuera_cdmx"], "nombre_shp"])
    print(f"\nEstaciones fuera de la CDMX según el shapefile ({len(fuera)}): {sorted(fuera)}")
    if fuera != FUERA_CDMX_ESPERADAS:
        print("  OJO, difiere de la lista esperada:", sorted(fuera ^ FUERA_CDMX_ESPERADAS))
    print(f"\n→ {LLAVE.relative_to(LLAVE.parents[2])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

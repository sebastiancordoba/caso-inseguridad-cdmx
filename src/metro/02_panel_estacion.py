#!/usr/bin/env python3
"""Entregable B: panel estación × mes, 2019-01 a 2024-12.

Unidad: la estación (163), no el punto estación-línea (195). En una correspondencia el
punto más cercano a una carpeta es arbitrario —los andenes de dos líneas distan decenas
de metros y la carpeta no dice en cuál iba el pasajero—, así que las entradas de sus
líneas se suman y `lineas` las lista todas.

Numerador: carpetas de la FGJ de «ROBO A PASAJERO A BORDO DE METRO», con y sin violencia,
por fecha del hecho. Son DENUNCIAS. Cada carpeta se asigna al punto estación-línea más
cercano; cuenta para el panel si está a 150 m o menos. La distancia de todas se guarda en
datos/procesados/denuncias_metro_asignadas.csv para la sensibilidad posterior.

Denominador: entradas por torniquete (afluencia), sumadas por estación y mes. Un mes con
cero entradas es una estación cerrada, no un dato faltante: se deja en cero.
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

from comun import (
    CARPETAS, DELITO, DENUNCIAS, FIN, INICIO, LLAVE, PANEL, UMBRAL_M, UTM,
    arregla, canal, lee_afluencia, lee_estaciones, normaliza, tiene_agencia,
)


def entradas_mensuales(llave: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    af = lee_afluencia()
    avisos = []

    # Diciembre de 2020, Línea B: «Oceanía» viene dos veces por día y «Deportivo Oceanía»
    # no viene. Una de las dos series es Deportivo Oceanía mal rotulada, y no hay forma de
    # saber cuál: el orden de las filas entre las dos estaciones cambia de un día a otro en
    # los meses vecinos (comprobado), y sus niveles se traslapan. No se reparte: las
    # entradas de las dos estaciones ese mes quedan como dato faltante y marcadas.
    dup = af.duplicated(["fecha", "linea_corta", "clave"], keep=False)
    dudosas: set[tuple[str, str]] = set()
    if dup.any():
        d = af[dup]
        assert set(d["clave"]) == {"oceania"} and set(d["linea_corta"]) == {"B"}, d[["linea", "estacion"]].drop_duplicates()
        meses = sorted(d["fecha"].str[:7].unique())
        dudosas = {(m, e) for m in meses for e in ["Oceanía", "Deportivo Oceanía"]}
        avisos.append(
            f"Línea B, {', '.join(meses)}: «Oceanía» duplicada ({int(dup.sum())} filas, "
            f"{int(d['afluencia'].sum()):,} entradas entre las dos series) y sin «Deportivo Oceanía». "
            "No se puede saber qué serie es de cuál: entradas = NaN para las dos estaciones ese mes."
        )
        af = af[~dup].copy()
    assert not af.duplicated(["fecha", "linea_corta", "clave"]).any()

    ll = llave.assign(clave=llave["nombre_afluencia"].map(lambda s: normaliza(arregla(s))))
    ll = ll[["linea", "clave", "nombre_shp"]].drop_duplicates()
    # Las tres claves resueltas a mano conservan su clave de afluencia, así que el cruce es directo.
    af = af.merge(ll, left_on=["linea_corta", "clave"], right_on=["linea", "clave"], how="left", validate="m:1")
    assert af["nombre_shp"].notna().all(), af.loc[af["nombre_shp"].isna(), ["linea", "estacion"]].drop_duplicates()

    af["anio_mes"] = af["fecha"].str[:7]
    por_punto = af.groupby(["nombre_shp", "linea_corta", "fecha"])["afluencia"].sum().reset_index()
    # Día cerrado: ninguna línea de la estación registró entradas.
    por_dia = por_punto.groupby(["nombre_shp", "fecha"])["afluencia"].sum().reset_index()
    por_dia["anio_mes"] = por_dia["fecha"].str[:7]
    m = por_dia.groupby(["nombre_shp", "anio_mes"]).agg(
        entradas=("afluencia", "sum"),
        dias_con_dato=("fecha", "nunique"),
        dias_sin_entradas=("afluencia", lambda x: int((x == 0).sum())),
    ).reset_index().rename(columns={"nombre_shp": "estacion"})
    # Rejilla completa: toda estación, todo mes. Lo que falte se queda como NaN, a la vista.
    meses = sorted(af["anio_mes"].unique())
    rejilla = pd.MultiIndex.from_product([sorted(llave["nombre_shp"].unique()), meses], names=["estacion", "anio_mes"])
    m = m.set_index(["estacion", "anio_mes"]).reindex(rejilla).reset_index()
    m["entradas_dudosas"] = [(a, e) in dudosas for a, e in zip(m["anio_mes"], m["estacion"])]
    m.loc[m["entradas_dudosas"], ["entradas", "dias_con_dato", "dias_sin_entradas"]] = float("nan")
    return m, avisos


def denuncias() -> tuple[pd.DataFrame, dict[str, int]]:
    df = pd.read_csv(
        CARPETAS, dtype=str,
        usecols=["fecha_hecho", "hora_hecho", "fecha_inicio", "delito", "fiscalia", "agencia", "alcaldia_hecho", "latitud", "longitud"],
    )
    df = df[df["delito"].str.startswith(DELITO, na=False)].copy()
    cuenta = {"carpetas del delito, todos los años": len(df)}
    fecha = pd.to_datetime(df["fecha_hecho"].str[:10], format="%Y-%m-%d", errors="coerce")
    cuenta["sin fecha del hecho"] = int(fecha.isna().sum())
    df = df[fecha.between(INICIO, FIN)].copy()
    df["fecha"] = fecha[fecha.between(INICIO, FIN)]
    cuenta["en la ventana 2019-2024 por fecha del hecho"] = len(df)

    df["canal"] = canal(df["fiscalia"], df["agencia"])
    df["con_violencia"] = df["delito"].str.endswith("CON VIOLENCIA")
    assert (df["con_violencia"] | df["delito"].str.endswith("SIN VIOLENCIA")).all()
    lat = pd.to_numeric(df["latitud"], errors="coerce")
    lon = pd.to_numeric(df["longitud"], errors="coerce")
    df["con_coordenadas"] = lat.notna() & lon.notna()
    cuenta["sin coordenadas"] = int((~df["con_coordenadas"]).sum())

    est = lee_estaciones()[["NOMBRE", "linea", "geometry"]]
    con = df[df["con_coordenadas"]]
    pts = gpd.GeoDataFrame(con, geometry=gpd.points_from_xy(lon[con.index], lat[con.index]), crs=4326).to_crs(UTM)
    j = gpd.sjoin_nearest(pts, est, distance_col="distancia_m")
    j = j[~j.index.duplicated(keep="first")]  # empate exacto entre dos puntos: se queda el primero
    df.loc[j.index, "estacion_mas_cercana"] = j["NOMBRE"]
    df.loc[j.index, "linea_punto_mas_cercano"] = j["linea"]
    df.loc[j.index, "distancia_m"] = j["distancia_m"].round(1)
    df["asignada"] = df["distancia_m"].le(UMBRAL_M)
    cuenta[f"con coordenadas pero a más de {UMBRAL_M} m de toda estación"] = int((df["con_coordenadas"] & ~df["asignada"]).sum())
    cuenta["asignadas a una estación"] = int(df["asignada"].sum())

    df["anio_mes"] = df["fecha"].dt.strftime("%Y-%m")
    df["dia_semana"] = df["fecha"].dt.dayofweek  # 0 = lunes
    df["hora"] = pd.to_numeric(df["hora_hecho"].str[:2], errors="coerce")
    df["minuto"] = pd.to_numeric(df["hora_hecho"].str[3:5], errors="coerce")
    cols = ["fecha", "anio_mes", "dia_semana", "hora", "minuto", "fecha_inicio", "delito", "con_violencia", "fiscalia", "agencia", "canal",
            "alcaldia_hecho", "latitud", "longitud", "con_coordenadas", "estacion_mas_cercana",
            "linea_punto_mas_cercano", "distancia_m", "asignada"]
    return df[cols], cuenta


def main() -> int:
    llave = pd.read_csv(LLAVE, dtype={"linea": str, "cve_eod17": str})
    entradas, avisos = entradas_mensuales(llave)
    den, cuenta = denuncias()
    den.to_csv(DENUNCIAS, index=False)

    a = den[den["asignada"]]
    n = a.groupby(["estacion_mas_cercana", "anio_mes"]).agg(
        robos_denunciados_total=("asignada", "size"),
        robos_denunciados_con_violencia=("con_violencia", "sum"),
        robos_denunciados_canal_digital=("canal", lambda s: int((s == "DIGITAL").sum())),
        robos_denunciados_canal_agencia_metro=("canal", lambda s: int(s.str.startswith("STCM").sum())),
    ).reset_index().rename(columns={"estacion_mas_cercana": "estacion"})

    attrs = llave.groupby("nombre_shp").agg(
        lineas=("linea", lambda s: "|".join(sorted(set(s), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x)))),
        n_lineas=("linea", "nunique"),
        es_correspondencia=("es_correspondencia", "first"),
        fuera_cdmx=("fuera_cdmx", "first"),
    ).reset_index().rename(columns={"nombre_shp": "estacion"})

    panel = entradas.merge(n, on=["estacion", "anio_mes"], how="left").merge(attrs, on="estacion", validate="m:1")
    cuentas = ["robos_denunciados_total", "robos_denunciados_con_violencia",
               "robos_denunciados_canal_digital", "robos_denunciados_canal_agencia_metro"]
    panel[cuentas] = panel[cuentas].fillna(0).astype(int)  # sin carpeta asignada ese mes = cero denuncias, no dato faltante
    panel["robos_denunciados_sin_violencia"] = panel["robos_denunciados_total"] - panel["robos_denunciados_con_violencia"]
    panel["tiene_agencia"] = tiene_agencia(panel["estacion"], panel["anio_mes"])  # con vigencia por mes
    panel["anio"] = panel["anio_mes"].str[:4].astype(int)
    panel["mes"] = panel["anio_mes"].str[5:].astype(int)
    panel = panel[[
        "estacion", "anio_mes", "anio", "mes", "lineas", "n_lineas", "es_correspondencia", "fuera_cdmx", "tiene_agencia",
        "robos_denunciados_total", "robos_denunciados_con_violencia", "robos_denunciados_sin_violencia",
        "robos_denunciados_canal_digital", "robos_denunciados_canal_agencia_metro",
        "entradas", "dias_con_dato", "dias_sin_entradas", "entradas_dudosas",
    ]].sort_values(["estacion", "anio_mes"])

    assert len(panel) == 163 * 72, len(panel)
    assert not panel.duplicated(["estacion", "anio_mes"]).any()
    assert panel["robos_denunciados_total"].sum() == cuenta["asignadas a una estación"]
    panel.to_csv(PANEL, index=False)

    print("Carpetas:")
    for k, v in cuenta.items():
        print(f"  {v:>7,}  {k}")
    v = cuenta["en la ventana 2019-2024 por fecha del hecho"]
    print(f"  sin asignar: {v - cuenta['asignadas a una estación']:,} de {v:,} "
          f"({100 * (1 - cuenta['asignadas a una estación'] / v):.1f} %)")
    lejos = den[den["con_coordenadas"] & ~den["asignada"]]
    print("  las que quedan lejos, por distancia:",
          pd.cut(lejos["distancia_m"], [150, 250, 500, 1000, 1e6]).value_counts().sort_index().to_dict())
    print("  sin coordenadas, por año:", den[~den["con_coordenadas"]].groupby(den["fecha"].dt.year).size().to_dict())
    print("  sin coordenadas, con violencia: %.1f %% contra %.1f %% en las que sí traen" % (
        100 * den.loc[~den["con_coordenadas"], "con_violencia"].mean(), 100 * den.loc[den["con_coordenadas"], "con_violencia"].mean()))
    cerr = panel[(panel["entradas"] == 0)]
    falt = panel[panel["entradas"].isna()]
    print(f"\nEstaciones-mes sin entradas conocidas: {len(falt)} "
          f"({', '.join(falt['estacion'] + ' ' + falt['anio_mes'])}), con {falt['robos_denunciados_total'].sum()} robos denunciados.")
    print(f"Entradas: {panel['entradas'].sum():,.0f} en la ventana; {len(cerr)} estaciones-mes con cero entradas "
          f"(cerradas), con {cerr['robos_denunciados_total'].sum()} robos denunciados en esos meses.")
    for t in avisos:
        print("  AVISO:", t)
    print(f"\n{len(panel):,} filas → {PANEL.relative_to(PANEL.parents[2])}; "
          f"{len(den):,} carpetas → {DENUNCIAS.relative_to(DENUNCIAS.parents[2])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

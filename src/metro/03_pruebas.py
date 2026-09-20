#!/usr/bin/env python3
"""Entregable C: las tres pruebas que matan el encuadre, en orden. Para en la primera que falle.

Los criterios de falla se fijaron ANTES de ver resultados (docs/decisiones.md, 2026-09-20):

C1  falla si Spearman(conteo, tasa) >= 0.9 Y los top-10 coinciden en nueve o más.
C2  falla si 7 o más de las 10 primeras por tasa son de correspondencia, o 12 o más de
    las 20 primeras. Las correspondencias son 28 de 163 (17 %): por azar se esperan 1.7
    en un top-10 y 3.4 en un top-20.
C3  no mata: describe si la tasa de la red se sostuvo cuando la afluencia se desplomó.

Tasa cruda = 1e6 × robos denunciados / entradas, sobre los meses en que la estación tuvo
entradas conocidas y mayores que cero. Código de salida: 0 pasa, 2 falla una prueba.
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from comun import DENUNCIAS, FIGURAS, PANEL, TABLAS

C1_RHO, C1_COINCIDENCIAS = 0.9, 9
C2_TOP10, C2_TOP20 = 7, 12


def tasas_por_estacion(panel: pd.DataFrame) -> pd.DataFrame:
    abiertos = panel[panel["entradas"] > 0]  # deja fuera meses cerrados y los dos sin entradas conocidas
    t = abiertos.groupby("estacion").agg(
        lineas=("lineas", "first"),
        es_correspondencia=("es_correspondencia", "first"),
        fuera_cdmx=("fuera_cdmx", "first"),
        robos_denunciados=("robos_denunciados_total", "sum"),
        robos_denunciados_con_violencia=("robos_denunciados_con_violencia", "sum"),
        entradas=("entradas", "sum"),
        meses_abierta=("anio_mes", "nunique"),
    ).reset_index()
    t["tasa_denuncias_mm"] = 1e6 * t["robos_denunciados"] / t["entradas"]
    t["posicion_conteo"] = t["robos_denunciados"].rank(ascending=False, method="min").astype(int)
    t["posicion_tasa"] = t["tasa_denuncias_mm"].rank(ascending=False, method="min").astype(int)
    t["cambio_de_posicion"] = t["posicion_conteo"] - t["posicion_tasa"]  # positivo: sube al ordenar por tasa
    return t.sort_values("posicion_conteo")


def spearman(a: pd.Series, b: pd.Series) -> float:
    """Pearson de los rangos (empates con rango promedio); evita depender de scipy."""
    return a.rank().corr(b.rank())


def c1(t: pd.DataFrame, nombre: str) -> dict:
    rho = spearman(t["robos_denunciados"], t["tasa_denuncias_mm"])
    top_c = set(t.nsmallest(10, "posicion_conteo")["estacion"])
    top_t = set(t.nsmallest(10, "posicion_tasa")["estacion"])
    return {"universo": nombre, "estaciones": len(t), "spearman": round(rho, 3), "coincidencias_top10": len(top_c & top_t),
            "falla": bool(rho >= C1_RHO and len(top_c & top_t) >= C1_COINCIDENCIAS)}


def c2(t: pd.DataFrame, nombre: str) -> dict:
    o = t.sort_values("posicion_tasa")
    k10, k20 = int(o.head(10)["es_correspondencia"].sum()), int(o.head(20)["es_correspondencia"].sum())
    con, sin = t[t["es_correspondencia"]], t[~t["es_correspondencia"]]
    return {
        "universo": nombre, "estaciones": len(t), "correspondencias": len(con),
        "corresp_en_top10_tasa": k10, "esperadas_top10": round(10 * len(con) / len(t), 1),
        "corresp_en_top20_tasa": k20, "esperadas_top20": round(20 * len(con) / len(t), 1),
        "mediana_tasa_corresp": round(con["tasa_denuncias_mm"].median(), 2),
        "mediana_tasa_sin_corresp": round(sin["tasa_denuncias_mm"].median(), 2),
        "tasa_conjunta_corresp": round(1e6 * con["robos_denunciados"].sum() / con["entradas"].sum(), 2),
        "tasa_conjunta_sin_corresp": round(1e6 * sin["robos_denunciados"].sum() / sin["entradas"].sum(), 2),
        "falla": bool(k10 >= C2_TOP10 or k20 >= C2_TOP20),
    }


def c3(panel: pd.DataFrame, den: pd.DataFrame) -> pd.DataFrame:
    red = panel.groupby("anio_mes").agg(entradas=("entradas", "sum"),
                                        robos_denunciados_asignados=("robos_denunciados_total", "sum")).reset_index()
    # A nivel red no hace falta estación: se cuentan TODAS las carpetas de la ventana, con
    # o sin coordenadas, porque la falta de coordenadas crece de 2022 a 2024.
    todas = den.groupby("anio_mes").size().rename("robos_denunciados").reset_index()
    red = red.merge(todas, on="anio_mes", how="left").fillna({"robos_denunciados": 0})
    red["tasa_denuncias_mm"] = 1e6 * red["robos_denunciados"] / red["entradas"]
    red["tasa_denuncias_mm_solo_asignados"] = 1e6 * red["robos_denunciados_asignados"] / red["entradas"]
    return red


def figura_c3(red: pd.DataFrame) -> None:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    x = pd.to_datetime(red["anio_mes"])
    fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    ax[0].plot(x, red["entradas"] / 1e6, color="#33658a")
    ax[0].set_ylabel("Entradas a la red\n(millones al mes)")
    ax[1].plot(x, red["robos_denunciados"], color="#555555")
    ax[1].set_ylabel("Robos denunciados\n(carpetas al mes)")
    ax[2].plot(x, red["tasa_denuncias_mm"], color="#b3412c", label="todas las carpetas")
    ax[2].plot(x, red["tasa_denuncias_mm_solo_asignados"], color="#b3412c", alpha=0.4, ls="--", label="solo las asignadas a estación")
    ax[2].set_ylabel("Robos denunciados por\nmillón de entradas")
    ax[2].legend(frameon=False, fontsize=8)
    for a in ax:
        a.axvspan(pd.Timestamp("2020-03-23"), pd.Timestamp("2021-12-31"), color="#dddddd", alpha=0.5, lw=0)
        a.set_ylim(bottom=0)
        a.spines[["top", "right"]].set_visible(False)
    ax[0].set_title("C3. ¿La tasa de denuncias se sostuvo cuando cayó la afluencia? Red del Metro, 2019–2024\n"
                    "(sombreado: marzo de 2020 a diciembre de 2021)", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "c3_tasa_red_vs_afluencia.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 5))
    periodo = pd.cut(x.dt.year, [2018, 2019, 2021, 2024], labels=["2019", "2020–2021", "2022–2024"])
    for p, c in zip(["2019", "2020–2021", "2022–2024"], ["#33658a", "#b3412c", "#777777"]):
        m = periodo == p
        ax.scatter(red.loc[m, "entradas"] / 1e6, red.loc[m, "robos_denunciados"], color=c, label=p, s=22)
    ax.set_xlabel("Entradas a la red (millones al mes)")
    ax.set_ylabel("Robos denunciados (carpetas al mes)")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("C3. Si la exposición fuera lineal, los puntos caerían\nsobre una recta que pasa por el origen", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "c3_denuncias_vs_entradas.png", dpi=150)
    plt.close(fig)


def main() -> int:
    panel = pd.read_csv(PANEL, dtype={"lineas": str})
    den = pd.read_csv(DENUNCIAS)
    TABLAS.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)

    t = tasas_por_estacion(panel)
    t.to_csv(TABLAS / "c1_tasas_por_estacion.csv", index=False)
    universos = {
        "todas": t,
        "solo CDMX": tasas_por_estacion(panel[~panel["fuera_cdmx"]]),
        "30 o más robos denunciados": tasas_por_estacion(panel[panel["estacion"].isin(t.loc[t["robos_denunciados"] >= 30, "estacion"])]),
    }

    # ------------------------------------------------------------------ C1
    print("=" * 100, "\nC1. Aritmética del titular\n")
    tasa_red = 1e6 * t["robos_denunciados"].sum() / t["entradas"].sum()
    print(f"Tasa de la red: {tasa_red:.2f} robos denunciados por millón de entradas "
          f"({t['robos_denunciados'].sum():,} / {t['entradas'].sum() / 1e6:,.0f} M). "
          f"Mediana entre estaciones: {t['tasa_denuncias_mm'].median():.2f}.")
    cols = ["posicion_conteo", "estacion", "lineas", "es_correspondencia", "robos_denunciados", "entradas",
            "tasa_denuncias_mm", "posicion_tasa", "cambio_de_posicion"]
    top20 = t.head(20)[cols].assign(entradas=lambda d: (d["entradas"] / 1e6).round(1), tasa_denuncias_mm=lambda d: d["tasa_denuncias_mm"].round(2))
    print("\nLas 20 primeras por conteo (entradas en millones):\n", top20.to_string(index=False))
    top20.to_csv(TABLAS / "c1_top20_por_conteo.csv", index=False)
    top20t = t.sort_values("posicion_tasa").head(20)[cols].assign(entradas=lambda d: (d["entradas"] / 1e6).round(1), tasa_denuncias_mm=lambda d: d["tasa_denuncias_mm"].round(2))
    print("\nLas 20 primeras por tasa:\n", top20t.to_string(index=False))
    top20t.to_csv(TABLAS / "c1_top20_por_tasa.csv", index=False)
    r1 = pd.DataFrame([c1(u, n) for n, u in universos.items()])
    print("\n", r1.to_string(index=False))
    r1.to_csv(TABLAS / "c1_resultado.csv", index=False)
    if r1.loc[0, "falla"]:
        print("\nC1 FALLA: el orden por tasa es casi el orden por conteo. El conteo basta. Se para aquí.")
        return 2
    print("\nC1 pasa.")

    # ------------------------------------------------------------------ C2
    print("\n" + "=" * 100, "\nC2. Contaminación del denominador\n")
    r2 = pd.DataFrame([c2(u, n) for n, u in universos.items()])
    print(r2.T.to_string(header=False))
    r2.to_csv(TABLAS / "c2_resultado.csv", index=False)
    por_lineas = t.groupby(t["lineas"].str.count(r"\|") + 1).agg(
        estaciones=("estacion", "size"), robos_denunciados=("robos_denunciados", "sum"), entradas=("entradas", "sum"),
        mediana_tasa=("tasa_denuncias_mm", "median"))
    por_lineas["tasa_conjunta"] = 1e6 * por_lineas["robos_denunciados"] / por_lineas["entradas"]
    por_lineas.index.name = "lineas_en_la_estacion"
    print("\nPor número de líneas que pasan por la estación:\n", por_lineas.round(2).to_string())
    por_lineas.to_csv(TABLAS / "c2_por_numero_de_lineas.csv")
    if r2.loc[0, "falla"]:
        print("\nC2 FALLA: las correspondencias copan la cabeza del orden por tasa. Se está midiendo el "
              "torniquete, no el riesgo. No se intenta arreglar. Se para aquí.")
        return 2
    print("\nC2 pasa.")

    # ------------------------------------------------------------------ C3
    print("\n" + "=" * 100, "\nC3. Exposición lineal, prueba natural 2020-2021\n")
    red = c3(panel, den)
    red.to_csv(TABLAS / "c3_red_mensual.csv", index=False)
    figura_c3(red)
    anio = red["anio_mes"].str[:4].astype(int)
    por_anio = red.groupby(anio).agg(entradas=("entradas", "sum"), robos_denunciados=("robos_denunciados", "sum"))
    por_anio["tasa_denuncias_mm"] = 1e6 * por_anio["robos_denunciados"] / por_anio["entradas"]
    por_anio["entradas_vs_2019"] = por_anio["entradas"] / por_anio.loc[2019, "entradas"]
    por_anio["denuncias_vs_2019"] = por_anio["robos_denunciados"] / por_anio.loc[2019, "robos_denunciados"]
    por_anio["tasa_vs_2019"] = por_anio["tasa_denuncias_mm"] / por_anio.loc[2019, "tasa_denuncias_mm"]
    print(por_anio.round(3).to_string())
    por_anio.to_csv(TABLAS / "c3_por_anio.csv")
    print("\nCorrelación de Spearman entre la tasa mensual y las entradas mensuales: "
          f"{spearman(red['tasa_denuncias_mm'], red['entradas']):.2f} (72 meses)")
    peor = red[red["anio_mes"].between("2020-04", "2020-06")]
    print(f"Abril a junio de 2020: entradas al {100 * peor['entradas'].sum() / red[red['anio_mes'].between('2019-04', '2019-06')]['entradas'].sum():.0f} % "
          f"de las del mismo trimestre de 2019; tasa {1e6 * peor['robos_denunciados'].sum() / peor['entradas'].sum():.2f} contra "
          f"{1e6 * red[red['anio_mes'].between('2019-04', '2019-06')]['robos_denunciados'].sum() / red[red['anio_mes'].between('2019-04', '2019-06')]['entradas'].sum():.2f}.")
    print(f"\nFiguras → {FIGURAS.relative_to(FIGURAS.parents[2])}/c3_*.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())

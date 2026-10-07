#!/usr/bin/env python3
"""Diagnóstico de la falla de C2: ¿el orden por tasa mide dónde se PUEDE DENUNCIAR?

Hipótesis de trabajo: las estaciones con agencia del Ministerio Público del Metro
(Hidalgo, Pantitlán, Observatorio, y Guerrero por la agencia de Zarco y Violeta) tienen
tasas infladas porque ahí es más fácil denunciar. Sin modelo: tasas, razones y tablas.

T0  agencias con vigencia medida en las carpetas → datos/procesados/agencias_mp_metro.csv
T1  Observatorio (agencia, sin correspondencia) contra las estaciones sin correspondencia
T2  comparaciones emparejadas, con todos los canales y solo con Denuncia Digital
T3  2×2 agencia × correspondencia
T4  razón agencia / sin agencia por año, y peso de la Denuncia Digital por año
T7  cota: cuántos transbordos harían falta para igualar las tasas

Los criterios están en docs/decisiones.md (núm. 19), escritos antes de correr esto.
Código de salida 2 = punto de paro 1: el efecto agencia NO queda establecido.
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comun import AGENCIAS, AGENCIAS_CSV, CARPETAS, DENUNCIAS, FIGURAS, FUENTE_DD, FUENTE_FGJ, PANEL, TABLAS

CON_AGENCIA = [a["estacion"] for a in AGENCIAS if a["cuenta_como_agencia"]]

# Controles de T2, elegidos a mano (decisión 21). Cada uno con su razón.
PARES: dict[str, dict] = {
    "Hidalgo": {
        "ventana": ("2019-01", "2024-12"),
        "controles": {
            "Bellas Artes": "correspondencia de dos líneas, a una estación por la L2, mismo centro, entradas casi iguales (79.9 M contra 75.7 M)",
            "Balderas": "correspondencia de dos líneas, comparte la L3, centro, 58.1 M",
            "Salto del Agua": "correspondencia de dos líneas, centro, 51.0 M",
            "Pino Suárez": "correspondencia de dos líneas, comparte la L2, centro, 93.7 M. OJO: hoy tiene agencia según la FGJ, sin fecha; control posiblemente contaminado",
        },
    },
    "Guerrero": {
        "ventana": ("2019-01", "2024-12"),
        "controles": {
            "Garibaldi/Lagunilla": "correspondencia de dos líneas, a una estación por la LB, misma zona, 45.2 M",
            "Morelos": "correspondencia de dos líneas, comparte la LB, centro-oriente, 23.2 M",
            "Oceanía": "correspondencia de dos líneas, comparte la LB, 33.3 M; zona distinta (oriente), se incluye para no escoger solo controles de tasa baja",
            "Jamaica": "correspondencia de dos líneas, centro-oriente, 32.7 M",
        },
    },
    "Pantitlán": {
        "ventana": ("2019-01", "2024-12"),
        "controles": {
            "Tacubaya": "la única otra correspondencia de tres o más líneas con terminal; 142.7 M, la segunda de la red. Es el menos malo",
            "Chabacano": "correspondencia de tres líneas; 68.8 M, fuera de la regla de entradas: se incluye porque no hay más con tres líneas",
            "San Lázaro": "correspondencia del oriente con terminal de autobuses (TAPO), comparte la L1; 62.3 M, fuera de la regla de entradas",
        },
    },
    "Observatorio": {
        "ventana": ("2019-01", "2019-08"),  # mientras operó su agencia
        "controles": {
            "Tasqueña": "terminal de una línea con terminal de autobuses foráneos, como Observatorio",
            "Universidad": "terminal de una línea con paradero grande",
            "Barranca del Muerto": "terminal de una línea, también en el poniente",
        },
    },
}


def byar(d: float, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de Poisson para un conteo d, aproximación de Byar."""
    if d == 0:
        return 0.0, 3.69
    lo = d * (1 - 1 / (9 * d) - z / (3 * np.sqrt(d))) ** 3
    hi = (d + 1) * (1 - 1 / (9 * (d + 1)) + z / (3 * np.sqrt(d + 1))) ** 3
    return max(lo, 0.0), hi


def tasas(panel: pd.DataFrame, desde: str, hasta: str, num: str = "robos_denunciados_total") -> pd.DataFrame:
    p = panel[panel["anio_mes"].between(desde, hasta) & (panel["entradas"] > 0)]
    t = p.groupby("estacion").agg(robos_denunciados=(num, "sum"), entradas=("entradas", "sum"),
                                  es_correspondencia=("es_correspondencia", "first"), fuera_cdmx=("fuera_cdmx", "first"))
    t["tasa_denuncias_mm"] = 1e6 * t["robos_denunciados"] / t["entradas"]
    ic = t["robos_denunciados"].map(byar)
    t["ic95_inf"] = [1e6 * a / e for (a, _), e in zip(ic, t["entradas"])]
    t["ic95_sup"] = [1e6 * b / e for (_, b), e in zip(ic, t["entradas"])]
    return t


def t0(den: pd.DataFrame) -> None:
    c = pd.read_csv(CARPETAS, dtype=str, usecols=["fecha_inicio", "agencia"])
    c = c[c["agencia"].fillna("").str.startswith("STCM")]
    act = c.groupby("agencia")["fecha_inicio"].agg(primera_carpeta_cualquier_delito=lambda s: s.str[:10].min(),
                                                   ultima_carpeta_cualquier_delito=lambda s: s.str[:10].max(),
                                                   carpetas_cualquier_delito_2016_2025="size")
    por_anio = pd.crosstab(c["agencia"], c["fecha_inicio"].str[:4]).add_prefix("carpetas_")
    filas = []
    for a in AGENCIAS:
        f = dict(a)
        f["fuentes"] = f["fuentes"].replace("FGJ", FUENTE_FGJ).replace("DD", FUENTE_DD)
        f["fecha_de_consulta"] = "2026-09-20"
        if a["clave"]:
            f.update(act.loc[a["clave"]].to_dict())
            f.update(por_anio.loc[a["clave"]].to_dict())
            f["robos_a_bordo_del_metro_abiertos_2019_2024"] = int((den["agencia"] == a["clave"]).sum())
        filas.append(f)
    ag = pd.DataFrame(filas)
    ag.to_csv(AGENCIAS_CSV, index=False)
    print("T0. Agencias del Ministerio Público del Metro\n")
    cols = ["clave", "estacion", "ubicacion", "desde", "hasta", "cuenta_como_agencia", "ultima_carpeta_cualquier_delito",
            "robos_a_bordo_del_metro_abiertos_2019_2024"]
    print(ag[cols].to_string(index=False))
    print("\nCarpetas de cualquier delito por año de inicio:\n", por_anio.to_string())
    ob = act.loc["STCMOB", "ultima_carpeta_cualquier_delito"]
    assert ob[:7] == "2019-08", f"la vigencia escrita para STCMOB no coincide con los datos: {ob}"
    print(f"\n  STCMOB (Observatorio): última carpeta {ob}. Dejó de operar a mitad del periodo → variación temporal.")
    print("  Ninguna fuente oficial da fechas de apertura o cierre; todas las claves menos STCMOB abren carpetas de 2016 a 2025.")
    print(f"  → {AGENCIAS_CSV.relative_to(AGENCIAS_CSV.parents[2])}")


def canales(den: pd.DataFrame) -> None:
    print("\n" + "=" * 100 + "\nCanal por el que entró la denuncia (todas las carpetas de la ventana, asignadas o no)\n")
    x = pd.crosstab(den["canal"], den["fecha"].str[:4], margins=True)
    print(x.to_string())
    x.to_csv(TABLAS / "agencias_canal_por_anio.csv")
    a = den[den["asignada"]]
    print("\n¿La coordenada de la carpeta es el lugar del hecho o la agencia? Carpetas que abrió cada agencia "
          "del Metro, según la estación donde cae su coordenada:")
    filas = []
    for ag in AGENCIAS:
        if not ag["clave"]:
            continue
        g = a[a["canal"] == ag["clave"]]
        if len(g) == 0:
            continue
        filas.append({"agencia": ag["clave"], "estacion_sede": ag["estacion"], "robos_denunciados_asignados": len(g),
                      "en_la_estacion_sede": int((g["estacion_mas_cercana"] == ag["estacion"]).sum()),
                      "pct_en_la_sede": round(100 * (g["estacion_mas_cercana"] == ag["estacion"]).mean(), 1),
                      "estaciones_distintas": g["estacion_mas_cercana"].nunique()})
    r = pd.DataFrame(filas)
    print(r.to_string(index=False))
    r.to_csv(TABLAS / "agencias_donde_caen_sus_carpetas.csv", index=False)


def t1(panel: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    print("\n" + "=" * 100 + "\nT1. Observatorio contra las estaciones sin correspondencia (dentro de la CDMX)\n")
    o = panel[panel["estacion"] == "Observatorio"].groupby("anio").agg(entradas=("entradas", "sum"),
                                                                        robos_denunciados=("robos_denunciados_total", "sum"))
    print("Afluencia de Observatorio por año (cae a cero desde 2023-12: cierre del tramo poniente de la L1):\n", o.to_string())
    filas = []
    for nombre, (d, h) in {"(a) 2019-01 a 2019-08, con agencia": ("2019-01", "2019-08"),
                           "(b) 2019-09 a 2021-12, sin agencia": ("2019-09", "2021-12"),
                           "(c) 2019 a 2021, la del encargo": ("2019-01", "2021-12")}.items():
        t = tasas(panel, d, h)
        ref = t[~t["es_correspondencia"] & ~t["fuera_cdmx"]]
        ob = ref.loc["Observatorio"]
        otras = ref.drop(index="Observatorio")["tasa_denuncias_mm"]
        filas.append({"ventana": nombre, "robos_denunciados": int(ob["robos_denunciados"]),
                      "entradas_M": round(ob["entradas"] / 1e6, 1), "tasa_denuncias_mm": round(ob["tasa_denuncias_mm"], 2),
                      "ic95": f"{ob['ic95_inf']:.2f} a {ob['ic95_sup']:.2f}",
                      "percentil_entre_las_sin_correspondencia": round(100 * (otras < ob["tasa_denuncias_mm"]).mean(), 1),
                      "n_referencia": len(otras), "mediana_referencia": round(otras.median(), 2),
                      "p90_referencia": round(otras.quantile(0.9), 2)})
    r = pd.DataFrame(filas)
    print("\n", r.to_string(index=False))
    r.to_csv(TABLAS / "t1_observatorio.csv", index=False)
    anomalia = bool(r.loc[0, "percentil_entre_las_sin_correspondencia"] > 90)
    print(f"\nT1: {'HAY' if anomalia else 'NO hay'} anomalía en Observatorio (criterio: arriba del percentil 90 en la ventana (a)).")
    return r, anomalia


def t2(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    print("\n" + "=" * 100 + "\nT2. Comparaciones emparejadas\n")
    filas = []
    for est, cfg in PARES.items():
        d, h = cfg["ventana"]
        todos = tasas(panel, d, h)
        dig = tasas(panel, max(d, "2020-01"), h, "robos_denunciados_canal_digital") if h >= "2020-01" else None
        for rol, e, razon in [("con agencia", est, "")] + [("control", c, r) for c, r in cfg["controles"].items()]:
            f = {"grupo": est, "ventana": f"{d} a {h}", "rol": rol, "estacion": e,
                 "robos_denunciados": int(todos.loc[e, "robos_denunciados"]), "entradas_M": round(todos.loc[e, "entradas"] / 1e6, 1),
                 "tasa_denuncias_mm": round(todos.loc[e, "tasa_denuncias_mm"], 2),
                 "ic95": f"{todos.loc[e, 'ic95_inf']:.2f} a {todos.loc[e, 'ic95_sup']:.2f}"}
            if dig is not None:
                f["robos_denunciados_digital_2020_2024"] = int(dig.loc[e, "robos_denunciados"])
                f["tasa_denuncias_mm_solo_digital"] = round(dig.loc[e, "tasa_denuncias_mm"], 2)
            f["por_que_este_control"] = razon
            filas.append(f)
    det = pd.DataFrame(filas)
    print(det.drop(columns="por_que_este_control").to_string(index=False))
    det.to_csv(TABLAS / "t2_pares_detalle.csv", index=False)

    res = []
    for est, g in det.groupby("grupo", sort=False):
        a, c = g[g["rol"] == "con agencia"].iloc[0], g[g["rol"] == "control"]
        f = {"estacion_con_agencia": est, "tasa": a["tasa_denuncias_mm"], "mediana_controles": round(c["tasa_denuncias_mm"].median(), 2),
             "razon_todos_los_canales": round(a["tasa_denuncias_mm"] / c["tasa_denuncias_mm"].median(), 2)}
        if "tasa_denuncias_mm_solo_digital" in g and pd.notna(a.get("tasa_denuncias_mm_solo_digital")):
            f["tasa_solo_digital"] = a["tasa_denuncias_mm_solo_digital"]
            f["mediana_controles_solo_digital"] = round(c["tasa_denuncias_mm_solo_digital"].median(), 2)
            f["razon_solo_digital"] = round(a["tasa_denuncias_mm_solo_digital"] / c["tasa_denuncias_mm_solo_digital"].median(), 2)
        f["anomalia"] = f["razon_todos_los_canales"] >= 2
        f["persiste_en_digital"] = bool(f.get("razon_solo_digital", np.nan) >= 2) if f["anomalia"] else None
        res.append(f)
    res = pd.DataFrame(res)
    print("\nResumen (anomalía: razón ≥ 2; atribuible a la agencia solo si NO persiste en el canal digital):\n", res.to_string(index=False))
    res.to_csv(TABLAS / "t2_pares_resumen.csv", index=False)
    return det, res


def canal_por_estacion(den: pd.DataFrame) -> None:
    print("\nSi tener la agencia a la mano hiciera denunciar más, en su estación sede pesaría más el canal "
          "«agencia del Metro». Composición por canal de los robos denunciados en cada estación:")
    a = den[den["asignada"]].copy()
    a["canal3"] = np.where(a["canal"].str.startswith("STCM"), "agencia del Metro", a["canal"])
    ests = [e for est, cfg in PARES.items() for e in [est, *cfg["controles"]]]
    x = pd.crosstab(a["estacion_mas_cercana"], a["canal3"]).loc[ests]
    x["total"] = x.sum(axis=1)
    for c in ["agencia del Metro", "DIGITAL", "otra agencia"]:
        x[f"pct_{c}"] = (100 * x[c] / x["total"]).round(1)
    x.insert(0, "rol", ["CON AGENCIA" if e in PARES else "control" for e in ests])
    print(x.to_string())
    x.to_csv(TABLAS / "agencias_canal_por_estacion.csv")
    red = a["canal3"].value_counts(normalize=True).mul(100).round(1).to_dict()
    print("Toda la red:", red)


def t3(panel: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 100 + "\nT3. Estratificación 2×2, agencia × correspondencia (2019–2024; Observatorio cuenta como «con agencia» "
          "aunque solo la tuvo ocho meses)\n")
    out = []
    for nombre, p in {"todas": panel, "solo CDMX": panel[~panel["fuera_cdmx"]]}.items():
        t = tasas(p, "2019-01", "2024-12")
        t["agencia"] = t.index.isin(CON_AGENCIA)
        total_den, total_ent = t["robos_denunciados"].sum(), t["entradas"].sum()
        for (ag, co), g in t.groupby(["agencia", "es_correspondencia"]):
            out.append({"universo": nombre, "agencia": "sí" if ag else "no", "correspondencia": "sí" if co else "no",
                        "n_estaciones": len(g), "estaciones": ", ".join(g.index) if len(g) <= 4 else "",
                        "robos_denunciados": int(g["robos_denunciados"].sum()),
                        "pct_de_los_robos_denunciados": round(100 * g["robos_denunciados"].sum() / total_den, 1),
                        "pct_de_las_entradas": round(100 * g["entradas"].sum() / total_ent, 1),
                        "tasa_conjunta": round(1e6 * g["robos_denunciados"].sum() / g["entradas"].sum(), 2),
                        "mediana_de_tasas": round(g["tasa_denuncias_mm"].median(), 2)})
    r = pd.DataFrame(out)
    print(r.to_string(index=False))
    r.to_csv(TABLAS / "t3_dos_por_dos.csv", index=False)
    return r


def t4(panel: pd.DataFrame, den: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 100 + "\nT4. ¿El exceso de las estaciones con agencia se diluye con los años?\n")
    p = panel[panel["entradas"] > 0].copy()
    p["grupo"] = np.select(
        [p["estacion"].isin(["Hidalgo", "Guerrero"]), p["estacion"].eq("Pantitlán"), p["es_correspondencia"]],
        ["Hidalgo y Guerrero", "Pantitlán", "otras correspondencias"], "sin correspondencia")
    g = p.groupby(["anio", "grupo"]).agg(d=("robos_denunciados_total", "sum"), e=("entradas", "sum"))
    tasa = (1e6 * g["d"] / g["e"]).unstack()
    r = pd.DataFrame({
        "tasa_hidalgo_y_guerrero": tasa["Hidalgo y Guerrero"], "tasa_pantitlan": tasa["Pantitlán"],
        "tasa_otras_correspondencias": tasa["otras correspondencias"], "tasa_sin_correspondencia": tasa["sin correspondencia"],
        "razon_hidalgo_guerrero_vs_otras_corresp": tasa["Hidalgo y Guerrero"] / tasa["otras correspondencias"],
        "razon_pantitlan_vs_otras_corresp": tasa["Pantitlán"] / tasa["otras correspondencias"],
        "razon_corresp_vs_sin_corresp": (g["d"].unstack()[["Hidalgo y Guerrero", "Pantitlán", "otras correspondencias"]].sum(axis=1)
                                         / g["e"].unstack()[["Hidalgo y Guerrero", "Pantitlán", "otras correspondencias"]].sum(axis=1))
                                        * 1e6 / tasa["sin correspondencia"],
    })
    anio = den["fecha"].str[:4].astype(int)
    r["pct_denuncia_digital_red"] = (100 * den["canal"].eq("DIGITAL").groupby(anio).mean())
    r["pct_agencias_del_metro_red"] = (100 * den["canal"].str.startswith("STCM").groupby(anio).mean())
    print(r.round(2).to_string())
    r.to_csv(TABLAS / "t4_por_anio.csv")

    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ax[0].plot(r.index, r["razon_hidalgo_guerrero_vs_otras_corresp"], marker="o", color="#b3412c", label="Hidalgo y Guerrero")
    ax[0].plot(r.index, r["razon_pantitlan_vs_otras_corresp"], marker="o", color="#33658a", label="Pantitlán")
    ax[0].axhline(1, color="#999999", lw=0.8)
    ax[0].set_ylabel("Razón de tasas de robos denunciados\ncontra las otras 25 correspondencias")
    ax[0].set_ylim(bottom=0)
    ax[0].legend(frameon=False)
    ax[0].set_title("T4. El exceso de las estaciones con agencia, por año", fontsize=10, loc="left")
    ax[1].plot(r.index, r["pct_denuncia_digital_red"], marker="o", color="#555555", label="Denuncia Digital")
    ax[1].plot(r.index, r["pct_agencias_del_metro_red"], marker="o", color="#b3412c", label="agencias del Metro")
    ax[1].set_ylabel("% de los robos denunciados de la red")
    ax[1].set_ylim(0, 100)
    ax[1].legend(frameon=False)
    ax[1].set_title("Por dónde entra la denuncia\n(Denuncia Digital opera desde el 6 de diciembre de 2019)", fontsize=10, loc="left")
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "t4_razon_agencia_por_anio.png", dpi=150)
    plt.close(fig)
    return r


def t7(panel: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 100 + "\nT7. Cota: ¿cuántos transbordos harían falta para que la tasa de las correspondencias bajara a la "
          "de las estaciones de paso?\n")
    t = tasas(panel[~panel["fuera_cdmx"]], "2019-01", "2024-12")
    paso = t[~t["es_correspondencia"]]
    r0 = 1e6 * paso["robos_denunciados"].sum() / paso["entradas"].sum()
    c = t[t["es_correspondencia"]].copy()
    # denuncias / (entradas + T) = r0  →  T = denuncias / r0 − entradas
    c["transbordos_necesarios_M"] = (c["robos_denunciados"] / r0 * 1e6 - c["entradas"]) / 1e6
    c["como_multiplo_de_sus_entradas"] = c["transbordos_necesarios_M"] * 1e6 / c["entradas"]
    tot = c["transbordos_necesarios_M"].clip(lower=0).sum()
    print(f"Tasa conjunta de las estaciones sin correspondencia (CDMX): {r0:.2f} por millón de entradas.")
    print(f"Conjunto de las 28 correspondencias: tasa {1e6 * c['robos_denunciados'].sum() / c['entradas'].sum():.2f}; harían falta "
          f"{(c['robos_denunciados'].sum() / r0 * 1e6 - c['entradas'].sum()) / 1e6:,.0f} M de transbordos en seis años = "
          f"{(c['robos_denunciados'].sum() / r0 * 1e6 - c['entradas'].sum()) / c['entradas'].sum():.2f} veces sus entradas "
          f"= {100 * (c['robos_denunciados'].sum() / r0 * 1e6 - c['entradas'].sum()) / t['entradas'].sum():.0f} % de las entradas de toda la red (CDMX).")
    s = c.sort_values("como_multiplo_de_sus_entradas", ascending=False)[
        ["robos_denunciados", "entradas", "tasa_denuncias_mm", "transbordos_necesarios_M", "como_multiplo_de_sus_entradas"]]
    s["entradas"] = (s["entradas"] / 1e6).round(1)
    print(s.round(2).to_string())
    s.round(3).to_csv(TABLAS / "t7_transbordos_necesarios.csv")
    print(f"(suma de los positivos: {tot:,.0f} M)")
    return s


def main() -> int:
    panel = pd.read_csv(PANEL, dtype={"lineas": str})
    den = pd.read_csv(DENUNCIAS, dtype={"agencia": str, "fiscalia": str, "fecha": str})
    TABLAS.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)

    t0(den)
    canales(den)
    _, anomalia_t1 = t1(panel)
    _, res = t2(panel)
    canal_por_estacion(den)
    t3(panel)
    t4(panel, den)
    t7(panel)

    print("\n" + "=" * 100 + "\nPUNTO DE PARO 1\n")
    con_anomalia = res[res["anomalia"]]
    atribuibles = con_anomalia[con_anomalia["persiste_en_digital"] == False]  # noqa: E712
    print(f"T1: anomalía en Observatorio = {anomalia_t1}.")
    print(f"T2: anomalía en {list(con_anomalia['estacion_con_agencia'])}; "
          f"de esas, el exceso desaparece en el canal digital (atribuible a la agencia) en {list(atribuibles['estacion_con_agencia'])}.")
    if not anomalia_t1 and atribuibles.empty:
        print("\nEl efecto agencia NO queda establecido. Se para aquí: no se corren T5, T6, el EDA ni las hipótesis.")
        return 2
    print("\nEl efecto agencia queda establecido al menos en parte; se puede seguir con el estrato limpio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

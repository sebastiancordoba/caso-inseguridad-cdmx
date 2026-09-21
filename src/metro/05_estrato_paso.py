#!/usr/bin/env python3
"""Compuerta T5: en las estaciones de paso de la CDMX, ¿conteo y tasa ordenan distinto? Y C3.

Estrato (a): estaciones sin correspondencia y dentro de la CDMX (124). Sin filtro de
agencia. Numerador: DENUNCIAS por fecha del hecho, 2019–2024, asignadas a la estación más
cercana dentro del umbral (150 m; sensibilidad con 100 y 250 m). Denominador: entradas en
los meses en que la estación estuvo abierta.

Criterio de falla (decisión 25): Spearman ≥ 0.9 Y nueve o más coincidencias en los top-10.
Código de salida 2 si falla con el umbral de 150 m y sin mínimo de denuncias.

C3 (decisión 28): tasa mensual de la red y del estrato contra entradas mensuales.
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comun import DENUNCIAS, FIGURAS, PANEL, TABLAS

C_RHO, C_COINCIDENCIAS = 0.9, 9


def byar(d: float, z: float = 1.96) -> tuple[float, float]:
    if d == 0:
        return 0.0, 3.69
    return (max(d * (1 - 1 / (9 * d) - z / (3 * np.sqrt(d))) ** 3, 0.0),
            (d + 1) * (1 - 1 / (9 * (d + 1)) + z / (3 * np.sqrt(d + 1))) ** 3)


def spearman(a: pd.Series, b: pd.Series) -> float:
    return a.rank().corr(b.rank())


def ranking(panel: pd.DataFrame, den: pd.DataFrame, umbral_m: int, minimo: int = 0) -> pd.DataFrame:
    """Conteo y tasa por estación del estrato (a), con el numerador rehecho al umbral dado."""
    base = panel[~panel["es_correspondencia"] & ~panel["fuera_cdmx"] & (panel["entradas"] > 0)]
    d = den[den["distancia_m"].le(umbral_m)].groupby(["estacion_mas_cercana", "anio_mes"]).size().rename("n").reset_index()
    p = base.merge(d, left_on=["estacion", "anio_mes"], right_on=["estacion_mas_cercana", "anio_mes"], how="left")
    t = p.groupby("estacion").agg(lineas=("lineas", "first"), robos_denunciados=("n", "sum"), entradas=("entradas", "sum"),
                                  meses_abierta=("anio_mes", "nunique")).reset_index()
    t["robos_denunciados"] = t["robos_denunciados"].astype(int)
    t = t[t["robos_denunciados"] >= minimo].copy()
    t["tasa_denuncias_mm"] = 1e6 * t["robos_denunciados"] / t["entradas"]
    ic = t["robos_denunciados"].map(byar)
    t["ic95_inf"] = [1e6 * a / e for (a, _), e in zip(ic, t["entradas"])]
    t["ic95_sup"] = [1e6 * b / e for (_, b), e in zip(ic, t["entradas"])]
    t["posicion_conteo"] = t["robos_denunciados"].rank(ascending=False, method="min").astype(int)
    t["posicion_tasa"] = t["tasa_denuncias_mm"].rank(ascending=False, method="min").astype(int)
    t["cambio_de_posicion"] = t["posicion_conteo"] - t["posicion_tasa"]  # positivo: sube al ordenar por tasa
    tasa_estrato = 1e6 * t["robos_denunciados"].sum() / t["entradas"].sum()
    t["se_distingue_del_estrato"] = np.where(t["ic95_inf"] > tasa_estrato, "arriba",
                                             np.where(t["ic95_sup"] < tasa_estrato, "abajo", "no"))
    t.attrs["tasa_estrato"] = tasa_estrato
    return t.sort_values("posicion_conteo")


def criterio(t: pd.DataFrame) -> dict:
    rho = spearman(t["robos_denunciados"], t["tasa_denuncias_mm"])
    a = set(t.nsmallest(10, "posicion_conteo")["estacion"])
    b = set(t.nsmallest(10, "posicion_tasa")["estacion"])
    return {"estaciones": len(t), "robos_denunciados": int(t["robos_denunciados"].sum()),
            "tasa_del_estrato": round(t.attrs["tasa_estrato"], 3), "spearman": round(rho, 3),
            "coincidencias_top10": len(a & b), "falla": bool(rho >= C_RHO and len(a & b) >= C_COINCIDENCIAS)}


def bonita(t: pd.DataFrame) -> pd.DataFrame:
    o = t[["estacion", "lineas", "robos_denunciados", "entradas", "tasa_denuncias_mm", "ic95_inf", "ic95_sup",
           "posicion_conteo", "posicion_tasa", "cambio_de_posicion", "se_distingue_del_estrato"]].copy()
    o["entradas"] = (o["entradas"] / 1e6).round(1)
    return o.round({"tasa_denuncias_mm": 2, "ic95_inf": 2, "ic95_sup": 2}).rename(columns={"entradas": "entradas_M"})


def t5(panel: pd.DataFrame, den: pd.DataFrame) -> bool:
    print("T5. Estrato (a): estaciones sin correspondencia dentro de la CDMX\n")
    t = ranking(panel, den, 150)
    t.to_csv(TABLAS / "t5_estrato_paso.csv", index=False)
    print(f"Tasa conjunta del estrato: {t.attrs['tasa_estrato']:.2f} robos denunciados por millón de entradas "
          f"({t['robos_denunciados'].sum():,} / {t['entradas'].sum() / 1e6:,.0f} M).")
    print(f"Estaciones cuya tasa se distingue de la del estrato: arriba {sum(t['se_distingue_del_estrato'] == 'arriba')}, "
          f"abajo {sum(t['se_distingue_del_estrato'] == 'abajo')}, no se distingue {sum(t['se_distingue_del_estrato'] == 'no')}.")

    res = []
    for umbral in [150, 100, 250]:
        for minimo in [0, 20, 30]:
            r = criterio(ranking(panel, den, umbral, minimo))
            res.append({"umbral_m": umbral, "minimo_de_robos_denunciados": minimo, **r})
    res = pd.DataFrame(res)
    print("\n1 y 4 y 5. Criterio, por umbral de asignación y mínimo de denuncias:\n", res.to_string(index=False))
    res.to_csv(TABLAS / "t5_criterio.csv", index=False)

    print("\n2. Top-15 por conteo:\n", bonita(t.head(15)).to_string(index=False))
    print("\n   Top-15 por tasa:\n", bonita(t.sort_values("posicion_tasa").head(15)).to_string(index=False))
    bonita(t.head(15)).to_csv(TABLAS / "t5_top15_por_conteo.csv", index=False)
    bonita(t.sort_values("posicion_tasa").head(15)).to_csv(TABLAS / "t5_top15_por_tasa.csv", index=False)

    for minimo in [0, 20, 30]:
        tm = ranking(panel, den, 150, minimo)
        sube = tm.sort_values("cambio_de_posicion", ascending=False).head(10)
        baja = tm.sort_values("cambio_de_posicion").head(10)
        print(f"\n3/4. Mínimo de {minimo} robos denunciados ({len(tm)} estaciones; tasa del estrato {tm.attrs['tasa_estrato']:.2f}). "
              "Las 10 que más SUBEN al pasar de conteo a tasa:\n", bonita(sube).to_string(index=False))
        print("    Las 10 que más BAJAN:\n", bonita(baja).to_string(index=False))
        bonita(sube).to_csv(TABLAS / f"t5_suben_min{minimo}.csv", index=False)
        bonita(baja).to_csv(TABLAS / f"t5_bajan_min{minimo}.csv", index=False)

    print("\n5. Sensibilidad al umbral de asignación (contra el ranking de 150 m, sin mínimo):")
    ref = t.set_index("estacion")
    filas = []
    for umbral in [100, 250]:
        o = ranking(panel, den, umbral).set_index("estacion")
        top_ref = set(ref.nsmallest(10, "posicion_tasa").index)
        top_o = set(o.nsmallest(10, "posicion_tasa").index)
        top_ref_c = set(ref.nsmallest(10, "posicion_conteo").index)
        top_o_c = set(o.nsmallest(10, "posicion_conteo").index)
        dist = ref["se_distingue_del_estrato"].ne("no")
        igual = (o.loc[ref.index[dist], "se_distingue_del_estrato"] == ref.loc[dist, "se_distingue_del_estrato"]).sum()
        filas.append({"umbral_m": umbral, "robos_denunciados": int(o["robos_denunciados"].sum()),
                      "spearman_de_tasas_vs_150m": round(spearman(o["tasa_denuncias_mm"], ref["tasa_denuncias_mm"]), 3),
                      "top10_tasa_en_comun": len(top_ref & top_o), "top10_conteo_en_comun": len(top_ref_c & top_o_c),
                      "sale_del_top10_tasa": ", ".join(sorted(top_ref - top_o)), "entra_al_top10_tasa": ", ".join(sorted(top_o - top_ref)),
                      "distinguibles_a_150m_que_siguen_igual": f"{igual} de {int(dist.sum())}"})
    s = pd.DataFrame(filas)
    print(s.to_string(index=False))
    s.to_csv(TABLAS / "t5_sensibilidad_umbral.csv", index=False)

    falla = bool(res.loc[0, "falla"])
    print(f"\nT5 {'FALLA: el conteo basta en el estrato' if falla else 'PASA: conteo y tasa ordenan distinto en el estrato'} "
          f"(Spearman {res.loc[0, 'spearman']}, {res.loc[0, 'coincidencias_top10']} coincidencias en el top-10).")
    return falla


def c3(panel: pd.DataFrame, den: pd.DataFrame) -> None:
    print("\n" + "=" * 100 + "\nC3. Exposición lineal: tasa mensual contra entradas mensuales, 2019–2024\n")
    abiertos = panel[panel["entradas"] > 0]
    red = abiertos.groupby("anio_mes").agg(entradas=("entradas", "sum")).reset_index()
    red = red.merge(den.groupby("anio_mes").size().rename("robos_denunciados").reset_index(), how="left").fillna(0)
    red = red.merge(den[den["asignada"]].groupby("anio_mes").size().rename("robos_denunciados_asignados").reset_index(), how="left").fillna(0)
    a = abiertos[~abiertos["es_correspondencia"] & ~abiertos["fuera_cdmx"]]
    est = a.groupby("anio_mes").agg(entradas=("entradas", "sum"), robos_denunciados=("robos_denunciados_total", "sum")).reset_index()
    series = {"red (todas las carpetas)": red, "estrato (a) (solo carpetas asignadas)": est}
    for s in series.values():
        s["tasa_denuncias_mm"] = 1e6 * s["robos_denunciados"] / s["entradas"]
    red["tasa_denuncias_mm_solo_asignadas"] = 1e6 * red["robos_denunciados_asignados"] / red["entradas"]
    red.to_csv(TABLAS / "c3_red_mensual.csv", index=False)
    est.to_csv(TABLAS / "c3_estrato_paso_mensual.csv", index=False)

    filas = []
    for nombre, s in series.items():
        g = s.groupby(s["anio_mes"].str[:4].astype(int)).agg(entradas=("entradas", "sum"), robos_denunciados=("robos_denunciados", "sum"))
        g["tasa_denuncias_mm"] = 1e6 * g["robos_denunciados"] / g["entradas"]
        for c in ["entradas", "robos_denunciados", "tasa_denuncias_mm"]:
            g[f"{c}_vs_2019"] = g[c] / g.loc[2019, c]
        g.insert(0, "serie", nombre)
        filas.append(g.reset_index())
        dentro = g.loc[[2020, 2021], "tasa_denuncias_mm_vs_2019"].between(0.75, 1.25).all()
        print(f"{nombre}: tasa 2020 = {g.loc[2020, 'tasa_denuncias_mm_vs_2019']:.2f} × la de 2019, 2021 = "
              f"{g.loc[2021, 'tasa_denuncias_mm_vs_2019']:.2f} ×; entradas 2020 = {g.loc[2020, 'entradas_vs_2019']:.2f} ×. "
              f"Exposición lineal {'SE SOSTIENE' if dentro else 'NO se sostiene'} (banda de ±25 %). "
              f"Spearman tasa–entradas mensual: {spearman(s['tasa_denuncias_mm'], s['entradas']):.2f}.")
    por_anio = pd.concat(filas).rename(columns={"anio_mes": "anio"})
    print("\n", por_anio.round(3).to_string(index=False))
    por_anio.to_csv(TABLAS / "c3_por_anio.csv", index=False)
    for nombre, s in series.items():
        q = s[s["anio_mes"].between("2020-04", "2020-06")]
        b = s[s["anio_mes"].between("2019-04", "2019-06")]
        print(f"{nombre}, abril–junio de 2020 contra abril–junio de 2019: entradas {q['entradas'].sum() / b['entradas'].sum():.2f} ×, "
              f"robos denunciados {q['robos_denunciados'].sum() / b['robos_denunciados'].sum():.2f} ×, "
              f"tasa {(q['robos_denunciados'].sum() / q['entradas'].sum()) / (b['robos_denunciados'].sum() / b['entradas'].sum()):.2f} ×.")

    # La gráfica muestra que el quiebre grande ocurre DENTRO de 2019, con la afluencia plana.
    # Por tramos, para separar ese quiebre del efecto de la pandemia (decisión 30).
    tramos = {"2019-01 a 2019-05": ("2019-01", "2019-05"), "2019-09 a 2020-02 (base prepandemia)": ("2019-09", "2020-02"),
              "2020-04 a 2020-06 (confinamiento)": ("2020-04", "2020-06"), "2020-07 a 2021-12": ("2020-07", "2021-12"),
              "2022-01 a 2024-12": ("2022-01", "2024-12")}
    ft = []
    for nombre, s in series.items():
        base = None
        for tramo, (d, h) in tramos.items():
            q = s[s["anio_mes"].between(d, h)]
            tasa = 1e6 * q["robos_denunciados"].sum() / q["entradas"].sum()
            ent = q["entradas"].mean() / 1e6
            if "base" in tramo:
                base = (tasa, ent)
            ft.append({"serie": nombre, "tramo": tramo, "entradas_M_al_mes": round(ent, 1),
                       "robos_denunciados_al_mes": round(q["robos_denunciados"].mean(), 1), "tasa_denuncias_mm": round(tasa, 2)})
        for f in ft:
            if f["serie"] == nombre:
                f["entradas_vs_base"] = round(f["entradas_M_al_mes"] / base[1], 2)
                f["tasa_vs_base"] = round(f["tasa_denuncias_mm"] / base[0], 2)
    ft = pd.DataFrame(ft)
    print("\nPor tramos, contra la base prepandemia (septiembre de 2019 a febrero de 2020):\n", ft.to_string(index=False))
    ft.to_csv(TABLAS / "c3_por_tramos.csv", index=False)

    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(3, 1, figsize=(9, 8.5), sharex=True)
    x = pd.to_datetime(red["anio_mes"])
    ax[0].plot(x, red["entradas"] / 1e6, color="#33658a", label="red")
    ax[0].plot(x, est["entradas"] / 1e6, color="#33658a", ls="--", label="estrato (a): 124 estaciones de paso")
    ax[0].set_ylabel("Entradas\n(millones al mes)")
    ax[1].plot(x, red["robos_denunciados"], color="#555555", label="red, todas las carpetas")
    ax[1].plot(x, est["robos_denunciados"], color="#555555", ls="--", label="estrato (a), carpetas asignadas")
    ax[1].set_ylabel("Robos denunciados\n(carpetas al mes)")
    ax[2].plot(x, red["tasa_denuncias_mm"], color="#b3412c", label="red, todas las carpetas")
    ax[2].plot(x, red["tasa_denuncias_mm_solo_asignadas"], color="#b3412c", alpha=0.35, label="red, solo carpetas asignadas")
    ax[2].plot(x, est["tasa_denuncias_mm"], color="#b3412c", ls="--", label="estrato (a), carpetas asignadas")
    ax[2].set_ylabel("Robos denunciados por\nmillón de entradas")
    for a_ in ax:
        a_.axvspan(pd.Timestamp("2020-03-23"), pd.Timestamp("2021-12-31"), color="#dddddd", alpha=0.5, lw=0)
        a_.set_ylim(bottom=0)
        a_.legend(frameon=False, fontsize=8)
        a_.spines[["top", "right"]].set_visible(False)
    ax[0].set_title("C3. ¿La tasa de denuncias se sostuvo cuando se desplomó la afluencia? Metro de la CDMX, 2019–2024\n"
                    "(sombreado: marzo de 2020 a diciembre de 2021)", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "c3_tasa_vs_afluencia.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    for a_, (nombre, s) in zip(ax, series.items()):
        # Los mismos tramos de la tabla. La recta es la tasa de la BASE prepandemia (2019-09 a
        # 2020-02), no la de 2019 completo: 2019 trae un quiebre propio, con la afluencia plana.
        mes = s["anio_mes"]
        grupos = [("2019-01 a 2019-08: antes del quiebre de 2019", mes.between("2019-01", "2019-08"), "#c9c5b8", "o"),
                  ("2019-09 a 2020-02: base prepandemia", mes.between("2019-09", "2020-02"), "#33658a", "o"),
                  ("2020-03: transición", mes == "2020-03", "#9db7cc", "o"),
                  ("2020-04 a 2020-06: confinamiento", mes.between("2020-04", "2020-06"), "#b3412c", "s"),
                  ("2020-07 a 2021-12", mes.between("2020-07", "2021-12"), "#e08a3c", "o"),
                  ("2022-01 a 2024-12", mes >= "2022-01", "#777777", "o")]
        for etiqueta, m, c, marca in grupos:
            a_.scatter(s.loc[m, "entradas"] / 1e6, s.loc[m, "robos_denunciados"], color=c, s=22, marker=marca, label=etiqueta)
        base = mes.between("2019-09", "2020-02")
        k = s.loc[base, "robos_denunciados"].sum() / s.loc[base, "entradas"].sum()
        xs = np.array([0, s["entradas"].max() / 1e6])
        a_.plot(xs, k * xs * 1e6, color="#33658a", lw=0.9, ls=":", label=f"tasa de la base constante ({1e6 * k:.2f} por millón)")
        a_.set_xlabel("Entradas (millones al mes)")
        a_.set_ylabel("Robos denunciados (carpetas al mes)")
        a_.set_xlim(left=0)
        a_.set_ylim(bottom=0)
        a_.set_title(nombre, fontsize=10, loc="left")
        a_.legend(frameon=False, fontsize=8)
        a_.spines[["top", "right"]].set_visible(False)
    fig.suptitle("C3. Con exposición lineal, los meses caerían sobre la recta punteada (tasa de la base prepandemia)", fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "c3_denuncias_vs_entradas.png", dpi=150)
    plt.close(fig)
    print(f"\nFiguras → {FIGURAS.relative_to(FIGURAS.parents[2])}/c3_tasa_vs_afluencia.png y c3_denuncias_vs_entradas.png")


def por_anio_estandarizado(panel: pd.DataFrame) -> None:
    """Comprobación que C3 obliga (decisión 29): la tasa del estrato cae a la mitad después
    de 2019, así que una estación cerrada en los años de tasa baja (L1, L12) concentra su
    exposición en 2019 y su tasa del periodo sale inflada. Estandarización indirecta por
    año: esperadas = Σ_año entradas de la estación × tasa del estrato ese año. Aritmética."""
    print("\n" + "=" * 100 + "\n6. Comprobación que C3 obliga: ¿el orden por tasa aguanta si se descuenta el año?\n")
    a = panel[~panel["es_correspondencia"] & ~panel["fuera_cdmx"] & (panel["entradas"] > 0)]
    ta = a.groupby("anio").apply(lambda g: g["robos_denunciados_total"].sum() / g["entradas"].sum(), include_groups=False)
    a = a.assign(esperadas=a["entradas"] * a["anio"].map(ta))
    t = a.groupby("estacion").agg(lineas=("lineas", "first"), robos_denunciados=("robos_denunciados_total", "sum"),
                                  entradas=("entradas", "sum"), robos_denunciados_esperados=("esperadas", "sum"),
                                  pct_entradas_en_2019=("entradas", lambda x: 0.0)).reset_index()
    e19 = a[a["anio"] == 2019].groupby("estacion")["entradas"].sum()
    t["pct_entradas_en_2019"] = (100 * t["estacion"].map(e19).fillna(0) / t["entradas"]).round(1)
    t["tasa_denuncias_mm"] = 1e6 * t["robos_denunciados"] / t["entradas"]
    t["razon_observadas_esperadas"] = t["robos_denunciados"] / t["robos_denunciados_esperados"]
    ic = t["robos_denunciados"].map(byar)
    t["razon_ic95_inf"] = [lo / e for (lo, _), e in zip(ic, t["robos_denunciados_esperados"])]
    t["razon_ic95_sup"] = [hi / e for (_, hi), e in zip(ic, t["robos_denunciados_esperados"])]
    t["posicion_conteo"] = t["robos_denunciados"].rank(ascending=False, method="min").astype(int)
    t["posicion_tasa"] = t["tasa_denuncias_mm"].rank(ascending=False, method="min").astype(int)
    t["posicion_razon"] = t["razon_observadas_esperadas"].rank(ascending=False, method="min").astype(int)
    t["se_distingue_descontando_el_anio"] = np.where(t["razon_ic95_inf"] > 1, "arriba", np.where(t["razon_ic95_sup"] < 1, "abajo", "no"))
    t.to_csv(TABLAS / "t5_estandarizado_por_anio.csv", index=False)

    print(f"% de las entradas del periodo que cae en 2019: estrato {100 * a.loc[a['anio'] == 2019, 'entradas'].sum() / a['entradas'].sum():.1f}; "
          f"mediana L1 {t.loc[t['lineas'] == '1', 'pct_entradas_en_2019'].median():.1f}; L12 {t.loc[t['lineas'] == '12', 'pct_entradas_en_2019'].median():.1f}.")
    top_c = set(t.nsmallest(10, "posicion_conteo")["estacion"])
    top_t = set(t.nsmallest(10, "posicion_tasa")["estacion"])
    top_r = set(t.nsmallest(10, "posicion_razon")["estacion"])
    print(f"Spearman conteo–razón: {spearman(t['robos_denunciados'], t['razon_observadas_esperadas']):.3f}; "
          f"coincidencias top-10 conteo–razón: {len(top_c & top_r)}. (Criterio de T5 con la razón en vez de la tasa.)")
    print(f"Spearman tasa cruda–razón: {spearman(t['tasa_denuncias_mm'], t['razon_observadas_esperadas']):.3f}; "
          f"top-10 en común: {len(top_t & top_r)}; salen {sorted(top_t - top_r)}; entran {sorted(top_r - top_t)}.")
    crudo = pd.read_csv(TABLAS / "t5_estrato_paso.csv").set_index("estacion")["se_distingue_del_estrato"]
    t["se_distingue_con_tasa_cruda"] = t["estacion"].map(crudo)
    print("\nDistinguibles con la tasa cruda (filas) contra descontando el año (columnas):\n",
          pd.crosstab(t["se_distingue_con_tasa_cruda"], t["se_distingue_descontando_el_anio"]).to_string())
    cambian = t[t["se_distingue_con_tasa_cruda"] != t["se_distingue_descontando_el_anio"]]
    print("\nLas que cambian de estatus:\n", cambian[["estacion", "lineas", "robos_denunciados", "pct_entradas_en_2019", "tasa_denuncias_mm",
          "razon_observadas_esperadas", "razon_ic95_inf", "razon_ic95_sup", "se_distingue_con_tasa_cruda", "se_distingue_descontando_el_anio"]].round(2).to_string(index=False))
    firmes = t[(t["se_distingue_con_tasa_cruda"] == t["se_distingue_descontando_el_anio"]) & (t["se_distingue_con_tasa_cruda"] != "no")]
    cols = ["estacion", "lineas", "robos_denunciados", "entradas", "tasa_denuncias_mm", "razon_observadas_esperadas",
            "razon_ic95_inf", "razon_ic95_sup", "posicion_conteo", "posicion_razon"]
    for lado, asc in [("arriba", False), ("abajo", True)]:
        f = firmes[firmes["se_distingue_con_tasa_cruda"] == lado].sort_values("razon_observadas_esperadas", ascending=asc)[cols].copy()
        f["entradas"] = (f["entradas"] / 1e6).round(1)
        print(f"\nFirmes {lado} del estrato con los dos criterios ({len(f)}):\n", f.round(2).rename(columns={"entradas": "entradas_M"}).to_string(index=False))
        f.round(3).to_csv(TABLAS / f"t5_firmes_{lado}.csv", index=False)


def main() -> int:
    panel = pd.read_csv(PANEL, dtype={"lineas": str})
    den = pd.read_csv(DENUNCIAS, dtype={"agencia": str, "fiscalia": str})
    TABLAS.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    falla = t5(panel, den)
    c3(panel, den)
    por_anio_estandarizado(panel)
    return 2 if falla else 0


if __name__ == "__main__":
    sys.exit(main())

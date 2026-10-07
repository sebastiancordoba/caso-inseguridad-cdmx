#!/usr/bin/env python3
"""EDA del estrato (a): 124 estaciones sin correspondencia dentro de la CDMX, 2019–2024.

El numerador son DENUNCIAS (carpetas de la FGJ por fecha del hecho). Escribe tablas en
datos/procesados/metro_tablas/eda_*.csv y figuras en docs/figuras/metro/eda_*.png. No ajusta
ningún modelo: describe, y cada bloque termina diciendo qué decisión de modelado implica
(eso va en docs/eda.md).

Regímenes que C3 dejó establecidos y que se marcan en toda serie temporal:
  R1  enero–agosto de 2019: tasa de denuncias ~2.5 veces la posterior, con afluencia plana
  R2  abril–junio de 2020: confinamiento, la tasa cae a la mitad
  R0  el resto
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comun import DENUNCIAS, FIGURAS, PANEL, TABLAS

R1 = ("2019-01", "2019-08")
R2 = ("2020-04", "2020-06")
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
ROJO, AZUL, GRIS = "#b3412c", "#2f6690", "#555555"


def byar(d: float, z: float = 1.96) -> tuple[float, float]:
    if d == 0:
        return 0.0, 3.69
    return (max(d * (1 - 1 / (9 * d) - z / (3 * np.sqrt(d))) ** 3, 0.0),
            (d + 1) * (1 - 1 / (9 * (d + 1)) + z / (3 * np.sqrt(d + 1))) ** 3)


def marca_regimenes(ax) -> None:
    ax.axvspan(pd.Timestamp("2019-01-01"), pd.Timestamp("2019-08-31"), color="#e9d8a6", alpha=0.45, lw=0, label="R1: ene–ago 2019")
    ax.axvspan(pd.Timestamp("2020-04-01"), pd.Timestamp("2020-06-30"), color="#e5b5ab", alpha=0.6, lw=0, label="R2: confinamiento")


def limpia(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)


def main() -> int:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    panel = pd.read_csv(PANEL, dtype={"lineas": str})
    den = pd.read_csv(DENUNCIAS, dtype={"agencia": str, "fiscalia": str})
    a = panel[~panel["es_correspondencia"] & ~panel["fuera_cdmx"] & (panel["entradas"] > 0)].copy()
    estrato = set(a["estacion"])
    da = den[den["asignada"] & den["estacion_mas_cercana"].isin(estrato)].copy()
    firmes_arriba = pd.read_csv(TABLAS / "t5_firmes_arriba.csv")
    firmes_abajo = pd.read_csv(TABLAS / "t5_firmes_abajo.csv")
    assert len(estrato) == 124 and len(firmes_arriba) == 20 and len(firmes_abajo) == 19

    # ------------------------------------------------------------ 1. distribución por estación
    print("1. Distribución de robos denunciados por estación (estrato a, 2019–2024)\n")
    t = a.groupby("estacion").agg(denuncias=("robos_denunciados_total", "sum"), entradas=("entradas", "sum"))
    q = t["denuncias"].describe(percentiles=[.1, .25, .5, .75, .9]).round(1)
    print(q.to_string())
    orden = t["denuncias"].sort_values(ascending=False)
    conc = {f"top {k}": round(100 * orden.head(k).sum() / orden.sum(), 1) for k in [5, 10, 20, 31, 62]}
    print("% de los robos denunciados del estrato que concentran las primeras:", conc)
    print("estaciones con menos de 15:", int((t["denuncias"] < 15).sum()), "| con cero:", int((t["denuncias"] == 0).sum()))
    pd.concat([q, pd.Series(conc)]).to_csv(TABLAS / "eda_distribucion.csv", header=["valor"])
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].hist(t["denuncias"], bins=np.arange(0, 121, 5), color=GRIS)
    ax[0].axvline(15, color=ROJO, ls="--", lw=1)
    ax[0].text(16, ax[0].get_ylim()[1] * 0.9, "15: umbral de\nevidencia suficiente", color=ROJO, fontsize=8)
    ax[0].set_xlabel("Robos denunciados por estación, 2019–2024")
    ax[0].set_ylabel("Estaciones")
    ax[1].hist(1e6 * t["denuncias"] / t["entradas"], bins=np.arange(0, 2.3, 0.1), color=GRIS)
    ax[1].axvline(1e6 * t["denuncias"].sum() / t["entradas"].sum(), color=ROJO, ls="--", lw=1)
    ax[1].set_xlabel("Robos denunciados por millón de entradas (tasa cruda)")
    ax[1].set_ylabel("Estaciones")
    for x in ax:
        limpia(x)
    fig.suptitle("EDA 1. Distribución de robos denunciados por estación: 124 estaciones de paso, CDMX", fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "eda_1_distribucion.png", dpi=150)
    plt.close(fig)

    # ------------------------------------------------------------ 2. sobredispersión
    print("\n2. Sobredispersión: media contra varianza de los robos denunciados, por estación\n")
    filas = []
    for nivel, clave in [("estación × mes", "anio_mes"), ("estación × año", "anio")]:
        g = a.groupby(["estacion", clave])["robos_denunciados_total"].sum().reset_index()
        mv = g.groupby("estacion")["robos_denunciados_total"].agg(media="mean", varianza=lambda x: x.var(ddof=1), n="size")
        mv = mv[mv["media"] > 0]
        mv["razon_var_media"] = mv["varianza"] / mv["media"]
        filas.append({"nivel": nivel, "estaciones": len(mv), "mediana_var_entre_media": round(mv["razon_var_media"].median(), 2),
                      "pct_con_var_mayor_que_media": round(100 * (mv["razon_var_media"] > 1).mean(), 1),
                      "p90_var_entre_media": round(mv["razon_var_media"].quantile(.9), 2)})
        mv.to_csv(TABLAS / f"eda_media_varianza_{clave}.csv")
        if clave == "anio_mes":
            mv_mes = mv
        else:
            mv_anio = mv
    r = pd.DataFrame(filas)
    print(r.to_string(index=False))
    # ¿cuánta de esa varianza es el quiebre de 2019? misma cuenta sin R1 ni R2
    sin = a[~a["anio_mes"].between(*R1) & ~a["anio_mes"].between(*R2)]
    g = sin.groupby("estacion")["robos_denunciados_total"].agg(media="mean", varianza=lambda x: x.var(ddof=1))
    g = g[g["media"] > 0]
    print(f"Estación × mes sin R1 ni R2: mediana de varianza/media = {(g['varianza'] / g['media']).median():.2f}; "
          f"{100 * ((g['varianza'] / g['media']) > 1).mean():.0f} % de las estaciones con varianza mayor que la media.")
    r.loc[len(r)] = {"nivel": "estación × mes, sin R1 ni R2", "estaciones": len(g),
                     "mediana_var_entre_media": round((g["varianza"] / g["media"]).median(), 2),
                     "pct_con_var_mayor_que_media": round(100 * ((g["varianza"] / g["media"]) > 1).mean(), 1),
                     "p90_var_entre_media": round((g["varianza"] / g["media"]).quantile(.9), 2)}
    r.to_csv(TABLAS / "eda_sobredispersion.csv", index=False)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
    for x, mv, titulo in [(ax[0], mv_mes, "Por estación, entre sus meses abiertos"), (ax[1], mv_anio, "Por estación, entre sus años abiertos")]:
        x.scatter(mv["media"], mv["varianza"], s=14, color=GRIS, alpha=.7)
        lim = [mv["media"].min() * 0.8, mv["media"].max() * 1.3]
        x.plot(lim, lim, color=ROJO, lw=1, label="Poisson: varianza = media")
        x.set_xscale("log")
        x.set_yscale("log")
        x.set_xlabel("Media de robos denunciados")
        x.set_ylabel("Varianza")
        x.set_title(titulo, fontsize=9, loc="left")
        x.legend(frameon=False, fontsize=8)
        limpia(x)
    fig.suptitle("EDA 2. Sobredispersión de los robos denunciados: leve entre meses, fuerte entre años (el salto de 2019)", fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "eda_2_sobredispersion.png", dpi=150)
    plt.close(fig)

    # ------------------------------------------------------------ 3. serie mensual y estacionalidad
    print("\n3. Serie mensual del estrato y estacionalidad\n")
    m = a.groupby("anio_mes").agg(denuncias=("robos_denunciados_total", "sum"), entradas=("entradas", "sum")).reset_index()
    m["tasa_denuncias_mm"] = 1e6 * m["denuncias"] / m["entradas"]
    m["regimen"] = np.where(m["anio_mes"].between(*R1), "R1", np.where(m["anio_mes"].between(*R2), "R2", "R0"))
    m["mes"] = m["anio_mes"].str[5:].astype(int)
    m.to_csv(TABLAS / "eda_serie_mensual_estrato.csv", index=False)
    reg = m.groupby("regimen").agg(meses=("anio_mes", "size"), denuncias=("denuncias", "sum"), entradas=("entradas", "sum"))
    reg["tasa_denuncias_mm"] = 1e6 * reg["denuncias"] / reg["entradas"]
    print(reg.round(3).to_string())
    r0 = m[m["regimen"] == "R0"]
    est = r0.groupby("mes").agg(denuncias=("denuncias", "sum"), entradas=("entradas", "sum"), n_meses=("anio_mes", "size"))
    est["tasa_denuncias_mm"] = 1e6 * est["denuncias"] / est["entradas"]
    ic = est["denuncias"].map(byar)
    est["ic95_inf"] = [1e6 * lo / e for (lo, _), e in zip(ic, est["entradas"])]
    est["ic95_sup"] = [1e6 * hi / e for (_, hi), e in zip(ic, est["entradas"])]
    est["vs_media"] = est["tasa_denuncias_mm"] / (1e6 * est["denuncias"].sum() / est["entradas"].sum())
    print("\nEstacionalidad (solo régimen R0), tasa de denuncias por mes del año:\n", est.round(3).to_string())
    est.to_csv(TABLAS / "eda_estacionalidad.csv")
    # toda la red, con todas las carpetas (no hace falta estación)
    den["mes"] = den["anio_mes"].str[5:].astype(int)
    red_r0 = den[~den["anio_mes"].between(*R1) & ~den["anio_mes"].between(*R2)]
    ent_red = panel[(panel["entradas"] > 0) & ~panel["anio_mes"].between(*R1) & ~panel["anio_mes"].between(*R2)].groupby("mes")["entradas"].sum()
    est_red = pd.DataFrame({"denuncias": red_r0.groupby("mes").size(), "entradas": ent_red})
    est_red["tasa_denuncias_mm"] = 1e6 * est_red["denuncias"] / est_red["entradas"]
    est_red.to_csv(TABLAS / "eda_estacionalidad_red.csv")

    fig, ax = plt.subplots(2, 1, figsize=(10, 6.5))
    x = pd.to_datetime(m["anio_mes"])
    ax[0].plot(x, m["tasa_denuncias_mm"], color=ROJO)
    marca_regimenes(ax[0])
    ax[0].set_ylabel("Robos denunciados por\nmillón de entradas")
    ax[0].set_ylim(bottom=0)
    ax[0].legend(frameon=False, fontsize=8)
    ax[0].set_title("Estrato (a), serie mensual (solo carpetas asignadas; desde 2022 faltan más coordenadas)", fontsize=9, loc="left")
    ax[1].errorbar(est.index, est["tasa_denuncias_mm"], yerr=[est["tasa_denuncias_mm"] - est["ic95_inf"], est["ic95_sup"] - est["tasa_denuncias_mm"]],
                   fmt="o-", color=GRIS, capsize=3, label="estrato (a)")
    ax[1].plot(est_red.index, est_red["tasa_denuncias_mm"], "s--", color=AZUL, alpha=.7, label="toda la red, todas las carpetas")
    ax[1].set_xticks(range(1, 13))
    ax[1].set_xticklabels(["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    ax[1].set_ylabel("Robos denunciados por\nmillón de entradas")
    ax[1].set_ylim(bottom=0)
    ax[1].legend(frameon=False, fontsize=8)
    ax[1].set_title("Por mes del año, solo régimen R0 (IC 95 % de Poisson)", fontsize=9, loc="left")
    for z in ax:
        limpia(z)
    fig.suptitle("EDA 3. Serie mensual con los tres regímenes, y estacionalidad", fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "eda_3_serie_y_estacionalidad.png", dpi=150)
    plt.close(fig)

    # ------------------------------------------------------------ 4. hora × día: CONTEOS
    print("\n4. Perfil hora × día. CONTEOS de denuncias, no tasas: la afluencia abierta es diaria, no horaria\n")
    for nombre, d in [("toda la red (todas las carpetas)", den), ("estrato (a)", da)]:
        print(f"{nombre}: {len(d):,} denuncias; hora en punto: {100 * (d['minuto'] == 0).mean():.0f} %; "
              f"a las 12:00 exactas: {100 * ((d['hora'] == 12) & (d['minuto'] == 0)).mean():.1f} %; "
              f"minuto múltiplo de 30: {100 * (d['minuto'] % 30 == 0).mean():.0f} %; sin hora: {d['hora'].isna().sum()}")
    por_hora = da.groupby("hora").size().reindex(range(24), fill_value=0)
    franja = {"6 a 9 h": por_hora[6:10].sum(), "10 a 13 h": por_hora[10:14].sum(), "14 a 17 h": por_hora[14:18].sum(),
              "18 a 21 h": por_hora[18:22].sum(), "22 a 5 h": por_hora[22:].sum() + por_hora[:6].sum()}
    print("estrato (a), % por franja:", {k: round(100 * v / por_hora.sum(), 1) for k, v in franja.items()})
    print("estrato (a), % por día:", {DIAS[i]: round(100 * v / len(da), 1) for i, v in da.groupby("dia_semana").size().items()})
    hd = pd.crosstab(da["dia_semana"], da["hora"]).reindex(index=range(7), columns=range(24), fill_value=0)
    hd.to_csv(TABLAS / "eda_hora_dia_estrato.csv")
    hd_red = pd.crosstab(den["dia_semana"], den["hora"]).reindex(index=range(7), columns=range(24), fill_value=0)
    hd_red.to_csv(TABLAS / "eda_hora_dia_red.csv")
    aviso = "CONTEOS de denuncias, no tasas: la afluencia abierta es diaria, no horaria. No es riesgo por hora: a las horas pico hay más gente."
    fig, ax = plt.subplots(2, 1, figsize=(10, 6.2))
    for z, tabla, titulo in [(ax[0], hd_red, f"Toda la red, todas las carpetas (n = {len(den):,})"), (ax[1], hd, f"Estrato (a) (n = {len(da):,})")]:
        im = z.imshow(tabla.to_numpy(), aspect="auto", cmap="Greys")
        z.set_yticks(range(7))
        z.set_yticklabels(DIAS)
        z.set_xticks(range(0, 24, 2))
        z.set_title(titulo, fontsize=9, loc="left")
        fig.colorbar(im, ax=z, label="robos denunciados")
    ax[1].set_xlabel("Hora del hecho declarada en la carpeta")
    fig.suptitle("EDA 4. Perfil hora × día de los robos denunciados\n" + aviso, fontsize=9, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "eda_4_hora_dia_red.png", dpi=150)
    plt.close(fig)

    top10 = firmes_arriba.head(10)["estacion"].tolist()
    fig, axs = plt.subplots(2, 5, figsize=(14, 5.4), sharex=True, sharey=True)
    perfiles = []
    ref = por_hora / por_hora.sum()
    for z, e in zip(axs.ravel(), top10):
        d = da[da["estacion_mas_cercana"] == e]
        h = d.groupby("hora").size().reindex(range(24), fill_value=0)
        z.bar(range(24), h / h.sum(), color=GRIS)
        z.plot(range(24), ref, color=ROJO, lw=1)
        z.set_title(f"{e} (n = {len(d)})", fontsize=8, loc="left")
        limpia(z)
        pico = d["hora"].between(6, 9).mean(), d["hora"].between(18, 21).mean()
        perfiles.append({"estacion": e, "denuncias": len(d), "pct_6_a_9h": round(100 * pico[0], 1), "pct_18_a_21h": round(100 * pico[1], 1),
                         "pct_fin_de_semana": round(100 * d["dia_semana"].isin([5, 6]).mean(), 1)})
    for z in axs[1]:
        z.set_xlabel("hora")
    for z in axs[:, 0]:
        z.set_ylabel("proporción de sus\nrobos denunciados")
    fig.suptitle("EDA 4b. Perfil horario de las diez primeras «firmes por arriba» (barras) contra el del estrato (línea roja)\n" + aviso
                 + " Con 12 a 90 denuncias por estación, las diferencias entre paneles son en buena parte ruido.", fontsize=9, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "eda_4b_hora_firmes.png", dpi=150)
    plt.close(fig)
    pf = pd.DataFrame(perfiles)
    pf.loc[len(pf)] = {"estacion": "ESTRATO (a)", "denuncias": len(da), "pct_6_a_9h": round(100 * da["hora"].between(6, 9).mean(), 1),
                       "pct_18_a_21h": round(100 * da["hora"].between(18, 21).mean(), 1), "pct_fin_de_semana": round(100 * da["dia_semana"].isin([5, 6]).mean(), 1)}
    print(pf.to_string(index=False))
    pf.to_csv(TABLAS / "eda_perfil_firmes.csv", index=False)

    # ------------------------------------------------------------ 5. razón obs/esp por año, 39 firmes
    print("\n5. ¿Las 39 firmes lo son de forma estable, o las pone ahí un año?\n")
    ta = a.groupby("anio").apply(lambda g: g["robos_denunciados_total"].sum() / g["entradas"].sum(), include_groups=False)
    ay = a.groupby(["estacion", "anio"]).agg(d=("robos_denunciados_total", "sum"), e=("entradas", "sum")).reset_index()
    ay["esp"] = ay["e"] * ay["anio"].map(ta)
    ay["razon"] = ay["d"] / ay["esp"]
    filas = []
    for lado, tabla in [("arriba", firmes_arriba), ("abajo", firmes_abajo)]:
        for e in tabla["estacion"]:
            g = ay[ay["estacion"] == e]
            del_lado = (g["razon"] > 1).sum() if lado == "arriba" else (g["razon"] < 1).sum()
            # dejando un año fuera: ¿sigue distinguiéndose de 1?
            aguanta = 0
            for anio in g["anio"]:
                h = g[g["anio"] != anio]
                lo, hi = byar(h["d"].sum())
                aguanta += (lo / h["esp"].sum() > 1) if lado == "arriba" else (hi / h["esp"].sum() < 1)
            peso = g.loc[g["d"].idxmax(), "d"] / g["d"].sum() if g["d"].sum() else np.nan
            filas.append({"lado": lado, "estacion": e, "denuncias": int(g["d"].sum()), "anios_abierta": len(g), "anios_del_lado": int(del_lado),
                          "sigue_firme_quitando_un_anio": f"{int(aguanta)} de {len(g)}", "firme_en_todos": bool(aguanta == len(g)),
                          "pct_denuncias_del_anio_mayor": round(100 * peso, 0),
                          **{f"razon_{int(r_.anio)}": round(r_.razon, 2) for r_ in g.itertuples()}})
    es = pd.DataFrame(filas)
    print(es.to_string(index=False))
    es.to_csv(TABLAS / "eda_estabilidad_firmes.csv", index=False)
    print("\nFirmes que lo siguen siendo quitando CUALQUIER año:", es.groupby("lado")["firme_en_todos"].sum().to_dict(),
          "de", es.groupby("lado").size().to_dict())

    fig, ax = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for z, lado, tabla, color in [(ax[0], "arriba", firmes_arriba, ROJO), (ax[1], "abajo", firmes_abajo, AZUL)]:
        for e in tabla["estacion"]:
            g = ay[ay["estacion"] == e]
            z.plot(g["anio"], g["razon"].clip(lower=0.04), color=color, alpha=.45, lw=1, marker="o", ms=2.5)
        z.axhline(1, color="#333", lw=.8)
        z.axvspan(2018.6, 2019.67, color="#e9d8a6", alpha=.45, lw=0)
        z.set_yscale("log")
        z.set_yticks([0.1, 0.25, 0.5, 1, 2, 4, 8])
        z.set_yticklabels(["0.1", "0.25", "0.5", "1", "2", "4", "8"])
        z.set_xlabel("Año del hecho")
        z.set_title(f"Las {len(tabla)} firmes por {lado}", fontsize=9, loc="left")
        limpia(z)
    ax[0].set_ylabel("Robos denunciados observados ÷ esperados\n(esperados: entradas × tasa del estrato ese año)")
    fig.suptitle("EDA 5. Razón observadas ÷ esperadas por año (sombreado: R1, ene–ago 2019 dentro de 2019; los ceros se dibujan en 0.04)", fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "eda_5_razon_anual_firmes.png", dpi=150)
    plt.close(fig)

    # ------------------------------------------------------------ 6. sensibilidad por estación al umbral
    print("\n6. Sensibilidad POR ESTACIÓN al umbral de asignación (100, 150, 250 m), las 39 firmes\n")
    base = a[["estacion", "anio_mes", "anio", "entradas"]]
    salida = None
    for u in [100, 150, 250]:
        d = den[den["distancia_m"].le(u) & den["estacion_mas_cercana"].isin(estrato)]
        n = d.groupby(["estacion_mas_cercana", "anio_mes"]).size().rename("n").reset_index()
        p = base.merge(n, left_on=["estacion", "anio_mes"], right_on=["estacion_mas_cercana", "anio_mes"], how="left").fillna({"n": 0})
        tasa_anio = p.groupby("anio").apply(lambda g: g["n"].sum() / g["entradas"].sum(), include_groups=False)
        p["esp"] = p["entradas"] * p["anio"].map(tasa_anio)
        s = p.groupby("estacion").agg(d=("n", "sum"), esp=("esp", "sum"))
        ic = s["d"].map(byar)
        s[f"denuncias_{u}m"] = s["d"].astype(int)
        s[f"razon_{u}m"] = (s["d"] / s["esp"]).round(2)
        s[f"estatus_{u}m"] = np.where([lo / e > 1 for (lo, _), e in zip(ic, s["esp"])], "arriba",
                                      np.where([hi / e < 1 for (_, hi), e in zip(ic, s["esp"])], "abajo", "no"))
        s = s[[f"denuncias_{u}m", f"razon_{u}m", f"estatus_{u}m"]]
        salida = s if salida is None else salida.join(s)
    firmes = pd.concat([firmes_arriba.assign(lado="arriba"), firmes_abajo.assign(lado="abajo")])[["estacion", "lado"]]
    sens = firmes.merge(salida, left_on="estacion", right_index=True)
    sens["aguanta_los_tres"] = (sens["estatus_100m"] == sens["lado"]) & (sens["estatus_150m"] == sens["lado"]) & (sens["estatus_250m"] == sens["lado"])
    sens["cambio_pct_denuncias_100_a_250"] = (100 * (sens["denuncias_250m"] / sens["denuncias_100m"].replace(0, np.nan) - 1)).round(0)
    print(sens.to_string(index=False))
    sens.to_csv(TABLAS / "eda_sensibilidad_umbral_por_estacion.csv", index=False)
    print("\nAguantan los tres umbrales:", sens.groupby("lado")["aguanta_los_tres"].sum().to_dict(), "de", sens.groupby("lado").size().to_dict())
    print("Las que no:", sens.loc[~sens["aguanta_los_tres"], "estacion"].tolist())

    # resumen para el modelo: qué estaciones son firmes con TODO (año y umbral)
    rob = es.merge(sens[["estacion", "aguanta_los_tres"]], on="estacion")
    rob["robusta"] = rob["firme_en_todos"] & rob["aguanta_los_tres"]
    rob[["lado", "estacion", "denuncias", "firme_en_todos", "aguanta_los_tres", "robusta"]].to_csv(TABLAS / "eda_firmes_robustas.csv", index=False)
    print("\nRobustas a quitar cualquier año Y a los tres umbrales:", rob.groupby("lado")["robusta"].sum().to_dict())
    print(rob.loc[rob["robusta"]].groupby("lado")["estacion"].apply(list).to_dict())
    print(f"\nFiguras → {FIGURAS.relative_to(FIGURAS.parents[2])}/eda_*.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""La tercera lista: una que contemple el volumen y el riesgo por pasajero a la vez.

Las dos listas que ya existen optimizan cosas distintas. La de conteo cubre más denuncias;
la de tasa cubre más riesgo por pasajero expuesto (M6). Los sinodales pidieron, el 15 de
octubre de 2026, una tercera que las contemple a las dos y que se vea que sirve. Aquí se
proponen varias formas de combinarlas, se evalúan todas FUERA DE MUESTRA con la misma
métrica que M6, y se elige una con un criterio escrito antes de mirar la tabla final.

Cómo se evalúa. Igual que M6: se ajusta el modelo con los años de entrenamiento, se arma
cada lista con lo que se sabía entonces, y se mide lo que pasó en el año siguiente: cuántas
denuncias cubren las k estaciones elegidas, con cuánta afluencia que vigilar, y a cuántas
denuncias por millón de entradas. Se hace con dos años de prueba —2024 (ajuste 2019–2023,
el de M6) y 2023 (ajuste 2019–2022)— para que la elección no dependa de un año.

Las reglas candidatas, todas calculadas solo con los años de entrenamiento:
  conteo         las k con más denuncias                                (lista 1, la publicada)
  tasa           las k con mayor tasa encogida del modelo               (lista 2, la de M6)
  mixta(w)       w·lugar por conteo + (1−w)·lugar por tasa, las k de menor puntaje
  piso(n)        tasa encogida, pero solo entre estaciones con n o más denuncias
  preselección   de las 2k (o 3k) con más denuncias, las k de mayor tasa
  esperadas      tasa encogida × entradas: denuncias esperadas por año
  pareto         capas de no dominadas en (conteo, tasa), rotas por la mixta
  combinada      la mixta con w = ½, solo entre estaciones con evidencia suficiente
                 (15 denuncias o más en el entrenamiento: el mismo umbral que ya usa la app)

El criterio de elección, fijado antes de ver la tabla completa: entre las reglas que cubren
al menos el 60 % de las denuncias que cubre el conteo con el mismo k, gana la de mayor tasa
por millón de entradas; tiene que ganar —o quedar a 0.02 de la ganadora— en k = 10 y k = 20
y en los dos años de prueba. Si ninguna cumple en todos, se prefiere la más simple de decir.

Lo que pasó con ese criterio, dicho de frente: NINGUNA regla lo cumple en los cuatro casos.
La mejor cambia de año a año y de k a k (en 2023 gana más peso al conteo; en 2024, menos), lo
que es coherente con lo débil que ya se sabía que es la señal de un año al siguiente (M5,
rho ≈ 0.30). Por eso la elección final usa el criterio de reserva —la más simple— acotado a
dos exigencias que sí se cumplen siempre: que supere al conteo en denuncias por millón en
los cuatro casos, y que cubra más denuncias que la lista por tasa en los cuatro. La
combinada es la más simple de las que lo cumplen; el bootstrap de abajo dice cuánta de su
ventaja sobre el conteo sobrevive al remuestreo de estaciones.

Salidas, en datos/procesados/metro_tablas/:
  lista3_evaluacion.csv          toda regla × k × año de prueba, con sus coberturas
  tres_listas.csv                las 124 estaciones con su lugar en las tres listas (ajuste
                                 completo 2019–2024, el mismo que publica la app)
  tres_listas_cobertura_2024.csv qué cubre en 2024 el top-10 y el top-20 de cada lista
  tres_listas_fuera_de_muestra.csv las 20 primeras de cada lista ELEGIDAS CON 2019–2023, con
                                 lo que cada estación tuvo en 2024: son las estaciones a las
                                 que corresponden los números de cobertura. No son las mismas
                                 que las de tres_listas.csv (ajuste completo), y la app debe
                                 enseñar cada tabla con su etiqueta

    python src/metro/09_lista_propuesta.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from comun import PANEL, PROCESADOS, TABLAS  # noqa: E402

# 08_modelo.py empieza con dígito: se importa por ruta. Reusar su Ajuste garantiza que la
# tasa predicha de aquí es exactamente la de M5 y M6, no una reimplementación.
_esp = importlib.util.spec_from_file_location("modelo", AQUI / "08_modelo.py")
modelo = importlib.util.module_from_spec(_esp)
_esp.loader.exec_module(modelo)

PISO_EVIDENCIA = 15          # el mismo umbral de «evidencia insuficiente» de modelo_estaciones.csv
KS = (5, 10, 15, 20, 30)
PRUEBAS = {2024: range(2019, 2024), 2023: range(2019, 2023)}
CRITERIO_COBERTURA = 0.60    # fracción de lo que cubre el conteo que la regla debe cubrir
CRITERIO_HOLGURA = 0.02      # a cuánto de la mejor tasa se considera empate


def ajusta_y_prueba(panel: pd.DataFrame, entrena: range, prueba: int) -> pd.DataFrame:
    """Una fila por estación abierta en el año de prueba, con lo sabido al entrenar y lo observado."""
    d_tr = modelo.panel_anual(panel, excluye_r2=True, anios=entrena)
    d_te = modelo.panel_anual(panel, excluye_r2=True, anios=range(prueba, prueba + 1)).set_index("estacion")
    # «nb» en minúsculas: con cualquier otra cadena Ajuste cae en la Poisson sin avisar. El
    # assert de phi existe porque eso pasó (15 de octubre): el primer corte de este script
    # evaluó la Poisson creyendo que era la binomial negativa, y lo delató el orden del
    # top-10 por tasa, que no coincidía con el de modelo_fuera_de_muestra.csv.
    aj = modelo.Ajuste(d_tr, "nb").ajusta()
    assert aj.convergio, f"el ajuste {entrena} no convergió"
    _, _, _, phi = aj.desempaca(aj.th)
    assert np.isfinite(phi), "el ajuste salió Poisson: la familia tiene que ser «nb»"
    post = aj.posterior().set_index("estacion")
    crudo = d_tr.groupby("estacion").agg(y=("y", "sum"), E=("E", "sum"), anios=("anio", "nunique"))
    v = pd.DataFrame({"tasa": post["razon_encogida"], "conteo": crudo["y"], "E_tr": crudo["E"],
                      "anios_tr": crudo["anios"], "y_obs": d_te["y"], "E_obs": d_te["E"]}).dropna()
    v["lugar_conteo"] = v["conteo"].rank(ascending=False, method="first")
    v["lugar_tasa"] = v["tasa"].rank(ascending=False, method="first")
    return v


# ----------------------------------------------------------------------------- las reglas
# Cada regla devuelve las estaciones ordenadas de más a menos prioritaria.

def r_conteo(v: pd.DataFrame) -> list[str]:
    return list(v.sort_values(["conteo", "tasa"], ascending=False).index)

def r_tasa(v: pd.DataFrame) -> list[str]:
    return list(v.sort_values("tasa", ascending=False).index)

def r_mixta(w: float):
    def f(v: pd.DataFrame) -> list[str]:
        p = w * v["lugar_conteo"] + (1 - w) * v["lugar_tasa"]
        return list(p.sort_values().index)
    f.__name__ = f"mixta w={w}"
    return f

def r_piso(n: int):
    def f(v: pd.DataFrame) -> list[str]:
        s = v[v["conteo"] >= n].sort_values("tasa", ascending=False)
        resto = v.drop(s.index).sort_values("tasa", ascending=False)   # por si k supera al piso
        return list(s.index) + list(resto.index)
    f.__name__ = f"piso {n}"
    return f

def r_preseleccion(m: int):
    def f(v: pd.DataFrame, k: int) -> list[str]:
        pre = v.sort_values("conteo", ascending=False).head(m * k)
        return list(pre.sort_values("tasa", ascending=False).index)
    f.__name__ = f"preselección {m}k"
    f.depende_de_k = True
    return f

def r_esperadas(v: pd.DataFrame) -> list[str]:
    e = v["tasa"] * v["E_tr"] / v["anios_tr"]
    return list(e.sort_values(ascending=False).index)

def r_pareto(v: pd.DataFrame) -> list[str]:
    """Capas de Pareto en (conteo, tasa): primero las que nadie domina, luego las siguientes."""
    pend = v[["conteo", "tasa"]].copy()
    orden: list[str] = []
    mezcla = 0.5 * v["lugar_conteo"] + 0.5 * v["lugar_tasa"]
    while len(pend):
        capa = []
        for e, fila in pend.iterrows():
            domina = ((pend["conteo"] >= fila["conteo"]) & (pend["tasa"] >= fila["tasa"])
                      & ((pend["conteo"] > fila["conteo"]) | (pend["tasa"] > fila["tasa"])))
            if not domina.any():
                capa.append(e)
        capa.sort(key=lambda e: mezcla[e])
        orden += capa
        pend = pend.drop(capa)
    return orden

def r_combinada(v: pd.DataFrame) -> list[str]:
    """Promedio de los dos lugares, entre las de evidencia suficiente; las demás, al final."""
    con = v[v["conteo"] >= PISO_EVIDENCIA]
    p = 0.5 * con["lugar_conteo"] + 0.5 * con["lugar_tasa"]
    resto = v.drop(con.index)
    return list(p.sort_values().index) + list(resto.sort_values("tasa", ascending=False).index)

REGLAS = ([("conteo", r_conteo), ("tasa", r_tasa)]
          + [(f"mixta w={w}", r_mixta(w)) for w in (0.25, 0.5, 0.75)]
          + [(f"piso {n}", r_piso(n)) for n in (10, 15, 20, 25)]
          + [(f"preselección {m}k", r_preseleccion(m)) for m in (2, 3)]
          + [("esperadas", r_esperadas), ("pareto", r_pareto), ("combinada", r_combinada)])
ORACULOS = [("oráculo cobertura", lambda v: list(v.sort_values("y_obs", ascending=False).index)),
            ("oráculo tasa", lambda v: list((v["y_obs"] / v["E_obs"]).sort_values(ascending=False).index))]


def cubre(v: pd.DataFrame, elegidas: list[str]) -> dict:
    e = v.loc[elegidas]
    return {"estaciones": len(e), "denuncias_cubiertas": int(e["y_obs"].sum()),
            "pct_denuncias": round(100 * e["y_obs"].sum() / v["y_obs"].sum(), 1),
            "entradas_M": round(float(e["E_obs"].sum()), 1),
            "pct_entradas": round(100 * e["E_obs"].sum() / v["E_obs"].sum(), 1),
            "por_millon": round(float(e["y_obs"].sum() / e["E_obs"].sum()), 3)}


def evalua(v: pd.DataFrame, anio: int) -> pd.DataFrame:
    filas = []
    for k in KS:
        for nombre, regla in REGLAS + ORACULOS:
            orden = regla(v, k) if getattr(regla, "depende_de_k", False) else regla(v)
            filas.append({"anio_prueba": anio, "k": k, "regla": nombre, **cubre(v, orden[:k])})
    return pd.DataFrame(filas)


def elige(ev: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    """Aplica el criterio escrito arriba y dice qué reglas lo cumplen en cada (año, k)."""
    cand = [n for n, _ in REGLAS if n not in ("conteo", "tasa")]
    detalle = []
    for (anio, k), g in ev[ev["k"].isin((10, 20))].groupby(["anio_prueba", "k"]):
        g = g.set_index("regla")
        base = g.loc["conteo", "denuncias_cubiertas"]
        ok = g.loc[[c for c in cand if g.loc[c, "denuncias_cubiertas"] >= CRITERIO_COBERTURA * base]]
        mejor = ok["por_millon"].max()
        for c in cand:
            detalle.append({"anio_prueba": anio, "k": k, "regla": c,
                            "cubre_60pct_del_conteo": c in ok.index,
                            "a_0.02_de_la_mejor_tasa": c in ok.index and g.loc[c, "por_millon"] >= mejor - CRITERIO_HOLGURA})
    det = pd.DataFrame(detalle)
    cumple = det.groupby("regla")["a_0.02_de_la_mejor_tasa"].all()
    cumple = cumple[cumple].index.tolist()
    return (cumple, det)


def tres_listas(propuesta: str) -> pd.DataFrame:
    """Las 124 con su lugar en las tres listas, sobre el ajuste completo que publica la app."""
    m = pd.read_csv(PROCESADOS / "modelo_estaciones.csv", dtype={"lineas": str})
    t = m[["estacion", "lineas", "robos_denunciados", "entradas", "tasa_encogida_mm", "tasa_ic95_inf", "tasa_ic95_sup",
           "posicion_conteo", "posicion_encogida", "evidencia_insuficiente", "distinguible_modelo"]].copy()
    t = t.rename(columns={"robos_denunciados": "denuncias_2019_2024", "posicion_encogida": "lugar_tasa",
                          "posicion_conteo": "lugar_conteo"})
    t["entradas_M"] = (t.pop("entradas") / 1e6).round(1)
    assert propuesta == "combinada", "la tabla de las tres listas está escrita para la combinada; si cambia la regla, cámbiala aquí"
    t["puntaje_propuesta"] = (0.5 * t["lugar_conteo"] + 0.5 * t["lugar_tasa"]).round(1)
    # Las de evidencia insuficiente van después de todas las demás, ordenadas por tasa, igual
    # que en la regla evaluada: no se recomienda desplegar por ruido.
    con = t[~t["evidencia_insuficiente"]].sort_values(["puntaje_propuesta", "lugar_tasa"])
    sin = t[t["evidencia_insuficiente"]].sort_values("lugar_tasa")
    orden = list(con.index) + list(sin.index)
    t["lugar_propuesta"] = pd.Series(range(1, len(t) + 1), index=orden)
    t["regla_propuesta"] = "promedio del lugar por conteo y del lugar por tasa, entre estaciones con 15 denuncias o más"
    for col in ("conteo", "tasa", "propuesta"):
        t[f"top10_{col}"] = t[f"lugar_{col}"] <= 10
        t[f"top20_{col}"] = t[f"lugar_{col}"] <= 20
    return t.sort_values("lugar_propuesta").reset_index(drop=True)


def main() -> int:
    pd.set_option("display.width", 220)
    panel = pd.read_csv(PANEL, dtype={"lineas": str})
    evs, vs = [], {}
    for anio, entrena in PRUEBAS.items():
        v = ajusta_y_prueba(panel, entrena, anio)
        vs[anio] = v
        print(f"Prueba {anio}: ajuste {entrena.start}–{entrena.stop - 1}, {len(v)} estaciones abiertas, "
              f"{int(v['y_obs'].sum())} denuncias y {v['E_obs'].sum():.0f} M de entradas observadas "
              f"({v['y_obs'].sum() / v['E_obs'].sum():.3f} por millón en el estrato).")
        evs.append(evalua(v, anio))
    ev = pd.concat(evs, ignore_index=True)
    ev.to_csv(TABLAS / "lista3_evaluacion.csv", index=False)

    for anio in PRUEBAS:
        for k in (10, 20):
            g = ev[(ev["anio_prueba"] == anio) & (ev["k"] == k)].drop(columns=["anio_prueba", "k", "estaciones"])
            print(f"\n=== {anio}, top-{k} ===\n" + g.to_string(index=False))

    cumple, det = elige(ev)
    print("\nReglas que cumplen el criterio en los cuatro casos (2023 y 2024, k = 10 y 20):", cumple or "ninguna")
    print(det.pivot_table(index="regla", columns=["anio_prueba", "k"], values="a_0.02_de_la_mejor_tasa", aggfunc="first").to_string())

    # ¿Cuánta de la ventaja de la combinada sobre el conteo sobrevive si se remuestrean las
    # estaciones? Mismo bootstrap que usa 08_modelo.py para M5: las listas se arman con las
    # columnas de entrenamiento de la remuestra y se miden en su año de prueba.
    rng = np.random.default_rng(20261015)
    print("\nBootstrap sobre estaciones (2,000 remuestras): diferencia en denuncias por millón, IC 95 %")
    boot = []
    for anio, v in vs.items():
        for k in (10, 20):
            dif_c, dif_t = [], []
            for _ in range(2000):
                b = v.sample(len(v), replace=True, random_state=int(rng.integers(1 << 31)))
                b = b[~b.index.duplicated()]            # una estación no puede elegirse dos veces
                b["lugar_conteo"] = b["conteo"].rank(ascending=False, method="first")
                b["lugar_tasa"] = b["tasa"].rank(ascending=False, method="first")
                rc = cubre(b, r_combinada(b)[:k])["por_millon"]
                dif_c.append(rc - cubre(b, r_conteo(b)[:k])["por_millon"])
                dif_t.append(rc - cubre(b, r_tasa(b)[:k])["por_millon"])
            fila = {"anio_prueba": anio, "k": k,
                    "combinada_menos_conteo": round(float(np.mean(dif_c)), 3),
                    "ic95_inf_conteo": round(float(np.quantile(dif_c, .025)), 3), "ic95_sup_conteo": round(float(np.quantile(dif_c, .975)), 3),
                    "pct_remuestras_mejor_que_conteo": round(100 * float(np.mean(np.array(dif_c) > 0)), 1),
                    "combinada_menos_tasa": round(float(np.mean(dif_t)), 3),
                    "ic95_inf_tasa": round(float(np.quantile(dif_t, .025)), 3), "ic95_sup_tasa": round(float(np.quantile(dif_t, .975)), 3)}
            boot.append(fila)
    boot = pd.DataFrame(boot)
    boot.to_csv(TABLAS / "lista3_bootstrap.csv", index=False)
    print(boot.to_string(index=False))

    propuesta = "combinada"
    t = tres_listas(propuesta)
    t.to_csv(TABLAS / "tres_listas.csv", index=False)
    print(f"\nTres listas (ajuste completo) → {TABLAS / 'tres_listas.csv'}; propuesta = {propuesta}")
    print(t[["lugar_propuesta", "estacion", "denuncias_2019_2024", "entradas_M", "tasa_encogida_mm", "lugar_conteo", "lugar_tasa", "puntaje_propuesta"]]
          .head(20).to_string(index=False))

    # lo que cubre en 2024 cada una de las tres, para la conclusión
    v24 = vs[2024]
    filas = []
    for k in (10, 20):
        for nombre, regla in (("conteo", r_conteo), ("tasa", r_tasa), ("propuesta", r_combinada),
                              ("oráculo cobertura", ORACULOS[0][1])):
            filas.append({"k": k, "lista": nombre, **cubre(v24, regla(v24)[:k])})
    c = pd.DataFrame(filas)
    c.to_csv(TABLAS / "tres_listas_cobertura_2024.csv", index=False)
    print("\nCobertura en 2024 de las tres listas:\n" + c.to_string(index=False))

    # Las estaciones concretas detrás de esos números: elegidas con 2019–2023, medidas en 2024.
    filas = []
    for nombre, regla in (("conteo", r_conteo), ("tasa", r_tasa), ("propuesta", r_combinada)):
        for lugar, e in enumerate(regla(v24)[:20], start=1):
            f = v24.loc[e]
            filas.append({"lista": nombre, "lugar": lugar, "estacion": e, "denuncias_2019_2023": int(f["conteo"]),
                          "tasa_predicha_mm": round(float(f["tasa"]), 3), "denuncias_2024": int(f["y_obs"]),
                          "entradas_2024_M": round(float(f["E_obs"]), 2), "tasa_2024_mm": round(float(f["y_obs"] / f["E_obs"]), 3)})
    fm = pd.DataFrame(filas)
    fm.to_csv(TABLAS / "tres_listas_fuera_de_muestra.csv", index=False)
    print("\nLas diez primeras de cada lista, elegidas con 2019–2023:")
    for nombre in ("conteo", "tasa", "propuesta"):
        print(f"  {nombre:9s}", ", ".join(fm[(fm["lista"] == nombre) & (fm["lugar"] <= 10)]["estacion"]))
    en_las_tres = set.intersection(*[set(fm[(fm["lista"] == n) & (fm["lugar"] <= 10)]["estacion"]) for n in ("conteo", "tasa", "propuesta")])
    print("  en las tres:", sorted(en_las_tres) or "ninguna")
    return 0


if __name__ == "__main__":
    sys.exit(main())

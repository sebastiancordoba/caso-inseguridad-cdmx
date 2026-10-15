#!/usr/bin/env python3
"""Junta en UN solo JSON lo que la app estática necesita → docs/app/datos.json.

No calcula nada nuevo: lee el panel y las tablas que dejaron 02 a 05 (hay que correrlos
antes; `python src/metro/correr.py` lo hace en orden) y las coordenadas del shapefile.
El numerador son DENUNCIAS; todas las claves lo dicen (`denuncias`, `tasa_denuncias_mm`).

Estratos:
  a        sin correspondencia, dentro de la CDMX: tasa medible (124)
  b        correspondencia: exposición no identificable con datos abiertos (26)
  c        Hidalgo y Guerrero: correspondencias anómalas, hallazgo aparte (2)
  edomex   fuera de la CDMX: se denuncia ante otra fiscalía, no se mide (11)
"""

from __future__ import annotations

import json
import math

import geopandas as gpd
import pandas as pd

from comun import CRUDOS, PANEL, PROCESADOS, RAIZ, TABLAS, lee_estaciones, linea_corta

SALIDA = RAIZ / "docs" / "app" / "datos.json"
LINEAS_SHP = f"zip://{CRUDOS / 'stc_metro_shp.zip'}!stcmetro_shp/STC_Metro_lineas_utm14n.shp"
ANCHO = 1000  # unidades del viewBox del SVG
MIN_DENUNCIAS = 15  # por debajo, «evidencia insuficiente»: fuera de toda lista de recomendación
ANOMALAS = ["Hidalgo", "Guerrero"]
# Colores de la señalética del STC, escritos a mano (aproximados; son identidad, no dato).
COLORES = {"1": "#e9468f", "2": "#00599f", "3": "#b69c13", "4": "#6cbab1", "5": "#fdd200", "6": "#d81c23",
           "7": "#e87511", "8": "#118749", "9": "#512826", "A": "#a02d96", "B": "#118751", "12": "#b99e51"}


def byar(d: float, z: float = 1.96) -> tuple[float, float]:
    if d == 0:
        return 0.0, 3.69
    return (max(d * (1 - 1 / (9 * d) - z / (3 * math.sqrt(d))) ** 3, 0.0),
            (d + 1) * (1 - 1 / (9 * (d + 1)) + z / (3 * math.sqrt(d + 1))) ** 3)


def r(x: float, n: int = 2) -> float | None:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), n)


def main() -> int:
    panel = pd.read_csv(PANEL, dtype={"lineas": str})
    t5 = pd.read_csv(TABLAS / "t5_estrato_paso.csv", dtype={"lineas": str}).set_index("estacion")
    std = pd.read_csv(TABLAS / "t5_estandarizado_por_anio.csv").set_index("estacion")
    firmes = {**{e: "arriba" for e in pd.read_csv(TABLAS / "t5_firmes_arriba.csv")["estacion"]},
              **{e: "abajo" for e in pd.read_csv(TABLAS / "t5_firmes_abajo.csv")["estacion"]}}
    t7 = pd.read_csv(TABLAS / "t7_transbordos_necesarios.csv").set_index("estacion")
    t2 = pd.read_csv(TABLAS / "t2_pares_resumen.csv").set_index("estacion_con_agencia")
    assert len(t5) == 124 and len(t7) == 28 and len(firmes) == 39
    # La magnitud que manda en la app es la tasa ENCOGIDA del modelo (docs/modelo.md); la cruda va de secundaria.
    mod = pd.read_csv(PROCESADOS / "modelo_estaciones.csv").set_index("estacion")
    diag = json.loads((TABLAS / "modelo_diagnostico.json").read_text(encoding="utf-8"))
    cob = pd.read_csv(TABLAS / "modelo_fuera_de_muestra_cobertura.csv")
    cob = cob[cob["estaciones"] == 10].set_index("regla")
    assert len(mod) == 124 and (mod["distinguible_modelo"] != "no").sum() == 25
    # El bloque «dos reglas» está escrito a mano en index.html: si el modelo cambia, que truene aquí y no mienta allá.
    m_, c_ = cob.loc["tasa predicha (modelo)"], cob.loc["conteo 2019–2023"]
    assert (int(m_["robos_denunciados_2024_cubiertos"]), float(m_["denuncias_2024_por_millon_de_entradas"]),
            int(c_["robos_denunciados_2024_cubiertos"]), float(c_["denuncias_2024_por_millon_de_entradas"]),
            round(float(m_["entradas_2024_M"])), round(float(c_["entradas_2024_M"])),
            int((mod["distinguible_modelo"] == "arriba").sum()), int((mod["distinguible_modelo"] == "abajo").sum())) == (41, 0.77, 92, 0.57, 53, 160, 14, 11), \
        "cambió el modelo: actualiza los números escritos a mano en docs/app/index.html (bloque «dos reglas» y «¿Cómo se calcula?»)"

    # --- geometría: metros UTM → viewBox, norte arriba
    est = lee_estaciones()
    lin = gpd.read_file(LINEAS_SHP).to_crs(est.crs)
    x0, y0, x1, y1 = lin.total_bounds
    margen = 0.03 * (x1 - x0)
    x0, y0, x1, y1 = x0 - margen, y0 - margen, x1 + margen, y1 + margen
    k = ANCHO / (x1 - x0)
    alto = round((y1 - y0) * k)

    def xy(px: float, py: float) -> list[float]:
        return [round((px - x0) * k, 1), round((y1 - py) * k, 1)]

    lineas = []
    for g in lin.itertuples():
        geo = g.geometry.simplify(25)  # 25 m: invisible a esta escala, quita dos tercios de los vértices
        clave = linea_corta(str(g.LINEA))
        lineas.append({"linea": clave, "color": COLORES[clave], "ruta": g.RUTA.replace("à", "á"),
                       "puntos": [xy(c[0], c[1]) for c in geo.coords]})  # el shapefile trae z

    centro = est.assign(x=est.geometry.x, y=est.geometry.y).groupby("NOMBRE")[["x", "y"]].mean()

    # --- por estación
    abiertos = panel[panel["entradas"] > 0]
    tot = abiertos.groupby("estacion").agg(denuncias=("robos_denunciados_total", "sum"), entradas=("entradas", "sum"),
                                           con_violencia=("robos_denunciados_con_violencia", "sum"))
    anual = abiertos.groupby(["estacion", "anio"]).agg(d=("robos_denunciados_total", "sum"), e=("entradas", "sum"))
    attrs = panel.groupby("estacion").agg(lineas=("lineas", "first"), corr=("es_correspondencia", "first"),
                                          fuera=("fuera_cdmx", "first"))

    estaciones = []
    for nombre, a in attrs.iterrows():
        estrato = "edomex" if a["fuera"] else "c" if nombre in ANOMALAS else "b" if a["corr"] else "a"
        d, e = int(tot.loc[nombre, "denuncias"]), float(tot.loc[nombre, "entradas"])
        lo, hi = byar(d)
        s = {"nombre": nombre, "lineas": a["lineas"].split("|"), "xy": xy(*centro.loc[nombre]), "estrato": estrato,
             "denuncias": d, "entradas_M": r(e / 1e6, 1), "tasa_denuncias_mm": r(1e6 * d / e),
             "tasa_ic95": [r(1e6 * lo / e), r(1e6 * hi / e)]}
        serie = []
        for anio in range(2019, 2025):
            if (nombre, anio) in anual.index:
                dd, ee = int(anual.loc[(nombre, anio), "d"]), float(anual.loc[(nombre, anio), "e"])
                l2, h2 = byar(dd)
                serie.append({"anio": anio, "denuncias": dd, "entradas_M": r(ee / 1e6, 1), "tasa_denuncias_mm": r(1e6 * dd / ee),
                              "tasa_ic95": [r(1e6 * l2 / ee), r(1e6 * h2 / ee)]})
            else:
                serie.append({"anio": anio, "cerrada": True})
        s["serie"] = serie
        if estrato == "a":
            f, g = t5.loc[nombre], std.loc[nombre]
            assert int(f["robos_denunciados"]) == d
            fila = mod.loc[nombre]
            assert int(fila["robos_denunciados"]) == d and bool(fila["evidencia_insuficiente"]) == (d < MIN_DENUNCIAS)
            s.update({"tasa_encogida_mm": r(fila["tasa_encogida_mm"]), "tasa_encogida_ic95": [r(fila["tasa_ic95_inf"]), r(fila["tasa_ic95_sup"])],
                      "razon_encogida": r(fila["razon_encogida"]), "razon_encogida_ic95": [r(fila["razon_ic95_inf"]), r(fila["razon_ic95_sup"])],
                      "estatus": str(fila["distinguible_modelo"]),  # arriba / abajo / no: IC 95 % de la razón fuera de 1
                      "pos_conteo": int(fila["posicion_conteo"]), "pos_encogida": int(fila["posicion_encogida"]),
                      "cambio": int(fila["posicion_conteo"]) - int(fila["posicion_encogida"]),  # positivo: sube al pasar de conteo a tasa
                      "evidencia_insuficiente": bool(fila["evidencia_insuficiente"]),
                      "sensible_al_umbral": bool(fila["sensible_al_umbral_de_asignacion"])})
        elif estrato in ("b", "c"):
            s.update({"transbordos_necesarios_M": r(t7.loc[nombre, "transbordos_necesarios_M"], 0),
                      "transbordos_multiplo_de_entradas": r(t7.loc[nombre, "como_multiplo_de_sus_entradas"], 1)})
            if estrato == "c":
                s.update({"razon_vs_controles": r(t2.loc[nombre, "razon_todos_los_canales"], 1),
                          "razon_vs_controles_solo_digital": r(t2.loc[nombre, "razon_solo_digital"], 1)})
        estaciones.append(s)

    ea = [s for s in estaciones if s["estrato"] == "a"]
    corr = [s for s in estaciones if s["estrato"] in ("b", "c")]
    meta = {
        "generado": pd.Timestamp.today().strftime("%Y-%m-%d"),
        "fecha_de_corte": "31 de enero de 2025",
        "ventana": "2019-01 a 2024-12, por fecha del hecho",
        "delito": "Robo a pasajero a bordo de Metro, con y sin violencia (carpetas de investigación de la FGJ CDMX)",
        "viewbox": [ANCHO, alto],
        "min_denuncias_para_recomendar": MIN_DENUNCIAS,
        "umbral_de_cambio": 20,
        "estrato_a": {"estaciones": len(ea), "denuncias": sum(s["denuncias"] for s in ea),
                      "entradas_M": r(sum(s["entradas_M"] for s in ea), 0),
                      "tasa_denuncias_mm": r(1e6 * t5["robos_denunciados"].sum() / t5["entradas"].sum()),
                      "con_evidencia_suficiente": sum(not s["evidencia_insuficiente"] for s in ea)},
        "correspondencias": {"estaciones": len(corr), "denuncias": sum(s["denuncias"] for s in corr)},
        "denuncias_asignadas": int(tot["denuncias"].sum()),
        "carpetas_en_la_ventana": 8366,
        "pct_sin_asignar": 19.1,
        "tasa_de_paso_usada_en_t7": 0.71,
        "modelo": {"nombre": "binomial negativa con efecto aleatorio de estación y efecto de año",
                   "tasa_de_la_estacion_tipica_mm": r(diag["tasa_base_mm"], 2), "distinguibles": 25,
                   "arriba": int((mod["distinguible_modelo"] == "arriba").sum()), "abajo": int((mod["distinguible_modelo"] == "abajo").sum())},
        "fuentes": {"carpetas": "https://archivo.datos.cdmx.gob.mx/FGJ/carpetas/carpetasFGJ_acumulado_2025_01.csv",
                    "afluencia": "https://datos.cdmx.gob.mx/dataset/afluencia-diaria-del-metro-cdmx",
                    "estaciones": "https://datos.cdmx.gob.mx/dataset/lineas-y-estaciones-del-metro"},
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps({"meta": meta, "lineas": lineas, "estaciones": estaciones}, ensure_ascii=False, separators=(",", ":")),
                      encoding="utf-8")
    kb = SALIDA.stat().st_size / 1024
    assert kb < 1024, f"datos.json pesa {kb:.0f} KB: hay que recortarlo"
    n = pd.Series([s["estrato"] for s in estaciones]).value_counts().to_dict()
    print(f"{len(estaciones)} estaciones {n}; {len(lineas)} líneas, {sum(len(x['puntos']) for x in lineas)} vértices; "
          f"{kb:.0f} KB → {SALIDA.relative_to(RAIZ)}")
    print(f"estrato (a): {meta['estrato_a']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Modelo del estrato (a): binomial negativa con efecto aleatorio de estación y efecto de año.

    y_st ~ NB(mu_st, phi),   log mu_st = log E_st + alpha + v_s + gamma_t,   v_s ~ N(0, sigma²)

y_st son ROBOS DENUNCIADOS (carpetas asignadas a la estación), E_st entradas en los meses en
que la estación estuvo abierta, gamma_t suma cero. La cantidad de interés es exp(alpha + v_s):
la tasa de denuncias por entrada, encogida hacia la del estrato en proporción a la poca
evidencia de cada estación.

Ajuste: máxima verosimilitud marginal. La integral sobre v_s (una por estación) se hace con
cuadratura de Gauss–Hermite adaptativa: centrada en la moda de cada estación y escalada con
su curvatura. La Poisson es el caso límite phi → ∞ y se ajusta con el mismo código. Los
intervalos de v_s salen de su distribución posterior dados los hiperparámetros estimados
(Bayes empírico): NO incorporan la incertidumbre de alpha, gamma, sigma y phi, y por eso son
algo estrechos. Se dice en docs/modelo.md.

Las hipótesis M1 a M7 están congeladas en docs/hipotesis.md desde antes de escribir esto.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from scipy import optimize, stats
from scipy.special import gammaln, logsumexp

from comun import PANEL, PROCESADOS, TABLAS

R2 = ("2020-04", "2020-06")
K_NODOS = 25
SALIDA = PROCESADOS / "modelo_estaciones.csv"


def spearman(a: pd.Series, b: pd.Series) -> float:
    return float(a.rank().corr(b.rank()))


def byar(d: float, z: float = 1.96) -> tuple[float, float]:
    if d == 0:
        return 0.0, 3.69
    return (max(d * (1 - 1 / (9 * d) - z / (3 * np.sqrt(d))) ** 3, 0.0),
            (d + 1) * (1 - 1 / (9 * (d + 1)) + z / (3 * np.sqrt(d + 1))) ** 3)


def panel_anual(panel: pd.DataFrame, excluye_r2: bool, anios: range) -> pd.DataFrame:
    a = panel[~panel["es_correspondencia"] & ~panel["fuera_cdmx"] & (panel["entradas"] > 0) & panel["anio"].isin(anios)]
    if excluye_r2:
        a = a[~a["anio_mes"].between(*R2)]
    g = a.groupby(["estacion", "anio"]).agg(y=("robos_denunciados_total", "sum"), E=("entradas", "sum")).reset_index()
    g["E"] = g["E"] / 1e6  # millones de entradas: exp(alpha + v_s) sale en denuncias por millón
    return g


class Ajuste:
    """Verosimilitud marginal de y_st con efecto aleatorio normal de estación."""

    def __init__(self, d: pd.DataFrame, familia: str, con_efecto_aleatorio: bool = True, nodos: int = K_NODOS):
        self.d = d.reset_index(drop=True)
        self.familia = familia
        self.re = con_efecto_aleatorio
        self.estaciones = sorted(d["estacion"].unique())
        self.anios = sorted(d["anio"].unique())
        self.s = d["estacion"].map({e: i for i, e in enumerate(self.estaciones)}).to_numpy()
        self.t = d["anio"].map({a: i for i, a in enumerate(self.anios)}).to_numpy()
        self.y = d["y"].to_numpy(float)
        self.logE = np.log(d["E"].to_numpy(float))
        self.S, self.T = len(self.estaciones), len(self.anios)
        self.K = nodos
        self.x, self.w = np.polynomial.hermite.hermgauss(nodos)

    # --- parámetros: alpha, gamma_1..T-1 (la última = −suma), log sigma, log phi
    def desempaca(self, th: np.ndarray):
        alpha = th[0]
        g = np.append(th[1:self.T], -th[1:self.T].sum())
        i = self.T
        sigma = np.exp(th[i]) if self.re else 0.0
        i += 1 if self.re else 0
        phi = np.exp(th[i]) if self.familia == "nb" else np.inf
        return alpha, g, sigma, phi

    def inicial(self) -> np.ndarray:
        tasa = self.y.sum() / np.exp(self.logE).sum()
        th = [np.log(tasa)] + [0.0] * (self.T - 1)
        if self.re:
            th.append(np.log(0.5))
        if self.familia == "nb":
            th.append(np.log(10.0))
        return np.array(th)

    def logp(self, eta: np.ndarray, phi: float, y: np.ndarray) -> np.ndarray:
        mu = np.exp(eta)
        if np.isinf(phi):
            return y * eta - mu - gammaln(y + 1)
        return (gammaln(y + phi) - gammaln(phi) - gammaln(y + 1) + phi * (np.log(phi) - np.log(phi + mu))
                + y * (eta - np.log(phi + mu)))

    def moda(self, base: np.ndarray, sigma: float, phi: float) -> tuple[np.ndarray, np.ndarray]:
        """Moda y desviación de la posterior de v_s por estación (Newton, vectorizado)."""
        v = np.zeros(self.S)
        for _ in range(60):
            mu = np.exp(base + v[self.s])
            if np.isinf(phi):
                g1, g2 = self.y - mu, -mu
            else:
                g1, g2 = (self.y - mu) * phi / (phi + mu), -mu * phi * (phi + self.y) / (phi + mu) ** 2
            grad = np.bincount(self.s, g1, self.S) - v / sigma ** 2
            hess = np.bincount(self.s, g2, self.S) - 1 / sigma ** 2
            paso = grad / hess
            v = v - paso
            if np.abs(paso).max() < 1e-10:
                break
        return v, 1 / np.sqrt(-hess)

    def negloglik(self, th: np.ndarray) -> float:
        alpha, g, sigma, phi = self.desempaca(th)
        base = self.logE + alpha + g[self.t]
        if not self.re:
            return -self.logp(base, phi, self.y).sum()
        v0, sd = self.moda(base, sigma, phi)
        nodos = v0[:, None] + np.sqrt(2) * sd[:, None] * self.x[None, :]            # S × K
        lp = np.zeros((self.S, self.K))
        np.add.at(lp, self.s, self.logp(base[:, None] + nodos[self.s], phi, self.y[:, None]))
        lp += stats.norm.logpdf(nodos, 0, sigma) + self.x[None, :] ** 2 + np.log(self.w)[None, :]
        ll = np.log(np.sqrt(2) * sd) + logsumexp(lp, axis=1)
        return -ll.sum()

    def ajusta(self) -> "Ajuste":
        r = optimize.minimize(self.negloglik, self.inicial(), method="BFGS", options={"gtol": 1e-6, "maxiter": 500})
        if not r.success:  # BFGS a veces se queja de precisión estando ya en el óptimo: se afina con Nelder–Mead
            r2 = optimize.minimize(self.negloglik, r.x, method="Nelder-Mead", options={"xatol": 1e-7, "fatol": 1e-9, "maxiter": 20000})
            r = r2 if r2.fun <= r.fun + 1e-8 else r
        self.th, self.loglik, self.k = r.x, -r.fun, len(r.x)
        self.aic = 2 * self.k - 2 * self.loglik
        self.convergio = bool(r.success) or bool(np.linalg.norm(optimize.approx_fprime(r.x, self.negloglik, 1e-6)) < 1e-2)
        self.gradiente = float(np.linalg.norm(optimize.approx_fprime(r.x, self.negloglik, 1e-6)))
        return self

    def errores(self) -> np.ndarray:
        """Errores estándar por hessiano numérico (en la escala de los parámetros: log para sigma y phi)."""
        n, h = len(self.th), 1e-4
        H = np.zeros((n, n))
        f = self.negloglik
        for i in range(n):
            for j in range(i, n):
                ei, ej = np.eye(n)[i] * h, np.eye(n)[j] * h
                H[i, j] = H[j, i] = (f(self.th + ei + ej) - f(self.th + ei - ej) - f(self.th - ei + ej) + f(self.th - ei - ej)) / (4 * h * h)
        return np.sqrt(np.diag(np.linalg.inv(H)))

    def posterior(self) -> pd.DataFrame:
        """Posterior de v_s en una rejilla fina, dados los hiperparámetros: media y cuantiles de exp(v_s)."""
        alpha, g, sigma, phi = self.desempaca(self.th)
        base = self.logE + alpha + g[self.t]
        v0, sd = self.moda(base, sigma, phi)
        z = np.linspace(-7, 7, 561)
        rej = v0[:, None] + sd[:, None] * z[None, :]
        lp = np.zeros_like(rej)
        np.add.at(lp, self.s, self.logp(base[:, None] + rej[self.s], phi, self.y[:, None]))
        lp += stats.norm.logpdf(rej, 0, sigma)
        p = np.exp(lp - lp.max(axis=1, keepdims=True))
        p /= p.sum(axis=1, keepdims=True)
        cdf = np.cumsum(p, axis=1)
        q = lambda a: np.array([np.interp(a, cdf[i], rej[i]) for i in range(self.S)])  # noqa: E731
        return pd.DataFrame({
            "estacion": self.estaciones,
            "v_media": (p * rej).sum(axis=1), "v_sd": np.sqrt((p * rej ** 2).sum(axis=1) - (p * rej).sum(axis=1) ** 2),
            "razon_encogida": (p * np.exp(rej)).sum(axis=1), "razon_ic95_inf": np.exp(q(0.025)), "razon_ic95_sup": np.exp(q(0.975)),
            "tasa_encogida_mm": np.exp(alpha) * (p * np.exp(rej)).sum(axis=1),
            "tasa_ic95_inf": np.exp(alpha + q(0.025)), "tasa_ic95_sup": np.exp(alpha + q(0.975)),
            "prob_arriba_del_estrato": (p * (rej > 0)).sum(axis=1),
        })

    def ajustados(self) -> np.ndarray:
        alpha, g, sigma, phi = self.desempaca(self.th)
        base = self.logE + alpha + g[self.t]
        v0 = self.moda(base, sigma, phi)[0] if self.re else np.zeros(self.S)
        return np.exp(base + v0[self.s])


def describe(m: Ajuste, nombre: str) -> dict:
    alpha, g, sigma, phi = m.desempaca(m.th)
    return {"modelo": nombre, "parametros": m.k, "loglik": round(m.loglik, 2), "AIC": round(m.aic, 2), "convergio": m.convergio,
            "norma_gradiente": round(m.gradiente, 5), "tasa_base_mm": round(float(np.exp(alpha)), 3),
            "sigma_v": round(float(sigma), 3) if m.re else None, "phi": None if np.isinf(phi) else round(float(phi), 1)}


def main() -> int:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    TABLAS.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(PANEL, dtype={"lineas": str})
    d = panel_anual(panel, excluye_r2=True, anios=range(2019, 2025))
    print(f"Panel estación × año, sin abril–junio de 2020: {len(d)} celdas, {d['estacion'].nunique()} estaciones, "
          f"{int(d['y'].sum()):,} robos denunciados, {d['E'].sum():,.0f} M de entradas; {100 * (d['y'] == 0).mean():.1f} % de celdas en cero.")

    # ------------------------------------------------------------------ a. Poisson contra NB
    print("\n" + "=" * 100 + "\na. Poisson contra binomial negativa (M1) y varianza del efecto de estación (M2)\n")
    pois = Ajuste(d, "poisson").ajusta()
    nb = Ajuste(d, "nb").ajusta()
    nb_sin = Ajuste(d, "nb", con_efecto_aleatorio=False).ajusta()
    pois_sin = Ajuste(d, "poisson", con_efecto_aleatorio=False).ajusta()
    comp = pd.DataFrame([describe(pois_sin, "Poisson, sin efecto de estación"), describe(nb_sin, "NB, sin efecto de estación"),
                         describe(pois, "Poisson + efecto de estación"), describe(nb, "NB + efecto de estación")])
    print(comp.to_string(index=False))
    if not (pois.convergio and nb.convergio):
        print("\nALGÚN MODELO NO CONVERGIÓ. Por el timebox acordado se para aquí: quedan el EDA y este diagnóstico.")
        comp.to_csv(TABLAS / "modelo_comparacion.csv", index=False)
        return 3
    lr1 = 2 * (nb.loglik - pois.loglik)
    p1 = 0.5 * stats.chi2.sf(max(lr1, 0), 1)
    lr2 = 2 * (nb.loglik - nb_sin.loglik)
    p2 = 0.5 * stats.chi2.sf(max(lr2, 0), 1)
    lr2p = 2 * (pois.loglik - pois_sin.loglik)
    mu_p = pois.ajustados()
    pearson = float(((pois.y - mu_p) ** 2 / mu_p).sum())
    gl = len(d) - (pois.k - 1) - pois.S  # conservador: cuenta cada v_s como un parámetro
    print(f"\nM1. Razón de verosimilitudes NB contra Poisson (las dos con efecto de estación y de año): LR = {lr1:.2f}, "
          f"p = {p1:.4f} (mitad de χ²₁, por estar phi → ∞ en la frontera). ΔAIC (NB − Poisson) = {nb.aic - pois.aic:.2f}.")
    print(f"    Dispersión de Pearson de la Poisson, condicional a los efectos de estación: {pearson:.1f} / {gl} g.l. = {pearson / gl:.2f} "
          f"(g.l. conservadores); p = {stats.chi2.sf(pearson, gl):.4f}.")
    m1 = bool(p1 <= 0.05 and nb.aic < pois.aic)
    print(f"    → M1 {'SE SOSTIENE: queda sobredispersión, se usa la NB' if m1 else 'SE RECHAZA: la Poisson basta; el orden final se reporta con la Poisson'}.")
    print(f"M2. Razón de verosimilitudes contra sigma_v = 0: LR = {lr2:.1f} con NB (p = {p2:.2g}); {lr2p:.1f} con Poisson. "
          f"→ M2 {'SE SOSTIENE' if p2 <= 0.05 else 'SE RECHAZA'}.")
    pp, pn = pois.posterior(), nb.posterior()
    dist = lambda t: int(((t["razon_ic95_inf"] > 1) | (t["razon_ic95_sup"] < 1)).sum())  # noqa: E731
    print(f"    Para qué sirve la diferencia: Spearman del orden Poisson–NB = {spearman(pp['razon_encogida'], pn['razon_encogida']):.3f}; "
          f"estaciones con IC 95 % fuera de 1: {dist(pp)} con Poisson, {dist(pn)} con NB.")
    final, nombre_final = (nb, "NB") if m1 else (pois, "Poisson")
    ee = final.errores()
    alpha, g, sigma, phi = final.desempaca(final.th)
    print(f"\nModelo final: {nombre_final}. tasa base exp(alpha) = {np.exp(alpha):.3f} denuncias por millón de entradas "
          f"(IC 95 %: {np.exp(alpha - 1.96 * ee[0]):.3f} a {np.exp(alpha + 1.96 * ee[0]):.3f}); "
          f"sigma_v = {sigma:.3f} (IC 95 %: {np.exp(final.th[final.T] - 1.96 * ee[final.T]):.3f} a {np.exp(final.th[final.T] + 1.96 * ee[final.T]):.3f})"
          + ("" if np.isinf(phi) else f"; phi = {phi:.1f} (IC 95 %: {np.exp(final.th[-1] - 1.96 * ee[-1]):.1f} a {np.exp(final.th[-1] + 1.96 * ee[-1]):.1f})"))
    anios = pd.DataFrame({"anio": final.anios, "exp_gamma": np.exp(g).round(3)})
    print("Efecto de año, exp(gamma_t), relativo al año medio:", dict(zip(anios["anio"], anios["exp_gamma"])))
    # sensibilidad a los nodos de la cuadratura
    ll25 = final.loglik
    ll45 = -Ajuste(d, final.familia, nodos=45).negloglik(final.th)
    print(f"Cuadratura: log-verosimilitud con 25 nodos {ll25:.4f}, con 45 nodos {ll45:.4f} (diferencia {abs(ll25 - ll45):.1e}).")
    # chequeo predictivo de ceros
    mu_f = final.ajustados()
    p0 = np.exp(-mu_f) if np.isinf(phi) else (phi / (phi + mu_f)) ** phi
    print(f"Celdas en cero: observadas {int((final.y == 0).sum())}, esperadas por el modelo {p0.sum():.1f}.")
    comp["LR_vs_poisson"] = [None, None, None, round(lr1, 2)]
    comp.to_csv(TABLAS / "modelo_comparacion.csv", index=False)
    diag = {"LR_nb_vs_poisson": lr1, "p_nb_vs_poisson": p1, "delta_aic_nb_menos_poisson": nb.aic - pois.aic, "pearson_poisson": pearson,
            "gl_pearson": gl, "LR_sigma": lr2, "p_sigma": p2, "modelo_final": nombre_final, "sigma_v": float(sigma),
            "phi": None if np.isinf(phi) else float(phi), "tasa_base_mm": float(np.exp(alpha)), "exp_gamma": dict(zip(map(int, final.anios), map(float, np.exp(g)))),
            "loglik_25_nodos": ll25, "loglik_45_nodos": ll45, "ceros_observados": int((final.y == 0).sum()), "ceros_esperados": float(p0.sum())}

    # ------------------------------------------------------------------ c. orden encogido contra crudo
    print("\n" + "=" * 100 + "\nc. Orden por tasa encogida contra tasa cruda y razón observadas ÷ esperadas (M3)\n")
    post = final.posterior()
    t5 = pd.read_csv(TABLAS / "t5_estandarizado_por_anio.csv")[["estacion", "lineas", "robos_denunciados", "entradas", "tasa_denuncias_mm",
                                                                 "razon_observadas_esperadas", "posicion_conteo", "posicion_tasa", "posicion_razon"]]
    tab = post.merge(t5, on="estacion")
    tab["posicion_encogida"] = tab["razon_encogida"].rank(ascending=False, method="min").astype(int)
    tab["cambio_cruda_a_encogida"] = tab["posicion_tasa"] - tab["posicion_encogida"]
    tab["factor_de_encogimiento"] = ((tab["razon_encogida"] - 1) / (tab["razon_observadas_esperadas"] - 1)).round(2)
    rho_cruda, rho_razon = spearman(tab["razon_encogida"], tab["tasa_denuncias_mm"]), spearman(tab["razon_encogida"], tab["razon_observadas_esperadas"])
    rho_conteo = spearman(tab["razon_encogida"], tab["robos_denunciados"])
    top_e, top_c = set(tab.nsmallest(10, "posicion_encogida")["estacion"]), set(tab.nsmallest(10, "posicion_tasa")["estacion"])
    pocos_en_top = tab[(tab["posicion_encogida"] <= 10) & (tab["robos_denunciados"] < 15)]["estacion"].tolist()
    print(f"Spearman encogida–cruda: {rho_cruda:.3f}; encogida–razón obs/esp: {rho_razon:.3f}; encogida–conteo: {rho_conteo:.3f}.")
    print(f"Top-10 en común con la tasa cruda: {len(top_e & top_c)}; salen {sorted(top_c - top_e)}; entran {sorted(top_e - top_c)}.")
    print(f"Estaciones con menos de 15 denuncias en el top-10 encogido: {pocos_en_top or 'ninguna'} "
          f"(en el top-10 crudo: {tab[(tab['posicion_tasa'] <= 10) & (tab['robos_denunciados'] < 15)]['estacion'].tolist()}).")
    m3 = bool(rho_cruda >= 0.9 and not pocos_en_top)
    print(f"→ M3 {'SE SOSTIENE' if m3 else 'SE RECHAZA'}.")
    mov = tab.reindex(tab["cambio_cruda_a_encogida"].abs().sort_values(ascending=False).index).head(12)
    print("\nLas que más se mueven de la tasa cruda a la encogida:\n",
          mov[["estacion", "robos_denunciados", "tasa_denuncias_mm", "razon_observadas_esperadas", "razon_encogida", "posicion_tasa", "posicion_encogida", "cambio_cruda_a_encogida"]].round(2).to_string(index=False))
    print(f"\nEncogimiento por tamaño: mediana del factor (1 = no encoge) con <15 denuncias "
          f"{tab.loc[tab['robos_denunciados'] < 15, 'factor_de_encogimiento'].median():.2f}; con 15 a 39 "
          f"{tab.loc[tab['robos_denunciados'].between(15, 39), 'factor_de_encogimiento'].median():.2f}; con 40 o más "
          f"{tab.loc[tab['robos_denunciados'] >= 40, 'factor_de_encogimiento'].median():.2f}.")

    # ------------------------------------------------------------------ e. multiplicidad
    print("\n" + "=" * 100 + "\ne. Multiplicidad (M4)\n")
    tab["distinguible_modelo"] = np.where(tab["razon_ic95_inf"] > 1, "arriba", np.where(tab["razon_ic95_sup"] < 1, "abajo", "no"))
    firmes = pd.concat([pd.read_csv(TABLAS / "t5_firmes_arriba.csv").assign(lado="arriba"), pd.read_csv(TABLAS / "t5_firmes_abajo.csv").assign(lado="abajo")])
    rob = pd.read_csv(TABLAS / "eda_firmes_robustas.csv")
    tab["firme_fase3"] = tab["estacion"].map(dict(zip(firmes["estacion"], firmes["lado"]))).fillna("no")
    tab["robusta_eda"] = tab["estacion"].isin(rob.loc[rob["robusta"], "estacion"])
    n_mod = int((tab["distinguible_modelo"] != "no").sum())
    print(f"Distinguibles con pruebas una por una (fase 3): 39 (42 con la tasa cruda). Esperadas por azar al 95 %: ~6.")
    print(f"Distinguibles con el modelo (IC 95 % de exp(v_s) fuera de 1): {n_mod} "
          f"({int((tab['distinguible_modelo'] == 'arriba').sum())} arriba, {int((tab['distinguible_modelo'] == 'abajo').sum())} abajo).")
    print("Cruce fase 3 (filas) contra modelo (columnas):\n", pd.crosstab(tab["firme_fase3"], tab["distinguible_modelo"]).to_string())
    conserva = int(((tab["distinguible_modelo"] != "no") & tab["robusta_eda"]).sum())
    print(f"De las 19 robustas del EDA, el modelo conserva {conserva}. Pierde: {tab[tab['robusta_eda'] & (tab['distinguible_modelo'] == 'no')]['estacion'].tolist()}.")
    print(f"De las 20 firmes NO robustas, el modelo conserva {int(((tab['distinguible_modelo'] != 'no') & (tab['firme_fase3'] != 'no') & ~tab['robusta_eda']).sum())}.")
    print(f"Nuevas (distinguibles con el modelo y no firmes en fase 3): {tab[(tab['distinguible_modelo'] != 'no') & (tab['firme_fase3'] == 'no')]['estacion'].tolist()}.")
    m4 = bool(n_mod < 39 and conserva >= 12)
    print(f"→ M4 {'SE SOSTIENE' if m4 else 'SE RECHAZA'}.")

    # ------------------------------------------------------------------ b. robustez: con abril–junio de 2020
    print("\n" + "=" * 100 + "\nb. Robustez: incluyendo abril–junio de 2020 (M7)\n")
    d_con = panel_anual(panel, excluye_r2=False, anios=range(2019, 2025))
    con = Ajuste(d_con, final.familia).ajusta()
    pc = con.posterior().set_index("estacion")["razon_encogida"]
    rho7 = spearman(tab.set_index("estacion")["razon_encogida"], pc)
    a2, g2, s2, ph2 = con.desempaca(con.th)
    print(f"Con esos tres meses: {int(d_con['y'].sum() - d['y'].sum())} denuncias y {d_con['E'].sum() - d['E'].sum():.0f} M de entradas más. "
          f"sigma_v = {s2:.3f}; exp(gamma_2020) = {np.exp(g2[1]):.3f} contra {np.exp(g[1]):.3f} sin ellos. "
          f"Spearman del orden con y sin: {rho7:.4f}; mayor cambio de posición: "
          f"{int((pc.rank(ascending=False) - tab.set_index('estacion')['razon_encogida'].rank(ascending=False)).abs().max())} lugares.")
    m7 = bool(rho7 >= 0.98)
    print(f"→ M7 {'SE SOSTIENE' if m7 else 'SE RECHAZA'}.")

    # ------------------------------------------------------------------ d. fuera de muestra
    print("\n" + "=" * 100 + "\nd. Validación fuera de muestra: se ajusta con 2019–2023 y se predice el orden de 2024 (M5, M6)\n")
    d_tr = panel_anual(panel, excluye_r2=True, anios=range(2019, 2024))
    d_24 = panel_anual(panel, excluye_r2=True, anios=range(2024, 2025)).set_index("estacion")
    tr = Ajuste(d_tr, final.familia).ajusta()
    ptr = tr.posterior().set_index("estacion")
    crudo = d_tr.groupby("estacion").agg(y=("y", "sum"), E=("E", "sum"))
    v = pd.DataFrame({"tasa_predicha": ptr["razon_encogida"], "tasa_cruda_19_23": crudo["y"] / crudo["E"], "conteo_19_23": crudo["y"],
                      "y_2024": d_24["y"], "E_2024": d_24["E"]}).dropna()
    v["tasa_2024"] = v["y_2024"] / v["E_2024"]
    print(f"Entrenamiento: {int(d_tr['y'].sum()):,} denuncias; convergió: {tr.convergio}. Prueba: {len(v)} estaciones abiertas en 2024, "
          f"{int(v['y_2024'].sum())} robos denunciados ({v['y_2024'].median():.0f} por estación en mediana; {int((v['y_2024'] == 0).sum())} con cero).")
    rhos = {k: spearman(v[k], v["tasa_2024"]) for k in ["tasa_predicha", "tasa_cruda_19_23", "conteo_19_23"]}
    print("Spearman contra la tasa de denuncias observada en 2024:", {k: round(x, 3) for k, x in rhos.items()})
    # techo alcanzable: la tasa de 2024 es ruidosa. Se simula 2024 con la tasa predicha como verdad.
    rng = np.random.default_rng(20260920)
    lam = v["tasa_predicha"] * v["y_2024"].sum() / (v["tasa_predicha"] * v["E_2024"]).sum() * v["E_2024"]
    techo = [spearman(v["tasa_predicha"], pd.Series(rng.poisson(lam), index=v.index) / v["E_2024"]) for _ in range(2000)]
    print(f"Techo por ruido: si la tasa predicha fuera la verdad exacta, el Spearman contra un 2024 simulado (Poisson) sería "
          f"{np.mean(techo):.3f} (IC 95 %: {np.quantile(techo, .025):.3f} a {np.quantile(techo, .975):.3f}).")
    # incertidumbre del propio Spearman: bootstrap sobre estaciones (no estaba en el criterio; se reporta para no sobreleer M5)
    bs = []
    for _ in range(4000):
        b = v.sample(len(v), replace=True, random_state=int(rng.integers(1 << 31)))
        bs.append([spearman(b[k], b["tasa_2024"]) for k in ["tasa_predicha", "tasa_cruda_19_23", "conteo_19_23"]])
    bs = np.array(bs)
    print(f"Bootstrap sobre estaciones, IC 95 %: tasa predicha {np.quantile(bs[:, 0], .025):.3f} a {np.quantile(bs[:, 0], .975):.3f}; "
          f"predicha − cruda {np.quantile(bs[:, 0] - bs[:, 1], .025):+.3f} a {np.quantile(bs[:, 0] - bs[:, 1], .975):+.3f}; "
          f"predicha − conteo {np.quantile(bs[:, 0] - bs[:, 2], .025):+.3f} a {np.quantile(bs[:, 0] - bs[:, 2], .975):+.3f}.")
    ic_m5 = {"tasa_predicha": [float(np.quantile(bs[:, 0], .025)), float(np.quantile(bs[:, 0], .975))],
             "predicha_menos_cruda": [float(np.quantile(bs[:, 0] - bs[:, 1], .025)), float(np.quantile(bs[:, 0] - bs[:, 1], .975))],
             "predicha_menos_conteo": [float(np.quantile(bs[:, 0] - bs[:, 2], .025)), float(np.quantile(bs[:, 0] - bs[:, 2], .975))]}
    m5 = bool(rhos["tasa_predicha"] > 0.30 and rhos["tasa_predicha"] >= rhos["tasa_cruda_19_23"] and rhos["tasa_predicha"] >= rhos["conteo_19_23"])
    print(f"→ M5 {'SE SOSTIENE' if m5 else 'SE RECHAZA'}.")
    filas = []
    for k in [10, 20]:
        for regla, col in [("tasa predicha (modelo)", "tasa_predicha"), ("tasa cruda 2019–2023", "tasa_cruda_19_23"), ("conteo 2019–2023", "conteo_19_23"),
                           ("oráculo: conteo de 2024", "y_2024")]:
            e = v.nlargest(k, col)
            filas.append({"estaciones": k, "regla": regla, "robos_denunciados_2024_cubiertos": int(e["y_2024"].sum()),
                          "pct_de_los_del_estrato": round(100 * e["y_2024"].sum() / v["y_2024"].sum(), 1), "entradas_2024_M": round(e["E_2024"].sum(), 1),
                          "pct_de_las_entradas": round(100 * e["E_2024"].sum() / v["E_2024"].sum(), 1),
                          "denuncias_2024_por_millon_de_entradas": round(e["y_2024"].sum() / e["E_2024"].sum(), 2)})
    cob = pd.DataFrame(filas)
    print("\nMétrica de decisión: ¿qué cubre cada regla en 2024?\n", cob.to_string(index=False))
    print(f"(estrato en 2024: {v['y_2024'].sum() / v['E_2024'].sum():.2f} denuncias por millón de entradas)")
    cob.to_csv(TABLAS / "modelo_fuera_de_muestra_cobertura.csv", index=False)
    a_, c_ = cob[(cob["estaciones"] == 10) & cob["regla"].str.startswith("tasa predicha")].iloc[0], cob[(cob["estaciones"] == 10) & cob["regla"].str.startswith("conteo")].iloc[0]
    m6 = bool(a_["denuncias_2024_por_millon_de_entradas"] > c_["denuncias_2024_por_millon_de_entradas"])
    print(f"Top-10 por tasa predicha: {sorted(v.nlargest(10, 'tasa_predicha').index)}")
    print(f"Top-10 por conteo:        {sorted(v.nlargest(10, 'conteo_19_23').index)}")
    print(f"→ M6 {'SE SOSTIENE' if m6 else 'SE RECHAZA'} ({a_['denuncias_2024_por_millon_de_entradas']} contra {c_['denuncias_2024_por_millon_de_entradas']} por millón de entradas; "
          f"en absoluto, {a_['robos_denunciados_2024_cubiertos']} contra {c_['robos_denunciados_2024_cubiertos']} denuncias).")
    v.round(4).to_csv(TABLAS / "modelo_fuera_de_muestra.csv")

    # ------------------------------------------------------------------ tabla final
    eda_sens = pd.read_csv(TABLAS / "eda_sensibilidad_umbral_por_estacion.csv").set_index("estacion")["aguanta_los_tres"]
    tab["sensible_al_umbral_de_asignacion"] = tab["estacion"].map(~eda_sens).fillna(False) | tab["estacion"].eq("Tasqueña")
    tab["evidencia_insuficiente"] = tab["robos_denunciados"] < 15
    tab["modelo"] = nombre_final
    final_tab = tab.sort_values("posicion_encogida")[[
        "posicion_encogida", "estacion", "lineas", "robos_denunciados", "entradas", "tasa_denuncias_mm", "tasa_encogida_mm", "tasa_ic95_inf", "tasa_ic95_sup",
        "razon_observadas_esperadas", "razon_encogida", "razon_ic95_inf", "razon_ic95_sup", "prob_arriba_del_estrato", "distinguible_modelo",
        "firme_fase3", "robusta_eda", "posicion_conteo", "posicion_tasa", "posicion_razon", "cambio_cruda_a_encogida", "factor_de_encogimiento",
        "evidencia_insuficiente", "sensible_al_umbral_de_asignacion", "modelo"]].round(4)
    final_tab.to_csv(SALIDA, index=False)
    print(f"\n{len(final_tab)} estaciones → {SALIDA.relative_to(SALIDA.parents[2])}")
    ver = final_tab[["posicion_encogida", "estacion", "robos_denunciados", "tasa_denuncias_mm", "tasa_encogida_mm", "tasa_ic95_inf", "tasa_ic95_sup",
                     "razon_encogida", "razon_ic95_inf", "razon_ic95_sup", "distinguible_modelo", "posicion_conteo", "posicion_tasa"]].round(2)
    print("\nPrimeras 20:\n", ver.head(20).to_string(index=False))
    print("\nÚltimas 15:\n", ver.tail(15).to_string(index=False))

    diag.update({"M1": m1, "M2": bool(p2 <= 0.05), "M3": m3, "M4": m4, "M5": m5, "M6": m6, "M7": m7, "spearman_encogida_cruda": rho_cruda,
                 "spearman_encogida_razon": rho_razon, "distinguibles_modelo": n_mod, "robustas_conservadas": conserva,
                 "spearman_fuera_de_muestra": rhos, "techo_spearman": float(np.mean(techo)), "bootstrap_m5": ic_m5, "spearman_con_y_sin_r2": rho7})
    (TABLAS / "modelo_diagnostico.json").write_text(json.dumps(diag, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\nVeredictos:", {k: diag[k] for k in ["M1", "M2", "M3", "M4", "M5", "M6", "M7"]})
    return 0


if __name__ == "__main__":
    sys.exit(main())

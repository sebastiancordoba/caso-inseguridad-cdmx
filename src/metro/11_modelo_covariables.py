#!/usr/bin/env python3
"""¿Más información mejora la predicción? El protocolo de la decisión 66, tal como se escribió.

La binomial negativa de 08_modelo.py predice la tasa del año siguiente con ρ ≈ 0.3 (M5). Este
script prueba si covariables de estación —línea, entorno de delitos de la FGJ a 500 m,
tamaño— o una tendencia por estación mejoran esa predicción FUERA DE MUESTRA, con años de
prueba rodantes (2022, 2023, 2024) y las métricas y el criterio de mejora fijados ANTES de
correrlo (decisión 66, commit 60e5c59). No se buscan reglas nuevas: las tres listas (conteo,
tasa, combinada) se reevalúan con el modelo ganador, si lo hay.

El modelo general, con u(s) de dimensión 1 (solo intercepto) o 2 (intercepto y pendiente):

    y(s,t) ~ NB(mu, phi),  log mu = log E(s,t) + alpha + gamma(t) + x(s)'beta + v(s) + b(s)·(t − t̄)
    v(s) ~ N(0, sigma²),  b(s) ~ N(0, tau²), independientes

Con beta = 0 y sin b(s) es exactamente el modelo base: se comprueba que reproduce M5 y M6.
La integral sobre u(s) se hace con cuadratura de Gauss–Hermite adaptativa (moda y curvatura
por estación), como en 08, extendida a dos dimensiones. La predicción para el año de prueba
t* es exp(alpha + x'beta) · E[exp(v + b·(t* − t̄)) | datos], con las covariables calculadas
solo con los años de entrenamiento.

Salidas, en datos/procesados/metro_tablas/:
  covariables_evaluacion.csv     modelo × año de prueba × k: por millón y denuncias cubiertas por
                                 el top-k por tasa predicha, por conteo y por la combinada; ρ y
                                 log-verosimilitud multinomial
  covariables_bootstrap.csv      modelo × año × k: diferencia contra el base, IC 95 % y P(> 0)
  covariables_veredicto.csv      los tres criterios (a, b, c) por modelo y si mejora
  covariables_ajuste_completo.csv  ajuste 2019–2024: parámetros, loglik, AIC, LR, sigma_v, tau
  covariables_coeficientes.csv   beta con error estándar, ajuste completo
  covariables_predicciones.csv   tasa predicha por modelo, año de prueba y estación

    python src/metro/11_modelo_covariables.py
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats
from scipy.special import gammaln, logsumexp

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from comun import PANEL, PROCESADOS, TABLAS  # noqa: E402


def importa(nombre: str, archivo: str):
    esp = importlib.util.spec_from_file_location(nombre, AQUI / archivo)
    mod = importlib.util.module_from_spec(esp)
    esp.loader.exec_module(mod)
    return mod


modelo = importa("modelo", "08_modelo.py")
lista = importa("lista", "09_lista_propuesta.py")

COVARIABLES = PROCESADOS / "covariables_estacion.csv"
PRUEBAS = {2022: range(2019, 2022), 2023: range(2019, 2023), 2024: range(2019, 2024)}
KS = (10, 20)
REMUESTRAS = 2000
SEMILLA = 20261020
P_MINIMA = 0.90
MODELOS = {  # nombre → (columnas fijas, con pendiente)
    "base": ([], False),
    "línea": (["línea"], False),
    "entorno": (["entorno_todos", "entorno_transeunte"], False),
    "tamaño": (["tamaño"], False),
    "todas las fijas": (["línea", "entorno_todos", "entorno_transeunte", "tamaño"], False),
    "tendencia": ([], True),
    "todas + tendencia": (["línea", "entorno_todos", "entorno_transeunte", "tamaño"], True),
}


# ----------------------------------------------------------------------------- covariables
def disenio(d_tr: pd.DataFrame, cov: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Matriz de diseño por estación (ordenada como Ajuste.estaciones), solo con años de entrenamiento."""
    est = sorted(d_tr["estacion"].unique())
    anios = sorted(d_tr["anio"].unique())
    c = cov[cov["estacion"].isin(est) & cov["anio"].isin(anios)].groupby("estacion").agg(
        linea=("linea", "first"), entorno_todos=("entorno_todos", "mean"), entorno_transeunte=("entorno_transeunte", "mean"))
    tam = d_tr.groupby("estacion")["E"].mean()
    X = pd.DataFrame(index=est)
    z = lambda s: (s - s.mean()) / s.std(ddof=0)  # noqa: E731
    for col in columnas:
        if col == "línea":
            dum = pd.get_dummies(c.loc[est, "linea"], prefix="línea", dtype=float)
            dum = dum.drop(columns=dum.columns[0])  # referencia: la primera línea en orden
            X = X.join(dum)
        elif col == "entorno_todos":
            X["entorno_todos"] = z(np.log1p(c.loc[est, "entorno_todos"]))
        elif col == "entorno_transeunte":
            X["entorno_transeunte"] = z(np.log1p(c.loc[est, "entorno_transeunte"]))
        elif col == "tamaño":
            X["tamaño"] = z(np.log(tam.loc[est]))
        else:
            raise ValueError(col)
    assert not X.isna().any().any()
    return X


# ----------------------------------------------------------------------------- el modelo
class AjusteX:
    """NB con efecto aleatorio de estación (intercepto y, opcionalmente, pendiente) y covariables fijas."""

    def __init__(self, d: pd.DataFrame, X: pd.DataFrame | None, pendiente: bool, nodos: int | None = None):
        self.d = d.reset_index(drop=True)
        self.estaciones = sorted(d["estacion"].unique())
        self.anios = sorted(d["anio"].unique())
        self.s = self.d["estacion"].map({e: i for i, e in enumerate(self.estaciones)}).to_numpy()
        self.t = self.d["anio"].map({a: i for i, a in enumerate(self.anios)}).to_numpy()
        self.y = self.d["y"].to_numpy(float)
        self.logE = np.log(self.d["E"].to_numpy(float))
        self.S, self.T, self.N = len(self.estaciones), len(self.anios), len(self.d)
        self.X = np.zeros((self.S, 0)) if X is None else X.loc[self.estaciones].to_numpy(float)
        self.nombres_beta = [] if X is None else list(X.columns)
        self.p = self.X.shape[1]
        self.q = 2 if pendiente else 1
        self.t_medio = float(np.mean(self.anios))
        dt = self.d["anio"].to_numpy(float) - self.t_medio
        self.Z = np.column_stack([np.ones(self.N), dt]) if pendiente else np.ones((self.N, 1))
        K = nodos or (25 if self.q == 1 else 15)
        x1, w1 = np.polynomial.hermite.hermgauss(K)
        self.z = np.array(list(itertools.product(x1, repeat=self.q)))            # M × q
        self.logw = np.log(np.array(list(itertools.product(w1, repeat=self.q)))).sum(1) + (self.z ** 2).sum(1)
        self.M = len(self.z)

    # parámetros: alpha, gamma_1..T-1, beta_1..p, log sigma, [log tau], log phi
    def desempaca(self, th):
        i = 0
        alpha = th[i]; i += 1
        g = np.append(th[i:i + self.T - 1], -th[i:i + self.T - 1].sum()); i += self.T - 1
        beta = th[i:i + self.p]; i += self.p
        sd = np.exp(th[i:i + self.q]); i += self.q
        phi = np.exp(th[i])
        return alpha, g, beta, sd, phi

    def inicial(self):
        tasa = self.y.sum() / np.exp(self.logE).sum()
        th = [np.log(tasa)] + [0.0] * (self.T - 1) + [0.0] * self.p + [np.log(0.4)] + ([np.log(0.1)] if self.q == 2 else []) + [np.log(16.0)]
        return np.array(th)

    def logp(self, eta, phi, y):
        mu = np.exp(eta)
        return (gammaln(y + phi) - gammaln(phi) - gammaln(y + 1) + phi * (np.log(phi) - np.log(phi + mu)) + y * (eta - np.log(phi + mu)))

    def derivadas(self, eta, phi):
        mu = np.exp(eta)
        return (self.y - mu) * phi / (phi + mu), -mu * phi * (phi + self.y) / (phi + mu) ** 2

    def moda(self, base, sd, phi):
        """Moda de la posterior de u(s) y su hessiano (negativo definido), Newton por estación, vectorizado."""
        Dinv = 1 / sd ** 2
        U = np.zeros((self.S, self.q))
        H = np.zeros((self.S, self.q, self.q))
        for _ in range(100):
            eta = base + (self.Z * U[self.s]).sum(1)
            g1, g2 = self.derivadas(eta, phi)
            G = np.column_stack([np.bincount(self.s, self.Z[:, k] * g1, self.S) for k in range(self.q)]) - Dinv * U
            for k in range(self.q):
                for l in range(self.q):
                    H[:, k, l] = np.bincount(self.s, self.Z[:, k] * self.Z[:, l] * g2, self.S) - (Dinv[k] if k == l else 0.0)
            paso = np.linalg.solve(H, G[:, :, None])[:, :, 0]
            paso = np.clip(paso, -5, 5)
            U = U - paso
            if np.abs(paso).max() < 1e-10:
                break
        return U, H

    def _nodos(self, U, H):
        """Nodos adaptativos u = u0 + sqrt(2)·L·z con L·L' = (−H)⁻¹, y el log del jacobiano."""
        Sig = np.linalg.inv(-H)
        L = np.linalg.cholesky(Sig)                                               # S × q × q
        nodos = U[:, None, :] + np.sqrt(2) * np.einsum("sij,mj->smi", L, self.z)  # S × M × q
        logjac = self.q / 2 * np.log(2) + np.log(np.linalg.det(L))
        return nodos, logjac

    def _lp_nodos(self, base, sd, phi, nodos):
        """Log-verosimilitud + log-prior en cada nodo, por estación: S × M."""
        eta = base[:, None] + np.einsum("nk,nmk->nm", self.Z, nodos[self.s])      # N × M
        lp = np.zeros((self.S, self.M))
        np.add.at(lp, self.s, self.logp(eta, phi, self.y[:, None]))
        lp += stats.norm.logpdf(nodos, 0, sd).sum(2)
        return lp

    def base(self, th):
        alpha, g, beta, sd, phi = self.desempaca(th)
        return self.logE + alpha + g[self.t] + (self.X @ beta)[self.s], sd, phi

    def negloglik(self, th):
        base, sd, phi = self.base(th)
        U, H = self.moda(base, sd, phi)
        nodos, logjac = self._nodos(U, H)
        lp = self._lp_nodos(base, sd, phi, nodos) + self.logw[None, :]
        return -(logjac + logsumexp(lp, axis=1)).sum()

    def ajusta(self):
        """L-BFGS-B con cotas en las desviaciones y en phi, y después BFGS para afinar.

        Sin cotas, BFGS se detiene por «pérdida de precisión» en los modelos con pendiente:
        con tres o cuatro años por estación la pendiente absorbe la sobredispersión y phi se
        va a infinito (la Poisson), dejando una dirección plana. La cota phi ≤ 10,000 es la
        Poisson a efectos prácticos y se reporta como tal.
        """
        th0 = self.inicial()
        n = len(th0)
        cotas = [(None, None)] * (n - self.q - 1) + [(np.log(1e-3), np.log(5))] * self.q + [(np.log(0.5), np.log(1e4))]
        r = optimize.minimize(self.negloglik, th0, method="L-BFGS-B", bounds=cotas, options={"maxiter": 2000, "ftol": 1e-12, "gtol": 1e-7})
        r2 = optimize.minimize(self.negloglik, r.x, method="BFGS", options={"gtol": 1e-6, "maxiter": 1000})
        if r2.fun <= r.fun and np.all(np.isfinite(r2.x)):
            r = r2
        self.th, self.loglik, self.k = r.x, -r.fun, len(r.x)
        self.aic = 2 * self.k - 2 * self.loglik
        self.gradiente = float(np.linalg.norm(optimize.approx_fprime(r.x, self.negloglik, 1e-6)))
        self.convergio = self.gradiente < 1e-2
        self.phi_en_cota = bool(r.x[-1] >= np.log(1e4) - 1e-6)
        return self

    def errores(self):
        n, h = len(self.th), 1e-4
        Hm = np.zeros((n, n))
        f = self.negloglik
        for i in range(n):
            for j in range(i, n):
                ei, ej = np.eye(n)[i] * h, np.eye(n)[j] * h
                Hm[i, j] = Hm[j, i] = (f(self.th + ei + ej) - f(self.th + ei - ej) - f(self.th - ei + ej) + f(self.th - ei - ej)) / (4 * h * h)
        return np.sqrt(np.diag(np.linalg.inv(Hm)))

    def predice(self, anio: int) -> pd.Series:
        """Tasa predicha (denuncias por millón, año medio) para el año `anio`: exp(alpha + x'beta)·E[exp(v + b·dt)]."""
        base, sd, phi = self.base(self.th)
        alpha, g, beta, sd, phi = self.desempaca(self.th)
        U, H = self.moda(base, sd, phi)
        nodos, _ = self._nodos(U, H)
        lp = self._lp_nodos(base, sd, phi, nodos) + self.logw[None, :]
        pesos = np.exp(lp - logsumexp(lp, axis=1, keepdims=True))
        a = np.array([1.0, anio - self.t_medio]) if self.q == 2 else np.array([1.0])
        esperanza = (pesos * np.exp(nodos @ a)).sum(1)
        return pd.Series(np.exp(alpha + self.X @ beta) * esperanza, index=self.estaciones, name="tasa")


# ----------------------------------------------------------------------------- evaluación
def arma_v(d_tr, d_te, tasa: pd.Series) -> pd.DataFrame:
    crudo = d_tr.groupby("estacion").agg(conteo=("y", "sum"), E_tr=("E", "sum"))
    v = pd.DataFrame({"tasa": tasa, "conteo": crudo["conteo"], "E_tr": crudo["E_tr"], "y_obs": d_te["y"], "E_obs": d_te["E"]}).dropna()
    v["lugar_conteo"] = v["conteo"].rank(ascending=False, method="first")
    v["lugar_tasa"] = v["tasa"].rank(ascending=False, method="first")
    return v


def metricas(v: pd.DataFrame) -> dict:
    tasa_obs = v["y_obs"] / v["E_obs"]
    p = v["tasa"] * v["E_obs"]
    p = p / p.sum()
    return {"rho": modelo.spearman(v["tasa"], tasa_obs), "log_multinomial": float((v["y_obs"] * np.log(p)).sum())}


def cobertura(v: pd.DataFrame, k: int) -> dict:
    out = {}
    for nombre, regla in (("tasa", lista.r_tasa), ("conteo", lista.r_conteo), ("combinada", lista.r_combinada)):
        c = lista.cubre(v, regla(v)[:k])
        out[f"{nombre}_por_millon"] = c["por_millon"]
        out[f"{nombre}_denuncias"] = c["denuncias_cubiertas"]
        out[f"{nombre}_entradas_M"] = c["entradas_M"]
    return out


def main() -> int:
    t0 = time.time()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    panel = pd.read_csv(PANEL, dtype={"lineas": str})
    cov = pd.read_csv(COVARIABLES, dtype={"linea": str})

    # ------------------------------------------------------------ ajustes rodantes
    vs: dict[tuple[str, int], pd.DataFrame] = {}
    filas, pred = [], []
    for anio, entrena in PRUEBAS.items():
        d_tr = modelo.panel_anual(panel, excluye_r2=True, anios=entrena)
        d_te = modelo.panel_anual(panel, excluye_r2=True, anios=range(anio, anio + 1)).set_index("estacion")
        for nombre, (cols, pendiente) in MODELOS.items():
            X = disenio(d_tr, cov, cols) if cols else None
            aj = AjusteX(d_tr, X, pendiente).ajusta()
            assert aj.convergio, f"{nombre} {anio} no convergió (gradiente {aj.gradiente:.3g})"
            v = arma_v(d_tr, d_te, aj.predice(anio))
            vs[(nombre, anio)] = v
            m = metricas(v)
            alpha, g, beta, sd, phi = aj.desempaca(aj.th)
            for k in KS:
                filas.append({"modelo": nombre, "anio_prueba": anio, "k": k, "parametros": aj.k, "estaciones_prueba": len(v),
                              "denuncias_prueba": int(v["y_obs"].sum()), **cobertura(v, k), **m,
                              "sigma_v": round(float(sd[0]), 4), "tau": round(float(sd[1]), 4) if pendiente else None, "phi": round(float(phi), 2)})
            pred.append(v[["tasa", "conteo", "y_obs", "E_obs"]].assign(modelo=nombre, anio_prueba=anio).reset_index(names="estacion"))
            print(f"  {anio} {nombre:18s} k={aj.k:2d} sigma_v={sd[0]:.3f}" + (f" tau={sd[1]:.3f}" if pendiente else "") +
                  f" phi={phi:5.1f}  rho={m['rho']:.3f}  top10 tasa {cobertura(v, 10)['tasa_por_millon']:.3f}  [{time.time() - t0:.0f} s]")
    ev = pd.DataFrame(filas)
    ev.to_csv(TABLAS / "covariables_evaluacion.csv", index=False)
    pd.concat(pred, ignore_index=True).round(4).to_csv(TABLAS / "covariables_predicciones.csv", index=False)

    # ------------------------------------------------------------ el base debe reproducir M5, M6 y la decisión 65
    diag = json.loads((TABLAS / "modelo_diagnostico.json").read_text())
    c24 = pd.read_csv(TABLAS / "tres_listas_cobertura_2024.csv").set_index(["k", "lista"])
    b24 = ev[(ev["modelo"] == "base") & (ev["anio_prueba"] == 2024)].set_index("k")
    assert abs(b24.loc[10, "rho"] - diag["spearman_fuera_de_muestra"]["tasa_predicha"]) < 1e-3, "el base no reproduce M5"
    for k in KS:
        for l, col in (("tasa", "tasa"), ("conteo", "conteo"), ("propuesta", "combinada")):
            assert b24.loc[k, f"{col}_denuncias"] == c24.loc[(k, l), "denuncias_cubiertas"], f"el base no reproduce la decisión 65 ({k}, {l})"
    print("\nEl modelo base reproduce M5 (ρ 2024) y las coberturas de 2024 de la decisión 65.")

    # ------------------------------------------------------------ tabla principal
    print("\n" + "=" * 110 + "\nDenuncias por millón cubiertas por el top-k por tasa predicha (métrica primaria)\n")
    piv = ev.pivot_table(index="modelo", columns=["anio_prueba", "k"], values="tasa_por_millon").loc[list(MODELOS)]
    print(piv.round(3).to_string())
    print("\nρ de Spearman, tasa predicha contra observada\n")
    rho = ev[ev["k"] == 10].pivot_table(index="modelo", columns="anio_prueba", values="rho").loc[list(MODELOS)]
    print(rho.round(3).to_string())
    print("\nLog-verosimilitud multinomial (más alta es mejor), diferencia contra el base\n")
    lm = ev[ev["k"] == 10].pivot_table(index="modelo", columns="anio_prueba", values="log_multinomial").loc[list(MODELOS)]
    print((lm - lm.loc["base"]).round(2).to_string())

    # ------------------------------------------------------------ bootstrap pareado sobre estaciones
    print("\n" + "=" * 110 + f"\nBootstrap pareado sobre estaciones ({REMUESTRAS} remuestras, semilla {SEMILLA})\n")
    rng = np.random.default_rng(SEMILLA)
    indices = {anio: [rng.integers(0, len(vs[("base", anio)]), len(vs[("base", anio)])) for _ in range(REMUESTRAS)] for anio in PRUEBAS}
    boot_filas, drho_prom = [], {}

    def rho_np(tasa, y, E):
        return float(np.corrcoef(stats.rankdata(tasa), stats.rankdata(y / E))[0, 1])

    def por_millon_topk(tasa, y, E, k):
        top = np.argsort(-tasa, kind="stable")[:k]
        return y[top].sum() / E[top].sum()

    for nombre in MODELOS:
        if nombre == "base":
            continue
        drho = np.zeros((REMUESTRAS, len(PRUEBAS)))
        for j, anio in enumerate(PRUEBAS):
            vb, vm = vs[("base", anio)], vs[(nombre, anio)]
            assert list(vb.index) == list(vm.index)
            tb, tm = vb["tasa"].to_numpy(), vm["tasa"].to_numpy()
            y, E = vb["y_obs"].to_numpy(), vb["E_obs"].to_numpy()
            dif = {k: np.zeros(REMUESTRAS) for k in KS}
            for i, idx in enumerate(indices[anio]):
                drho[i, j] = rho_np(tm[idx], y[idx], E[idx]) - rho_np(tb[idx], y[idx], E[idx])
                u = np.unique(idx)  # una estación no puede elegirse dos veces para la lista (igual que en 09)
                for k in KS:
                    dif[k][i] = por_millon_topk(tm[u], y[u], E[u], k) - por_millon_topk(tb[u], y[u], E[u], k)
            for k in KS:
                d = dif[k]
                boot_filas.append({"modelo": nombre, "anio_prueba": anio, "k": k, "dif_por_millon_media": round(float(d.mean()), 3),
                                   "ic95_inf": round(float(np.quantile(d, .025)), 3), "ic95_sup": round(float(np.quantile(d, .975)), 3),
                                   "p_mejor_que_base": round(float((d > 0).mean()), 3),
                                   "dif_rho_media": round(float(drho[:, j].mean()), 3), "p_rho_mejor": round(float((drho[:, j] > 0).mean()), 3)})
        drho_prom[nombre] = float((drho.mean(1) > 0).mean())
        print(f"  {nombre:18s} P(Δρ promedio de los tres años > 0) = {drho_prom[nombre]:.3f}  [{time.time() - t0:.0f} s]")
    boot = pd.DataFrame(boot_filas)
    boot.to_csv(TABLAS / "covariables_bootstrap.csv", index=False)
    print(boot.to_string(index=False))

    # ------------------------------------------------------------ veredicto, con el criterio de la decisión 66
    print("\n" + "=" * 110 + "\nVeredicto (criterio de la decisión 66)\n")
    ver = []
    for nombre in MODELOS:
        if nombre == "base":
            continue
        d_pm = (piv.loc[nombre] - piv.loc["base"]).to_numpy()
        d_rho = (rho.loc[nombre] - rho.loc["base"]).to_numpy()
        a = int((d_pm > 0).sum()) >= 4 and float(np.median(d_pm)) > 0
        b = int((d_rho > 0).sum()) >= 2
        c = drho_prom[nombre] >= P_MINIMA
        ver.append({"modelo": nombre, "parametros_2024": int(ev[(ev["modelo"] == nombre) & (ev["anio_prueba"] == 2024)]["parametros"].iloc[0]),
                    "a_casos_por_millon_mejor_de_6": int((d_pm > 0).sum()), "a_mediana_dif_por_millon": round(float(np.median(d_pm)), 3), "a_cumple": a,
                    "b_anios_rho_mejor_de_3": int((d_rho > 0).sum()), "b_dif_rho_media": round(float(d_rho.mean()), 3), "b_cumple": b,
                    "c_p_rho_promedio_positivo": round(drho_prom[nombre], 3), "c_cumple": c, "mejora": a and b and c})
    ver = pd.DataFrame(ver)
    ver.to_csv(TABLAS / "covariables_veredicto.csv", index=False)
    print(ver.to_string(index=False))
    ganadores = ver[ver["mejora"]].sort_values("parametros_2024")
    ganador = ganadores["modelo"].iloc[0] if len(ganadores) else None
    print(f"\n→ {'MEJORA: ' + ganador + ' (el de menos parámetros entre los que cumplen)' if ganador else 'NINGÚN modelo cumple el criterio: la señal sigue débil con más información.'}")

    # ------------------------------------------------------------ ajuste completo 2019–2024: cuánto explican las covariables
    print("\n" + "=" * 110 + "\nAjuste completo 2019–2024 (descripción, no criterio)\n")
    d_full = modelo.panel_anual(panel, excluye_r2=True, anios=range(2019, 2025))
    completo, coefs, base_ll = [], [], None
    for nombre, (cols, pendiente) in MODELOS.items():
        X = disenio(d_full, cov, cols) if cols else None
        aj = AjusteX(d_full, X, pendiente).ajusta()
        alpha, g, beta, sd, phi = aj.desempaca(aj.th)
        ee = aj.errores()
        if nombre == "base":
            base_ll, base_k = aj.loglik, aj.k
        lr = 2 * (aj.loglik - base_ll)
        gl = aj.k - base_k
        completo.append({"modelo": nombre, "parametros": aj.k, "loglik": round(aj.loglik, 2), "AIC": round(aj.aic, 2),
                         "LR_vs_base": round(lr, 2), "gl": gl, "p_LR": None if gl == 0 else round(float(stats.chi2.sf(lr, gl)), 4),
                         "tasa_base_mm": round(float(np.exp(alpha)), 3), "sigma_v": round(float(sd[0]), 4),
                         "tau": round(float(sd[1]), 4) if pendiente else None, "phi": round(float(phi), 2), "convergio": aj.convergio})
        i0 = aj.T  # alpha + T-1 gammas
        for j, nb in enumerate(aj.nombres_beta):
            coefs.append({"modelo": nombre, "coeficiente": nb, "beta": round(float(beta[j]), 4), "ee": round(float(ee[i0 + j]), 4),
                          "exp_beta": round(float(np.exp(beta[j])), 3)})
        print(f"  {nombre:18s} k={aj.k:2d} loglik={aj.loglik:9.2f} AIC={aj.aic:8.1f} LR={lr:6.2f} gl={gl:2d} sigma_v={sd[0]:.3f}"
              + (f" tau={sd[1]:.3f}" if pendiente else "") + f" phi={phi:.1f}  [{time.time() - t0:.0f} s]")
    pd.DataFrame(completo).to_csv(TABLAS / "covariables_ajuste_completo.csv", index=False)
    co = pd.DataFrame(coefs)
    co.to_csv(TABLAS / "covariables_coeficientes.csv", index=False)
    print("\nCoeficientes del modelo con todas las fijas (ajuste completo):")
    print(co[co["modelo"] == "todas las fijas"].to_string(index=False))
    sv = {r["modelo"]: r["sigma_v"] for r in completo}
    print(f"\nσ_v: base {sv['base']:.3f} → todas las fijas {sv['todas las fijas']:.3f}: las covariables explican el "
          f"{100 * (1 - sv['todas las fijas'] ** 2 / sv['base'] ** 2):.0f} % de la varianza entre estaciones (en escala log).")

    # ------------------------------------------------------------ las tres listas con el ganador (o el base, si no hay)
    quien = ganador or "base"
    print("\n" + "=" * 110 + f"\nLas tres listas evaluadas con el modelo «{quien}»\n")
    tl = ev[ev["modelo"] == quien][["anio_prueba", "k", "conteo_denuncias", "conteo_por_millon", "tasa_denuncias", "tasa_por_millon",
                                     "combinada_denuncias", "combinada_por_millon"]].assign(modelo=quien)
    tl.to_csv(TABLAS / "covariables_tres_listas.csv", index=False)
    print(tl.to_string(index=False))
    (TABLAS / "covariables_resumen.json").write_text(json.dumps({
        "ganador": ganador, "modelos": list(MODELOS), "anios_prueba": list(PRUEBAS), "remuestras": REMUESTRAS, "semilla": SEMILLA,
        "p_rho_promedio_positivo": drho_prom, "sigma_v_completo": sv}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nListo en {time.time() - t0:.0f} s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

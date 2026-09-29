"""
subcontracting-make-or-buy
--------------------------
Modelo "make or buy" para decidir que perfiles subcontratados conviene internalizar.

Inspirado en mi practica profesional en una consultora ambiental. Todos los datos
son SIMULADOS; no se usa informacion de la empresa.

Pasos:
  1. Genera un historial de ordenes de subcontratacion por especialista (SQLite).
  2. Consolida el historial con SQL (trazabilidad: meses activos, costo, continuidad).
  3. Compara costo subcontratado vs costo de contratar internamente
     (sueldo bruto + cargas + costos indirectos).
  4. Recomienda internalizar perfiles con demanda continua y ahorro positivo,
     e incluye un analisis de sensibilidad.

Uso:
  python make_or_buy.py --seed 3
"""
from __future__ import annotations

import argparse
import sqlite3

import numpy as np
import pandas as pd

MONTHS = pd.period_range("2024-01", "2025-12", freq="M")

# (perfil, costo mensual subcontratado CLP, sueldo bruto interno CLP, prob. de demanda mensual)
PROFILES = [
    ("Especialista SIG", 4_200_000, 2_400_000, 0.95),
    ("Ingeniero ambiental senior", 4_300_000, 2_550_000, 0.92),
    ("Especialista en fauna", 4_100_000, 2_350_000, 0.90),
    ("Hidrogeologo", 4_250_000, 2_500_000, 0.88),
    ("Arqueologo", 3_600_000, 2_300_000, 0.35),
    ("Especialista en ruido", 3_200_000, 2_100_000, 0.30),
    ("Abogado ambiental", 4_800_000, 3_300_000, 0.25),
]
EMPLOYER_COSTS = 0.12     # cargas del empleador (supuesto)
OVERHEAD = 0.10           # puesto de trabajo, licencias, gestion (supuesto)
MIN_CONTINUITY = 0.80     # % de meses con demanda para considerar internalizar


def build_db(rng: np.random.Generator) -> sqlite3.Connection:
    rows = []
    for name, cost, _, p in PROFILES:
        for m in MONTHS:
            if rng.random() < p:
                noise = rng.normal(1, 0.04)
                rows.append((name, str(m), round(cost * noise, -3)))
    con = sqlite3.connect(":memory:")
    pd.DataFrame(rows, columns=["perfil", "mes", "monto_clp"]).to_sql("ordenes", con, index=False)
    pd.DataFrame([(n, s) for n, _, s, _ in PROFILES],
                 columns=["perfil", "sueldo_bruto_clp"]).to_sql("mercado", con, index=False)
    return con


CONSOLIDATION_SQL = f"""
SELECT o.perfil,
       COUNT(DISTINCT o.mes)                          AS meses_activos,
       ROUND(COUNT(DISTINCT o.mes) * 1.0 / {len(MONTHS)}, 2) AS continuidad,
       ROUND(AVG(o.monto_clp), 0)                     AS costo_sub_mensual,
       SUM(o.monto_clp)                               AS gasto_total,
       m.sueldo_bruto_clp
FROM ordenes o
JOIN mercado m USING (perfil)
GROUP BY o.perfil
ORDER BY gasto_total DESC;
"""


def evaluate(df: pd.DataFrame, employer: float, overhead: float) -> pd.DataFrame:
    out = df.copy()
    out["costo_interno_mensual"] = (out.sueldo_bruto_clp * (1 + employer + overhead)).round(-3)
    out["ahorro_mensual"] = out.costo_sub_mensual - out.costo_interno_mensual
    # el interno se paga los 12 meses; el subcontrato solo los meses con demanda
    out["ahorro_anual_esperado"] = (12 * (out.continuidad * out.costo_sub_mensual
                                          - out.costo_interno_mensual)).round(-3)
    out["recomendacion"] = np.where(
        (out.continuidad >= MIN_CONTINUITY) & (out.ahorro_anual_esperado > 0),
        "INTERNALIZAR", "mantener subcontrato")
    return out


def clp(x: float) -> str:
    return f"${x:,.0f}".replace(",", ".")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=3)
    args = ap.parse_args()

    con = build_db(np.random.default_rng(args.seed))
    base = pd.read_sql(CONSOLIDATION_SQL, con)
    res = evaluate(base, EMPLOYER_COSTS, OVERHEAD)

    show = res[["perfil", "continuidad", "costo_sub_mensual", "costo_interno_mensual",
                "ahorro_mensual", "ahorro_anual_esperado", "recomendacion"]].copy()
    for c in ["costo_sub_mensual", "costo_interno_mensual", "ahorro_mensual", "ahorro_anual_esperado"]:
        show[c] = show[c].map(clp)
    print("\n=== Analisis make-or-buy (datos simulados) ===")
    print(show.to_string(index=False))

    chosen = res[res.recomendacion == "INTERNALIZAR"]
    print(f"\nPerfiles a internalizar: {len(chosen)}")
    print(f"Ahorro mensual promedio por persona: {clp(chosen.ahorro_mensual.mean())}")
    print(f"Ahorro anual esperado total: {clp(chosen.ahorro_anual_esperado.sum())}")

    print("\n=== Sensibilidad: ahorro anual total segun costos indirectos ===")
    for oh in (0.05, 0.10, 0.20, 0.30):
        r = evaluate(base, EMPLOYER_COSTS, oh)
        sel = r[r.recomendacion == "INTERNALIZAR"]
        print(f"overhead {oh:>4.0%}: {len(sel)} perfiles, ahorro {clp(sel.ahorro_anual_esperado.sum())}")


if __name__ == "__main__":
    main()

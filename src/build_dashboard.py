"""Export the data behind the interactive dashboard to docs/data.js.

The dashboard (docs/index.html) is a static page, so it can be hosted free on GitHub Pages.
Everything it shows is pre-aggregated here into small additive cells (state x month),
so the page can re-total any filter combination in the browser.
"""
import json
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "warehouse.duckdb"
OUT = ROOT / "docs" / "data.js"

STATE_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Federal District", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}

CELL_SQL_TEMPLATE = """
with o as (
    select
        customer_state as st,
        strftime(purchase_month, '%Y-%m') as m,
        is_late, review_score, actual_days, promised_days, days_vs_promise, missed_ship_by,
        case
            when days_vs_promise <= -15 then 0 when days_vs_promise <= -8 then 1
            when days_vs_promise <= -1  then 2 when days_vs_promise = 0  then 3
            when days_vs_promise <= 3   then 4 when days_vs_promise <= 7 then 5
            when days_vs_promise <= 14  then 6 else 7
        end as bucket
    from mart.fct_orders
    where is_delivered
)
select
    st, m,
    count(*)                                                      as n,
    sum(is_late::int)                                             as late,
    sum(promised_days)                                            as prom,
    sum(actual_days)                                              as act,
    count(review_score) filter (where not is_late)                as rv_on,
    count(review_score) filter (where is_late)                    as rv_late,
    coalesce(sum(review_score) filter (where not is_late), 0)     as sc_on,
    coalesce(sum(review_score) filter (where is_late), 0)         as sc_late,
    count(*) filter (where review_score = 1 and not is_late)      as one_on,
    count(*) filter (where review_score = 1 and is_late)          as one_late,
    count(*) filter (where missed_ship_by)                        as missed,
    -- review buckets: count and score sum for each of the 8 arrival-vs-promise buckets
    {bucket_cols},
    -- late orders if every promise had b extra days, b = 0..10
    {buffer_cols}
from o
group by st, m
order by st, m
"""

CELL_SQL = CELL_SQL_TEMPLATE.format(
    bucket_cols=",\n    ".join(
        [f"count(review_score) filter (where bucket = {i}) as b_n{i}" for i in range(8)]
        + [f"coalesce(sum(review_score) filter (where bucket = {i}), 0) as b_s{i}" for i in range(8)]),
    buffer_cols=",\n    ".join(f"sum((actual_days > promised_days + {b})::int) as buf{b}" for b in range(11)),
)


def build() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    cells = con.execute(CELL_SQL).df()
    con.close()
    metrics = json.loads((ROOT / "outputs" / "metrics.json").read_text())
    sellers = pd.read_csv(ROOT / "outputs" / "sql" / "08_seller_habits.csv")

    cols = ["n", "late", "prom", "act", "rv_on", "rv_late", "sc_on", "sc_late", "one_on", "one_late", "missed"]
    rows = []
    for r in cells.itertuples(index=False):
        rows.append([r.st, r.m] + [int(getattr(r, c)) for c in cols]
                    + [[int(getattr(r, f"b_n{i}")) for i in range(8)],
                       [int(getattr(r, f"b_s{i}")) for i in range(8)],
                       [int(getattr(r, f"buf{b}")) for b in range(11)]])

    data = {
        "cols": ["st", "m"] + cols + ["b_n", "b_s", "buf_late"],
        "cells": rows,
        "states": STATE_NAMES,
        "buckets": ["15+ days early", "8-14 days early", "1-7 days early", "On the day",
                    "1-3 days late", "4-7 days late", "8-14 days late", "15+ days late"],
        "sellers": [[round(a, 4), round(b, 4), round(c, 4), round(d, 4)] for a, b, c, d in
                    sellers[["late_rate_2017", "late_rate_2018", "missed_ship_by_2017", "missed_ship_by_2018"]].itertuples(index=False)],
        "metrics": {
            "review_penalty": metrics["review_penalty"],
            "repeat_purchase": metrics["repeat_purchase"],
            "seller_habits": metrics["seller_habits"],
            "handoff": metrics["handoff"],
            "holiday": metrics["holiday_vs_year_round"],
            "holiday_2017": metrics["holiday_2017"],
            "sizing": metrics["sizing"],
            "waves": metrics["waves"],
            "buffer_2018": metrics["buffer_2018"],
            "formula_backtest": metrics["formula_backtest"],
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("window.DASH = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print(f"  wrote docs/data.js ({OUT.stat().st_size / 1024:.0f} KB, {len(rows)} cells)")


if __name__ == "__main__":
    build()

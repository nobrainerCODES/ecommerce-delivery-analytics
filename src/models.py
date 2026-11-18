"""Statistical tests, backtests and sizing.

Reads the warehouse and the SQL outputs, then writes:
  outputs/model/*.csv     tables behind each chart
  outputs/metrics.json    every number quoted in the README and memo
"""
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from src.run_sql_analysis import run_query

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "warehouse.duckdb"
SQL_OUT = ROOT / "outputs" / "sql"
OUT = ROOT / "outputs" / "model"


def sql_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(SQL_OUT / f"{name}.csv")


# ---------------------------------------------------------------------------
# 1. Does the promise matter more than the wait?
# ---------------------------------------------------------------------------
def review_penalty(con) -> dict:
    """OLS of review score on a late flag and delivery days, with state, month and order value controls."""
    df = con.execute("""
        select review_score, is_late::int as late, least(actual_days, 60) as actual_days,
               customer_state, strftime(purchase_month, '%Y-%m') as month, ln(1 + items_value) as log_value
        from mart.fct_orders
        where is_delivered and review_score is not null and actual_days >= 0
    """).df()
    main = smf.ols(
        "review_score ~ late + actual_days + C(customer_state) + C(month) + log_value", data=df
    ).fit(cov_type="HC1")
    # Robustness: let every single delivery day have its own effect instead of a straight line.
    flexible = smf.ols(
        "review_score ~ late + C(actual_days) + C(customer_state) + C(month) + log_value", data=df
    ).fit(cov_type="HC1")
    late, per_day = main.params["late"], main.params["actual_days"]
    ci = main.conf_int().loc["late"]
    fci = flexible.conf_int().loc["late"]
    return {
        "n": int(main.nobs),
        "late_penalty_stars": float(late),
        "late_penalty_ci95": [float(ci[0]), float(ci[1])],
        "per_extra_day_stars": float(per_day),
        "late_equals_this_many_extra_days": float(late / per_day),
        "r_squared": float(main.rsquared),
        "robustness_flexible_days_penalty": float(flexible.params["late"]),
        "robustness_flexible_days_ci95": [float(fci[0]), float(fci[1])],
    }


# ---------------------------------------------------------------------------
# 2. Do late first orders lower repeat buying?
# ---------------------------------------------------------------------------
def repeat_purchase(con) -> dict:
    df = run_query(con, "10_repeat_purchase")
    df["log_value"] = np.log1p(df["items_value"])
    raw = df.groupby("late")["repeated_180d"].mean()
    lpm = smf.ols(
        "repeated_180d ~ late + C(customer_state) + C(purchase_month) + log_value", data=df
    ).fit(cov_type="HC1")
    ci = lpm.conf_int().loc["late"]
    return {
        "first_orders": int(len(df)),
        "repeat_rate_overall": float(df["repeated_180d"].mean()),
        "repeat_rate_on_time": float(raw[0]),
        "repeat_rate_late": float(raw[1]),
        "controlled_effect_pts": float(lpm.params["late"] * 100),
        "controlled_effect_ci95_pts": [float(ci[0] * 100), float(ci[1] * 100)],
        "p_value": float(lpm.pvalues["late"]),
    }


# ---------------------------------------------------------------------------
# 3. Which seller metrics are habits?
# ---------------------------------------------------------------------------
def pearson_ci(r: float, n: int) -> list:
    """95% confidence interval for a correlation using the Fisher z transform."""
    z, se = np.arctanh(r), 1 / np.sqrt(n - 3)
    return [float(np.tanh(z - 1.96 * se)), float(np.tanh(z + 1.96 * se))]


def seller_habits() -> dict:
    s = sql_csv("08_seller_habits")
    n = len(s)
    r_late = s["late_rate_2017"].corr(s["late_rate_2018"])
    r_ship = s["missed_ship_by_2017"].corr(s["missed_ship_by_2018"])
    return {
        "sellers": n,
        "late_rate_corr": float(r_late),
        "late_rate_corr_ci95": pearson_ci(r_late, n),
        "late_rate_spearman": float(s["late_rate_2017"].corr(s["late_rate_2018"], method="spearman")),
        "missed_ship_by_corr": float(r_ship),
        "missed_ship_by_corr_ci95": pearson_ci(r_ship, n),
        "missed_ship_by_spearman": float(s["missed_ship_by_2017"].corr(s["missed_ship_by_2018"], method="spearman")),
    }


# ---------------------------------------------------------------------------
# 4. Can a simple formula beat Olist's own promise date?
# ---------------------------------------------------------------------------
def formula_backtest(con) -> pd.DataFrame:
    """Walk-forward test on 2018. Each month, a route rule is fit only on orders that were already delivered
    before that month started (purchased 45 to 365 days earlier, so slow orders are not missing).
    Route rule: promise = the q-th percentile of past delivery days for that seller-state to customer-state route.
    Olist curve: Olist's own promise plus 0 to 10 buffer days (from 11_buffer_tradeoff)."""
    df = con.execute("""
        select purchase_date, cast(delivered_at as date) as delivered_date, actual_days, promised_days,
               route, customer_state
        from mart.fct_orders
        where is_delivered and route is not null
    """).df()
    df["purchase_date"] = pd.to_datetime(df["purchase_date"])
    df["delivered_date"] = pd.to_datetime(df["delivered_date"])
    months = pd.period_range("2018-01", "2018-08", freq="M")
    rows = []
    for q in [0.80, 0.85, 0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98]:
        parts = []
        for m in months:
            start, end = m.start_time, m.end_time
            hist = df[(df.purchase_date >= start - pd.Timedelta(days=365))
                      & (df.purchase_date < start - pd.Timedelta(days=45))
                      & (df.delivered_date < start)]
            route = hist.groupby("route")["actual_days"].agg(["count", lambda s, q=q: s.quantile(q)])
            route.columns = ["n", "qv"]
            route = route.loc[route["n"] >= 30, "qv"]
            state = hist.groupby("customer_state")["actual_days"].quantile(q)
            overall = hist["actual_days"].quantile(q)
            t = df[(df.purchase_date >= start) & (df.purchase_date <= end)].copy()
            t["rule_days"] = np.ceil(
                t["route"].map(route).fillna(t["customer_state"].map(state)).fillna(overall))
            parts.append(t)
        t = pd.concat(parts)
        rows.append({"method": "Route percentile rule", "setting": f"p{int(q * 100)}",
                     "avg_promised_days": t["rule_days"].mean(),
                     "late_rate": (t["actual_days"] > t["rule_days"]).mean()})
    # Same 2018 orders, Olist's own promise plus a flat buffer (the SQL version of this is 11_buffer_tradeoff).
    for b in range(0, 11):
        rows.append({"method": "Olist promise + buffer", "setting": f"+{b}d",
                     "avg_promised_days": (t["promised_days"] + b).mean(),
                     "late_rate": (t["actual_days"] > t["promised_days"] + b).mean()})
    return pd.DataFrame(rows)


def rule_vs_olist_at_same_late_rate(curve: pd.DataFrame) -> dict:
    """How many promise days does each method need to hit the same late rate? Linear interpolation on each curve."""
    out = {}
    for target in [0.05, 0.06]:
        vals = {}
        for method, g in curve.groupby("method"):
            g = g.sort_values("late_rate")
            vals[method] = float(np.interp(target, g["late_rate"], g["avg_promised_days"]))
        out[f"days_needed_for_{int(target * 100)}pct_late"] = vals
    return out


# ---------------------------------------------------------------------------
# 5. Holiday buffer vs the same cost spread over the whole year
# ---------------------------------------------------------------------------
def holiday_vs_year_round(con, buffer_days: int = 5) -> dict:
    df = con.execute("""
        select actual_days, promised_days,
               purchase_date between date '2017-11-20' and date '2017-12-31' as in_window
        from mart.fct_orders
        where is_delivered and year(purchase_date) = 2017
    """).df()
    base_late = int((df.actual_days > df.promised_days).sum())
    holiday_add = np.where(df.in_window, buffer_days, 0)
    holiday_late = int((df.actual_days > df.promised_days + holiday_add).sum())
    avg_cost = float(holiday_add.mean())
    # Year-round buffer with the same average cost. Days are whole numbers, so blend floor and ceil.
    lo = int(np.floor(avg_cost)); w = avg_cost - lo
    late_lo = (df.actual_days > df.promised_days + lo).sum()
    late_hi = (df.actual_days > df.promised_days + lo + 1).sum()
    year_round_late = float((1 - w) * late_lo + w * late_hi)
    return {
        "buffer_days": buffer_days,
        "orders_2017": int(len(df)),
        "late_orders_2017": base_late,
        "late_orders_with_holiday_buffer": holiday_late,
        "late_orders_avoided_holiday": base_late - holiday_late,
        "avg_added_promise_days": avg_cost,
        "late_orders_avoided_same_cost_year_round": float(base_late - year_round_late),
    }


# ---------------------------------------------------------------------------
# Run everything and size the levers
# ---------------------------------------------------------------------------
def run_all() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=True)

    kpi = sql_csv("01_headline_kpis").iloc[0]
    handoff = sql_csv("06_ship_by_handoff").set_index("missed_ship_by")
    time_split = sql_csv("07_where_the_time_goes").set_index("outcome")
    waves = sql_csv("09_late_waves")
    buffer = sql_csv("11_buffer_tradeoff").set_index("buffer_days")
    holiday = sql_csv("12_holiday_buffer").set_index("buffer_days")

    m = {}
    m["headline"] = {k: (v.item() if hasattr(v, "item") else v) for k, v in kpi.to_dict().items()}
    print("review penalty model ...")
    m["review_penalty"] = review_penalty(con)
    print("repeat purchase model ...")
    m["repeat_purchase"] = repeat_purchase(con)
    m["seller_habits"] = seller_habits()
    print("formula backtest ...")
    curve = formula_backtest(con)
    curve.to_csv(OUT / "formula_backtest.csv", index=False)
    m["formula_backtest"] = rule_vs_olist_at_same_late_rate(curve)
    m["holiday_vs_year_round"] = holiday_vs_year_round(con, buffer_days=5)

    late_base = int(handoff["late_orders"].sum())
    late_cf = int(handoff["late_orders_if_on_time_handoff"].sum())
    m["handoff"] = {
        "orders": int(handoff["orders"].sum()),
        "missed_share": float(handoff.loc[True, "orders"] / handoff["orders"].sum()),
        "late_rate_missed": float(handoff.loc[True, "late_rate"]),
        "late_rate_on_time_handoff": float(handoff.loc[False, "late_rate"]),
        "late_rate_ratio": float(handoff.loc[True, "late_rate"] / handoff.loc[False, "late_rate"]),
        "late_orders": late_base,
        "late_orders_if_every_handoff_on_time": late_cf,
        "late_orders_avoided": late_base - late_cf,
        "share_of_late_avoided": (late_base - late_cf) / late_base,
    }
    m["time_split"] = {
        "late_avg_seller_days": float(time_split.loc["Late", "avg_seller_days"]),
        "late_avg_carrier_days": float(time_split.loc["Late", "avg_carrier_days"]),
        "on_time_avg_seller_days": float(time_split.loc["On time", "avg_seller_days"]),
        "on_time_avg_carrier_days": float(time_split.loc["On time", "avg_carrier_days"]),
    }
    top3 = waves.sort_values("late_rank").head(3)
    m["waves"] = {
        "top3_months": [str(x)[:7] for x in top3["purchase_month"]],
        "top3_share_of_late": float(top3["cumulative_share_of_late"].iloc[-1]),
        "months_with_orders": int((waves["orders"] >= 500).sum()),
    }
    m["buffer_2018"] = {
        "late_rate_0": float(buffer.loc[0, "late_rate"]),
        "late_rate_1": float(buffer.loc[1, "late_rate"]),
        "late_rate_2": float(buffer.loc[2, "late_rate"]),
        "late_rate_3": float(buffer.loc[3, "late_rate"]),
        "avg_promised_days_0": float(buffer.loc[0, "avg_promised_days"]),
        "pts_per_day_first_3": float((buffer.loc[0, "late_rate"] - buffer.loc[3, "late_rate"]) / 3 * 100),
    }
    m["holiday_2017"] = {
        "window_orders": int(holiday.loc[0, "window_orders"]),
        "window_late_rate": float(holiday.loc[0, "window_late_rate"]),
        "rest_of_2017_late_rate": float(holiday.loc[0, "rest_of_2017_late_rate"]),
        "window_late_rate_plus5": float(holiday.loc[5, "window_late_rate"]),
        "window_late_orders": int(holiday.loc[0, "window_late_orders"]),
        "window_late_orders_plus5": int(holiday.loc[5, "window_late_orders"]),
    }

    # Sizing in reviews. Each late order avoided swaps the late 1-star rate for the on-time one.
    one_star_gap = m["headline"]["one_star_rate_late"] - m["headline"]["one_star_rate_on_time"]
    star_gap = m["headline"]["avg_review_late"] - m["headline"]["avg_review_on_time"]
    reviewed = m["headline"]["reviewed_orders"]
    review_share = reviewed / m["headline"]["delivered_orders"]

    def size(avoided: float) -> dict:
        return {
            "late_orders_avoided": float(avoided),
            "one_star_reviews_avoided": float(avoided * review_share * one_star_gap),
            "avg_rating_lift": float(-avoided * review_share * star_gap / reviewed),
        }

    m["sizing"] = {
        "one_star_rate_gap": float(one_star_gap),
        "ceiling_if_no_late_orders": size(m["headline"]["late_orders"]),
        "ship_by_compliance": size(m["handoff"]["late_orders_avoided"]),
        "holiday_buffer_5d": size(m["holiday_vs_year_round"]["late_orders_avoided_holiday"]),
    }
    # Both levers at once, counted on the same orders so overlap is not double counted.
    combined_late = con.execute("""
        select sum((
            case when missed_ship_by and handed_to_carrier_at is not null
                 then cast(delivered_at - (handed_to_carrier_at - ship_by_at) as date)
                 else cast(delivered_at as date) end
            > promised_date + case when purchase_date between date '2017-11-20' and date '2017-12-31'
                                   then 5 else 0 end
        )::int)
        from mart.fct_orders
        where is_delivered
    """).fetchone()[0]
    m["sizing"]["combined"] = size(m["headline"]["late_orders"] - combined_late)
    m["sizing"]["combined"]["share_of_late_avoided"] = float(
        (m["headline"]["late_orders"] - combined_late) / m["headline"]["late_orders"])

    (ROOT / "outputs" / "metrics.json").write_text(json.dumps(m, indent=2, default=str))
    con.close()
    print("wrote outputs/metrics.json")
    return m


if __name__ == "__main__":
    run_all()

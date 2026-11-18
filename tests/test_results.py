"""Checks on the analysis results, and that the README and memo quote the numbers the pipeline produced."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_results_are_in_a_sane_range(metrics):
    h = metrics["headline"]
    assert 0.05 < h["late_rate"] < 0.09
    assert h["avg_review_late"] < h["avg_review_on_time"]
    rp = metrics["review_penalty"]
    assert rp["late_penalty_ci95"][1] < 0          # being late lowers reviews, and the CI excludes zero
    assert rp["robustness_flexible_days_penalty"] < -1
    sh = metrics["seller_habits"]
    assert sh["missed_ship_by_corr"] > sh["late_rate_corr"]
    rr = metrics["repeat_purchase"]
    assert rr["p_value"] > 0.05                   # the README says this effect is not significant


def test_sizing_adds_up(metrics):
    s = metrics["sizing"]
    combined = s["combined"]["late_orders_avoided"]
    parts = s["ship_by_compliance"]["late_orders_avoided"] + s["holiday_buffer_5d"]["late_orders_avoided"]
    assert combined <= parts                      # overlap is removed, never added
    assert combined <= metrics["headline"]["late_orders"]


def expected_strings(m):
    h, rp, sh, ho, hol, sz, rr, w = (m["headline"], m["review_penalty"], m["seller_habits"], m["handoff"],
                                     m["holiday_vs_year_round"], m["sizing"], m["repeat_purchase"], m["waves"])
    return {
        "delivered orders": f"{h['delivered_orders']:,}",
        "late rate": f"{h['late_rate'] * 100:.1f}%",
        "share of 1-stars from late": f"{h['share_of_one_stars_from_late'] * 100:.0f}%",
        "avg review on time": f"{h['avg_review_on_time']:.2f}",
        "avg review late": f"{h['avg_review_late']:.2f}",
        "late penalty": f"{abs(rp['late_penalty_stars']):.2f} stars",
        "equivalent days": f"{rp['late_equals_this_many_extra_days']:.0f} extra days",
        "seller late r": f"r = {sh['late_rate_corr']:.2f}",
        "seller ship-by r": f"r = {sh['missed_ship_by_corr']:.2f}",
        "handoff avoided": f"{ho['late_orders_avoided']:,} fewer late orders",
        "holiday avoided": f"{hol['late_orders_avoided_holiday']:,} fewer late orders",
        "combined avoided": f"{sz['combined']['late_orders_avoided']:,.0f} late orders",
        "top 3 months share": f"{w['top3_share_of_late'] * 100:.0f}%",
        "repeat p value": f"p = {rr['p_value']:.2f}",
    }


def test_readme_matches_metrics(metrics):
    readme = (ROOT / "README.md").read_text()
    missing = {k: v for k, v in expected_strings(metrics).items() if v not in readme}
    assert not missing, f"README is out of date with outputs/metrics.json: {missing}"


def test_memo_matches_metrics(metrics):
    memo = (ROOT / "reports" / "memo.md").read_text()
    keys = ["late rate", "share of 1-stars from late", "late penalty", "seller late r", "seller ship-by r",
            "handoff avoided", "holiday avoided", "combined avoided", "top 3 months share", "repeat p value"]
    exp = expected_strings(metrics)
    missing = {k: exp[k] for k in keys if exp[k] not in memo}
    assert not missing, f"memo is out of date with outputs/metrics.json: {missing}"

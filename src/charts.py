"""Static charts for the README and memo, saved to reports/figures/*.png."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SQL_OUT = ROOT / "outputs" / "sql"
MODEL_OUT = ROOT / "outputs" / "model"
FIG = ROOT / "reports" / "figures"

# Palette (validated with a CVD check): blue = on time / main series, orange = late / comparison.
BLUE, ORANGE = "#2a78d6", "#eb6834"
MUTED_FILL = "#c3c2b7"
INK, INK_2, INK_3 = "#0b0b0b", "#52514e", "#898781"
GRID, SURFACE = "#e1e0d9", "#fcfcfb"

plt.rcParams.update({
    "font.family": ["Inter", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.edgecolor": MUTED_FILL,
    "axes.labelcolor": INK_2,
    "axes.titlecolor": INK,
    "axes.titlesize": 12,
    "axes.titleweight": "semibold",
    "axes.titlelocation": "left",
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "xtick.color": INK_3,
    "ytick.color": INK_3,
    "xtick.labelcolor": INK_2,
    "ytick.labelcolor": INK_2,
    "ytick.left": False,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "legend.frameon": False,
    "legend.fontsize": 9,
    "legend.labelcolor": INK_2,
})


def subtitle(ax, text):
    ax.text(0, 1.02, text, transform=ax.transAxes, color=INK_2, fontsize=9.5, va="bottom")


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {name}")


def fig_promise_cliff():
    df = pd.read_csv(SQL_OUT / "02_reviews_by_promise_gap.csv")
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    colors = [ORANGE if late else BLUE for late in df["is_late"]]
    labels = [t.replace(" days ", " days\n").replace("On the day", "On the\nday") for t in df["arrival_vs_promise"]]
    bars = ax.bar(labels, df["avg_review"], width=0.55, color=colors, zorder=3)
    ax.set_ylim(0, 5)
    ax.set_ylabel("Average review (1 to 5 stars)")
    ax.set_title("Reviews fall off a cliff the day the promise breaks", pad=24)
    subtitle(ax, "Average review by when the order arrived versus the promised date, 95,824 reviewed orders")
    for i in [0, 3, 4, 6]:  # label the story points only
        b = bars[i]
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.08, f"{b.get_height():.2f}",
                ha="center", va="bottom", color=INK, fontsize=9.5, fontweight="semibold")
    ax.tick_params(axis="x", labelrotation=0, labelsize=9)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=BLUE), plt.Rectangle((0, 0), 1, 1, color=ORANGE)],
              labels=["On time or early", "Late"], loc="upper right")
    save(fig, "1_promise_cliff.png")


def fig_same_wait():
    df = pd.read_csv(SQL_OUT / "03_same_wait_different_promise.csv")
    df["label"] = df["actual_wait"].str.slice(3)
    x = range(len(df))
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    w = 0.34
    b1 = ax.bar([i - w / 2 - 0.01 for i in x], df["avg_review_on_time"], width=w, color=BLUE, zorder=3, label="Arrived by the promised date")
    b2 = ax.bar([i + w / 2 + 0.01 for i in x], df["avg_review_late"], width=w, color=ORANGE, zorder=3, label="Arrived after the promised date")
    ax.set_xticks(list(x), df["label"])
    ax.set_xlabel("Actual time from purchase to delivery")
    ax.set_ylim(0, 5)
    ax.set_ylabel("Average review")
    ax.set_title("Same wait, different promise: customers grade the promise", pad=24)
    subtitle(ax, "Orders that took 20 to 29 days scored 4.00 when on time and 2.63 when late")
    i = 3
    for b in (b1[i], b2[i]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.08, f"{b.get_height():.2f}",
                ha="center", va="bottom", color=INK, fontsize=9.5, fontweight="semibold")
    ax.legend(loc="upper right")
    save(fig, "2_same_wait_different_promise.png")


def fig_monthly(metrics):
    df = pd.read_csv(SQL_OUT / "04_monthly_trend.csv", parse_dates=["purchase_month"])
    top3 = set(metrics["waves"]["top3_months"])
    df["lbl"] = df["purchase_month"].dt.strftime("%b\n%y")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True, gridspec_kw={"hspace": 0.45})
    x = range(len(df))
    ax1.plot(x, df["avg_promised_days"], color=BLUE, lw=2, solid_capstyle="round", label="Promised days")
    ax1.plot(x, df["avg_actual_days"], color=ORANGE, lw=2, solid_capstyle="round", label="Actual days")
    ax1.set_ylim(0, 45)
    ax1.set_ylabel("Days from purchase")
    ax1.set_title("Olist promised about twice the real delivery time", pad=24)
    subtitle(ax1, "Average promised vs actual delivery days by purchase month")
    ax1.legend(loc="upper right", ncols=2)
    for s, col in [("avg_promised_days", BLUE), ("avg_actual_days", ORANGE)]:
        ax1.plot([len(df) - 1], [df[s].iloc[-1]], "o", color=col, ms=6, mec=SURFACE, mew=2)
        ax1.text(len(df) - 0.6, df[s].iloc[-1], f"{df[s].iloc[-1]:.0f}", va="center", color=INK, fontsize=9)
    colors = [ORANGE if d.strftime("%Y-%m") in top3 else MUTED_FILL for d in df["purchase_month"]]
    bars = ax2.bar(x, df["late_rate"] * 100, width=0.6, color=colors, zorder=3)
    ax2.set_ylabel("Late orders (%)")
    ax2.set_title("Yet lateness came in waves", pad=24)
    share = metrics["waves"]["top3_share_of_late"]
    subtitle(ax2, f"Share of orders delivered late. The 3 orange months hold {share:.0%} of all late orders")
    for b, d in zip(bars, df["purchase_month"]):
        if d.strftime("%Y-%m") in top3:
            ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.4, f"{b.get_height():.0f}%",
                     ha="center", va="bottom", fontsize=9, color=INK, fontweight="semibold")
    ax2.set_xticks(list(x), df["lbl"])
    ax2.tick_params(axis="x", labelsize=8)
    ax2.set_ylim(0, 22)
    save(fig, "3_monthly_promise_and_waves.png")


def fig_seller_habits(metrics):
    df = pd.read_csv(SQL_OUT / "08_seller_habits.csv")
    sh = metrics["seller_habits"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2), gridspec_kw={"wspace": 0.3})
    panels = [
        ("late_rate_2017", "late_rate_2018", "Late delivery rate", sh["late_rate_corr"], "Barely repeats"),
        ("missed_ship_by_2017", "missed_ship_by_2018", "Missed ship-by deadline rate", sh["missed_ship_by_corr"], "Repeats: a real habit"),
    ]
    for ax, (a, b, title, r, verdict) in zip(axes, panels):
        ax.grid(True, axis="both")
        ax.scatter(df[a] * 100, df[b] * 100, s=28, color=BLUE, edgecolor=SURFACE, linewidth=1.2, zorder=3, alpha=0.85)
        lim = max(df[a].max(), df[b].max()) * 100 * 1.05
        ax.plot([0, lim], [0, lim], color=MUTED_FILL, lw=1, zorder=2)
        ax.set_xlim(0, lim); ax.set_ylim(0, lim)
        ax.set_xlabel("Seller's 2017 rate (%)")
        ax.set_ylabel("Same seller's 2018 rate (%)")
        ax.set_title(title, pad=22, fontsize=11)
        subtitle(ax, f"{verdict}, correlation r = {r:.2f}")
    fig.suptitle(f"Score sellers on what they control: {sh['sellers']} sellers with 30+ orders in both years",
                 x=0.07, ha="left", y=1.04, fontsize=12, fontweight="semibold", color=INK)
    save(fig, "4_seller_habits.png")


def fig_tradeoff():
    df = pd.read_csv(MODEL_OUT / "formula_backtest.csv")
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    ax.grid(True, axis="both")
    for method, col in [("Olist promise + buffer", BLUE), ("Route percentile rule", ORANGE)]:
        g = df[df.method == method].sort_values("avg_promised_days")
        g = g[(g.avg_promised_days >= 20) & (g.avg_promised_days <= 34)]
        ax.plot(g["avg_promised_days"], g["late_rate"] * 100, color=col, lw=2, marker="o", ms=5,
                mec=SURFACE, mew=1.5, label=method, zorder=3)
    o = df[(df.method == "Olist promise + buffer") & (df.setting == "+0d")].iloc[0]
    ax.annotate("Olist today", (o.avg_promised_days, o.late_rate * 100), xytext=(o.avg_promised_days + 1.2, o.late_rate * 100 + 1.6),
                fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=INK_3, lw=0.8))
    ax.set_xlabel("Average promised delivery time (days)")
    ax.set_ylabel("Late orders (%)")
    ax.set_title("Each extra day of promise buys fewer late orders", pad=24)
    subtitle(ax, "2018 walk-forward backtest. A route-based formula did not beat Olist's own estimate")
    ax.legend(loc="upper right")
    save(fig, "5_promise_tradeoff.png")


def run_all():
    metrics = json.loads((ROOT / "outputs" / "metrics.json").read_text())
    fig_promise_cliff()
    fig_same_wait()
    fig_monthly(metrics)
    fig_seller_habits(metrics)
    fig_tradeoff()


if __name__ == "__main__":
    run_all()

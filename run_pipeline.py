"""Run the whole project from raw data to dashboard with one command:

    python run_pipeline.py
"""
import time

from src import build_dashboard, build_warehouse, charts, models, run_sql_analysis

STEPS = [
    ("1/5 Build the DuckDB warehouse (staging + marts)", build_warehouse.build),
    ("2/5 Run the SQL analysis queries", run_sql_analysis.run_all),
    ("3/5 Run the statistical models and backtests", models.run_all),
    ("4/5 Draw the README charts", charts.run_all),
    ("5/5 Export the dashboard data", build_dashboard.build),
]

if __name__ == "__main__":
    start = time.time()
    for name, step in STEPS:
        print(f"\n{name}")
        step()
    print(f"\nDone in {time.time() - start:.0f}s. Open docs/index.html to see the dashboard.")

"""Build the DuckDB warehouse from the raw CSVs.

Runs sql/01_staging.sql then sql/02_marts.sql and writes warehouse.duckdb.
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SQL = ROOT / "sql"
DB_PATH = ROOT / "warehouse.duckdb"


def build(db_path: Path = DB_PATH) -> None:
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    for name in ["01_staging.sql", "02_marts.sql"]:
        sql = (SQL / name).read_text().replace("{raw}", RAW.as_posix())
        con.execute(sql)
        print(f"ran {name}")
    for table in ["staging.orders", "staging.reviews", "mart.fct_orders", "mart.dim_customers", "mart.dim_sellers"]:
        n = con.execute(f"select count(*) from {table}").fetchone()[0]
        print(f"  {table:<22} {n:>8,} rows")
    con.close()


if __name__ == "__main__":
    build()

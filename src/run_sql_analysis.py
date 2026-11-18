"""Run every query in sql/analysis against the warehouse and save each result to outputs/sql/<name>.csv."""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "warehouse.duckdb"
QUERIES = ROOT / "sql" / "analysis"
OUT = ROOT / "outputs" / "sql"


def run_query(con: duckdb.DuckDBPyConnection, name: str):
    """Run one analysis query by file stem (for example '06_ship_by_handoff') and return a DataFrame."""
    return con.execute((QUERIES / f"{name}.sql").read_text()).df()


def run_all() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    for path in sorted(QUERIES.glob("*.sql")):
        df = run_query(con, path.stem)
        df.to_csv(OUT / f"{path.stem}.csv", index=False)
        print(f"  {path.stem:<34} {len(df):>7,} rows")
    con.close()


if __name__ == "__main__":
    run_all()

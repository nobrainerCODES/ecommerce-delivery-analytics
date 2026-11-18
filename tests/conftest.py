import json
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def con():
    db = ROOT / "warehouse.duckdb"
    if not db.exists():
        pytest.skip("warehouse.duckdb not found. Run `python run_pipeline.py` first.")
    c = duckdb.connect(str(db), read_only=True)
    yield c
    c.close()


@pytest.fixture(scope="session")
def metrics():
    path = ROOT / "outputs" / "metrics.json"
    if not path.exists():
        pytest.skip("outputs/metrics.json not found. Run `python run_pipeline.py` first.")
    return json.loads(path.read_text())

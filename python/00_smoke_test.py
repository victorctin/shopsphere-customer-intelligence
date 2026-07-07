"""Connectivity smoke test: run before anything else touches the DB."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text

from config.db import get_engine


def main() -> int:
    eng = get_engine()
    with eng.begin() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar()
        conn.execute(text("CREATE TABLE IF NOT EXISTS _smoke (id INT)"))
        conn.execute(text("INSERT INTO _smoke VALUES (1)"))
        n = conn.execute(text("SELECT COUNT(*) FROM _smoke")).scalar()
        conn.execute(text("DROP TABLE _smoke"))
    print(f"MySQL version: {version}, roundtrip rows: {n}")
    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Phase 2 orchestrator: raw CSVs -> cleaning rules -> silver CSVs + quality
report. Exits 1 unless the report grades PERFECT (every injected defect class
found exactly). --load-db additionally applies the silver DDL and loads
silver_* tables (requires local .env credentials)."""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings

from clean_rules import clean_all
from quality_report import grade, parse_manifest, write_report

TABLE_NAMES = ["customers", "products", "orders", "order_items",
               "web_sessions", "web_events", "marketing_spend",
               "ab_test_assignments", "reviews_nps"]


def main(load_db: bool) -> None:
    t0 = time.time()
    raw_dir = settings.PROJECT_ROOT / "data" / "raw"
    tables = {name: pd.read_csv(raw_dir / f"{name}.csv") for name in TABLE_NAMES}

    silver, audit = clean_all(tables)

    silver_dir = settings.PROJECT_ROOT / "data" / "silver"
    silver_dir.mkdir(parents=True, exist_ok=True)
    for name, df in silver.items():
        df.to_csv(silver_dir / f"{name}.csv", index=False)
        print(f"  {name:<22} {len(df):>9,} rows -> silver csv")

    manifest = parse_manifest(settings.PROJECT_ROOT / "docs" / "dirty_data_manifest.md")
    grade_df = grade(audit, manifest)
    report_path = settings.PROJECT_ROOT / "docs" / "data_quality_report.md"
    write_report(grade_df, report_path)

    passed = int((grade_df["verdict"] == "PASS").sum())
    print(f"Quality gate: {passed}/{len(grade_df)} defect classes matched "
          f"-> {report_path.name}")

    if load_db:
        from config.db import get_engine
        from utils.db_io import load_dataframe
        from utils.run_sql import run_sql_file

        engine = get_engine()
        ddl = settings.PROJECT_ROOT / "sql" / "20_silver" / "01_silver_tables.sql"
        n = run_sql_file(ddl, engine)
        print(f"Executed {n} DDL statements from {ddl.name}")
        for name, df in silver.items():
            rows = load_dataframe(df, f"silver_{name}", engine)
            print(f"  {name:<22} {rows:>9,} rows -> silver_{name}")

    print(f"Done in {time.time() - t0:,.0f}s")
    if passed != len(grade_df):
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load-db", action="store_true",
                        help="apply silver DDL and load silver_* tables")
    main(parser.parse_args().load_db)

"""Create (or recreate) all bronze tables."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings
from config.db import get_engine
from utils.run_sql import run_sql_file


def main() -> None:
    ddl = settings.PROJECT_ROOT / "sql" / "10_bronze" / "01_bronze_tables.sql"
    n = run_sql_file(ddl, get_engine())
    print(f"Executed {n} statements from {ddl.name}")


if __name__ == "__main__":
    main()

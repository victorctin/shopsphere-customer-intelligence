"""Execute a .sql file statement-by-statement (splits on ';', strips -- comments)."""
from pathlib import Path

from sqlalchemy import text


def run_sql_file(path, engine) -> int:
    raw = Path(path).read_text(encoding="utf-8")
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    return len(statements)

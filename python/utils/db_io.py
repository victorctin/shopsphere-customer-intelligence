"""Chunked DataFrame -> MySQL loading."""
import re

from sqlalchemy import text

# TRUNCATE takes an identifier, which cannot be bound as a query parameter,
# so restrict table names to plain identifiers before interpolating.
_TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_dataframe(df, table: str, engine, chunksize: int = 10_000, truncate: bool = True) -> int:
    if not _TABLE_NAME_RE.fullmatch(table):
        raise ValueError(f"invalid table name: {table!r}")
    if truncate:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table}"))
    df.to_sql(table, engine, if_exists="append", index=False,
              chunksize=chunksize, method="multi")
    return len(df)

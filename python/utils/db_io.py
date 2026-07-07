"""Chunked DataFrame -> MySQL loading."""
from sqlalchemy import text


def load_dataframe(df, table: str, engine, chunksize: int = 10_000, truncate: bool = True) -> int:
    if truncate:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table}"))
    df.to_sql(table, engine, if_exists="append", index=False,
              chunksize=chunksize, method="multi")
    return len(df)

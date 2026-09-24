"""Use inside notebook cells:  from lab_db import save_df, load_df, DATA_DIR
Tables go to the local Postgres (database `lab`), so data survives restarts."""
import io
from pathlib import Path

import pandas as pd
import psycopg

DSN = "postgresql://lab:lab@127.0.0.1:5432/lab"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "thesis_project" / "data"


def _sql_type(dtype) -> str:
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    if pd.api.types.is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    return "TEXT"


def save_df(df: pd.DataFrame, table: str) -> None:
    """Create/replace `table` with the DataFrame (fast COPY)."""
    cols = ", ".join(f'"{c}" {_sql_type(t)}' for c, t in df.dtypes.items())
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False)
    buf.seek(0)
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS "{table}"')
        cur.execute(f'CREATE TABLE "{table}" ({cols})')
        with cur.copy(f'COPY "{table}" FROM STDIN WITH (FORMAT csv)') as cp:
            cp.write(buf.read())
    print(f"Saved {len(df):,} rows x {df.shape[1]} cols -> Postgres table '{table}'")


def load_df(table: str) -> pd.DataFrame:
    with psycopg.connect(DSN) as conn:
        return pd.read_sql(f'SELECT * FROM "{table}"', conn)

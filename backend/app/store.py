"""Postgres (notebooks, runs) + MinIO (images, files). Everything local."""
import json
import os
import time
from pathlib import Path

import psycopg
from minio import Minio

PG_DSN = os.getenv("LAB_PG_DSN", "postgresql://lab:lab@127.0.0.1:5432/lab")
MINIO_ENDPOINT = os.getenv("LAB_MINIO", "127.0.0.1:9000")
BUCKET = "lab"

_minio = None


def pg():
    return psycopg.connect(PG_DSN, autocommit=True)


def minio():
    global _minio
    if _minio is None:
        _minio = Minio(MINIO_ENDPOINT, access_key="minioadmin", secret_key="minioadmin", secure=False)
        if not _minio.bucket_exists(BUCKET):
            _minio.make_bucket(BUCKET)
    return _minio


def init(retries=30):
    for i in range(retries):
        try:
            with pg() as c:
                c.execute("""CREATE TABLE IF NOT EXISTS notebooks (
                    id SERIAL PRIMARY KEY, name TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT now())""")
                c.execute("""CREATE TABLE IF NOT EXISTS runs (
                    id SERIAL PRIMARY KEY, notebook_id INT REFERENCES notebooks(id),
                    code TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
                    outputs JSONB NOT NULL DEFAULT '[]', files JSONB NOT NULL DEFAULT '[]',
                    created_at TIMESTAMPTZ DEFAULT now(), started_at TIMESTAMPTZ, finished_at TIMESTAMPTZ,
                    seconds REAL)""")
                c.execute("ALTER TABLE runs ADD COLUMN IF NOT EXISTS step TEXT")
                c.execute("ALTER TABLE runs ADD COLUMN IF NOT EXISTS batch_id TEXT")
            minio()
            return
        except Exception:  # noqa: BLE001
            if i == retries - 1:
                raise
            time.sleep(1)


def put_bytes(key: str, data: bytes, content_type: str):
    import io
    minio().put_object(BUCKET, key, io.BytesIO(data), len(data), content_type=content_type)


def put_file(key: str, path: str):
    minio().fput_object(BUCKET, key, path)


def dumps(o):
    return json.dumps(o, default=str)


DATA_CSV = Path(__file__).resolve().parent.parent.parent / "thesis_project" / "data" / "data.csv"
RAW_TABLE = "hairfall_dataset"


def load_dataset() -> str:
    """Load thesis_project/data/data.csv into Postgres table hairfall_dataset (skipped if the file is unchanged)."""
    import hashlib

    import pandas as pd

    if not DATA_CSV.exists():
        return f"missing {DATA_CSV}"
    digest = hashlib.sha256(DATA_CSV.read_bytes()).hexdigest()
    with pg() as c:
        c.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
        row = c.execute("SELECT value FROM meta WHERE key='dataset_sha256'").fetchone()
        exists = c.execute("SELECT to_regclass(%s)", (RAW_TABLE,)).fetchone()[0]
        if row and row[0] == digest and exists:
            return "unchanged"
        df = pd.read_csv(DATA_CSV)
        types = {"int64": "BIGINT", "float64": "DOUBLE PRECISION"}
        cols = ", ".join(f'"{k}" {types.get(str(v), "TEXT")}' for k, v in df.dtypes.items())
        c.execute(f'DROP TABLE IF EXISTS "{RAW_TABLE}"')
        c.execute(f'CREATE TABLE "{RAW_TABLE}" ({cols})')
        with c.cursor().copy(f'COPY "{RAW_TABLE}" FROM STDIN WITH (FORMAT csv, HEADER true)') as cp:
            cp.write(DATA_CSV.read_bytes())
        c.execute("INSERT INTO meta VALUES ('dataset_sha256', %s) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value",
                  (digest,))
    return f"loaded {len(df):,} rows"

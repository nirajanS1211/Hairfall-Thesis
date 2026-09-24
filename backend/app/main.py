"""Hairfall Lab - local Kaggle/Colab-style runner for the thesis steps.

Every run (code, output, figures, files, time) is stored in Postgres + MinIO, and successful runs
are also written to thesis_project/<Step>/. Runs execute one at a time in a single persistent kernel.

Run: ./start.sh   (UI + API on http://127.0.0.1:8000, localhost only)
"""
import logging
import queue
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import kernel as kmod
from . import project, store

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("lab")

FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend"
RUN_COLS = "id, step, code, status, outputs, files, created_at, started_at, finished_at, seconds, batch_id"

app = FastAPI(title="Hairfall Lab")
jobs: "queue.Queue[int]" = queue.Queue()
state = {"kernel": None, "running": None, "dataset": "not loaded"}
kernel_lock = threading.Lock()


class RunReq(BaseModel):
    code: Optional[str] = None  # None = the step's default code


def _row(r):
    return {"id": r[0], "step": r[1], "code": r[2], "status": r[3], "outputs": r[4], "files": r[5],
            "created_at": r[6], "started_at": r[7], "finished_at": r[8], "seconds": r[9], "batch_id": r[10]}


def _kernel() -> kmod.Kernel:
    with kernel_lock:
        if state["kernel"] is None:
            state["kernel"] = kmod.Kernel()
        return state["kernel"]


def _worker():
    while True:
        run_id = jobs.get()
        with store.pg() as c:
            r = c.execute("SELECT step, code, status, batch_id FROM runs WHERE id=%s", (run_id,)).fetchone()
            if not r or r[2] != "queued":  # cancelled or skipped meanwhile
                continue
            step, code, _, batch = r
            c.execute("UPDATE runs SET status='running', started_at=now() WHERE id=%s", (run_id,))
        state["running"] = run_id
        t0 = time.time()

        def push(outputs):
            with store.pg() as c:
                c.execute("UPDATE runs SET outputs=%s, seconds=%s WHERE id=%s",
                          (store.dumps(outputs), round(time.time() - t0, 1), run_id))

        try:
            status, outputs, files = kmod.execute(_kernel(), run_id, code, push)
        except kmod.KernelDied as exc:
            status, outputs, files = "error", [{"type": "error", "text": str(exc), "ename": "KernelDied"}], []
            with kernel_lock:
                state["kernel"].shutdown()
                state["kernel"] = None  # a fresh kernel starts on the next run
        except Exception as exc:  # noqa: BLE001
            log.exception("run %s failed", run_id)
            status, outputs, files = "error", [{"type": "error", "text": str(exc), "ename": "BackendError"}], []
        secs = round(time.time() - t0, 1)
        with store.pg() as c:
            c.execute("UPDATE runs SET status=%s, outputs=%s, files=%s, finished_at=now(), seconds=%s WHERE id=%s",
                      (status, store.dumps(outputs), store.dumps(files), secs, run_id))
            if status != "ok" and batch:  # stop the rest of a "run all"
                c.execute("UPDATE runs SET status='skipped' WHERE batch_id=%s AND status='queued'", (batch,))
        if status == "ok":
            try:
                project.export_run(step, run_id, code, outputs, files, secs)
            except Exception:  # noqa: BLE001  (disk export must never break a run)
                log.exception("export of run %s failed", run_id)
        state["running"] = None


@app.on_event("startup")
def startup():
    store.init()
    project.ensure_steps()
    with store.pg() as c:
        c.execute("UPDATE runs SET status='interrupted' WHERE status IN ('queued','running')")
    try:
        state["dataset"] = store.load_dataset()
    except Exception as exc:  # noqa: BLE001
        state["dataset"] = f"error: {exc}"
    log.info("dataset: %s", state["dataset"])
    threading.Thread(target=_worker, daemon=True).start()


def _enqueue(step: str, code: str, batch: Optional[str] = None) -> int:
    with store.pg() as c:
        rid = c.execute("INSERT INTO runs (step, code, batch_id) VALUES (%s,%s,%s) RETURNING id",
                        (step, code, batch)).fetchone()[0]
    jobs.put(rid)
    return rid


# ---------- API ----------

@app.get("/api/status")
def status():
    with store.pg() as c:
        queued = c.execute("SELECT COUNT(*) FROM runs WHERE status='queued'").fetchone()[0]
    return {"running": state["running"], "queued": queued, "dataset": state["dataset"],
            "kernel": state["kernel"] is not None}


@app.get("/api/steps")
def list_steps():
    with store.pg() as c:
        latest = {r[1]: _row(r) for r in c.execute(
            f"SELECT DISTINCT ON (step) {RUN_COLS} FROM runs WHERE step IS NOT NULL ORDER BY step, id DESC")}
        last_ok = {r[0]: r[1] for r in c.execute(
            "SELECT DISTINCT ON (step) step, code FROM runs WHERE status='ok' ORDER BY step, id DESC")}
    out = []
    for s in project.steps():
        run = latest.get(s["id"])
        out.append({**s, "code": run["code"] if run else s["default_code"], "last_run": run,
                    "saved": s["id"] in last_ok})
    return out


@app.post("/api/steps/{step}/run")
def run_step(step: str, body: RunReq):
    steps = {s["id"]: s for s in project.steps()}
    if step not in steps:
        raise HTTPException(404, "unknown step")
    return {"run_id": _enqueue(step, body.code or steps[step]["default_code"])}


@app.post("/api/run-all")
def run_all(from_step: Optional[str] = None, to_step: Optional[str] = None):
    """Queue steps in order (optionally a range); stops at the first failure."""
    steps = project.steps()
    ids = [s["id"] for s in steps]
    lo = ids.index(from_step) if from_step in ids else 0
    hi = ids.index(to_step) + 1 if to_step in ids else len(ids)
    latest = {s["id"]: s["code"] for s in list_steps()}
    batch = uuid.uuid4().hex
    return {"batch_id": batch, "run_ids": [_enqueue(i, latest[i], batch) for i in ids[lo:hi]]}


@app.post("/api/stop")
def stop():
    with store.pg() as c:
        c.execute("UPDATE runs SET status='cancelled' WHERE status='queued'")
    if state["kernel"] and state["running"]:
        state["kernel"].interrupt()
    return {"ok": True}


@app.post("/api/restart")
def restart():
    stop()
    with kernel_lock:
        if state["kernel"]:
            state["kernel"].shutdown()
        state["kernel"] = None
    return {"ok": True}


@app.get("/api/runs/{run_id}")
def get_run(run_id: int):
    with store.pg() as c:
        r = c.execute(f"SELECT {RUN_COLS} FROM runs WHERE id=%s", (run_id,)).fetchone()
    if not r:
        raise HTTPException(404, "run not found")
    return _row(r)


@app.get("/api/steps/{step}/history")
def history(step: str):
    with store.pg() as c:
        rows = c.execute(f"SELECT {RUN_COLS} FROM runs WHERE step=%s ORDER BY id DESC LIMIT 50", (step,)).fetchall()
    return [_row(r) for r in rows]


@app.get("/api/dataset")
def dataset(offset: int = 0, limit: int = 50, sort: Optional[str] = None, desc: bool = False,
            q: Optional[str] = None):
    limit = max(1, min(limit, 500))
    with store.pg() as c:
        cols = [r[0] for r in c.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position",
            (store.RAW_TABLE,))]
        if not cols:
            raise HTTPException(503, "dataset not loaded")
        where, params = "", []
        if q:
            where = "WHERE " + " OR ".join(f'CAST("{col}" AS TEXT) ILIKE %s' for col in cols)
            params = [f"%{q}%"] * len(cols)
        order = f'ORDER BY "{sort}" {"DESC" if desc else "ASC"}' if sort in cols else 'ORDER BY "id"'
        total = c.execute(f'SELECT COUNT(*) FROM "{store.RAW_TABLE}" {where}', params).fetchone()[0]
        rows = c.execute(f'SELECT * FROM "{store.RAW_TABLE}" {where} {order} LIMIT %s OFFSET %s',
                         params + [limit, offset]).fetchall()
    return {"columns": cols, "rows": rows, "total": total, "source": str(store.DATA_CSV.name)}


@app.get("/api/dataset/stats")
def dataset_stats():
    import pandas as pd
    with store.pg() as c:
        df = pd.read_sql(f'SELECT * FROM "{store.RAW_TABLE}"', c)
    num = df.drop(columns=["id"]).select_dtypes("number")
    stats = num.describe().T.round(3).reset_index().rename(columns={"index": "column"})
    return {"rows": len(df), "columns": df.shape[1], "missing": int(df.isna().sum().sum()),
            "target": df["hair_fall"].value_counts().sort_index().to_dict(),
            "gender": df["gender"].value_counts().to_dict(), "describe": stats.to_dict("records")}


@app.get("/api/files/{key:path}")
def get_file(key: str, download: bool = False):
    try:
        obj = store.minio().get_object(store.BUCKET, key)
        data, ctype = obj.read(), obj.headers.get("Content-Type", "application/octet-stream")
    except Exception:  # noqa: BLE001
        raise HTTPException(404, "file not found")
    headers = {"Content-Disposition": f'attachment; filename="{key.split("/")[-1]}"'} if download else {}
    return Response(data, media_type=ctype, headers=headers)


# ---------- UI ----------

@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

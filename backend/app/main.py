"""Local notebook-runner backend. Paste code -> run in a kernel -> saved forever in Postgres + MinIO.

Run: uvicorn app.main:app --port 8000   (binds to localhost only)
"""
import queue
import threading
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from . import kernel as kmod
from . import project, store

app = FastAPI(title="Hairfall Lab")
kernels: dict[int, kmod.Kernel] = {}
jobs: "queue.Queue[tuple[int, int]]" = queue.Queue()  # one job at a time: protects 16 GB RAM


class NewNotebook(BaseModel):
    name: str = "Untitled"


class RunReq(BaseModel):
    code: str
    step: Optional[str] = None  # e.g. "Step_05_CatBoost"; saves code/output/files to thesis_project/<step>/


def _get_kernel(nb_id: int) -> kmod.Kernel:
    if nb_id not in kernels:
        kernels[nb_id] = kmod.Kernel()
    return kernels[nb_id]


def worker():
    while True:
        nb_id, run_id = jobs.get()
        with store.pg() as c:
            code = c.execute("SELECT code FROM runs WHERE id=%s", (run_id,)).fetchone()[0]
            c.execute("UPDATE runs SET status='running', started_at=now() WHERE id=%s", (run_id,))
        t0 = time.time()

        def push(outputs):
            with store.pg() as c:
                c.execute("UPDATE runs SET outputs=%s WHERE id=%s", (store.dumps(outputs), run_id))

        try:
            status, outputs, files = kmod.execute(_get_kernel(nb_id), run_id, code, push)
        except Exception as exc:  # noqa: BLE001
            status, outputs, files = "error", [{"type": "error", "text": str(exc), "ename": "BackendError"}], []
        secs = round(time.time() - t0, 1)
        with store.pg() as c:
            c.execute(
                "UPDATE runs SET status=%s, outputs=%s, files=%s, finished_at=now(), seconds=%s WHERE id=%s",
                (status, store.dumps(outputs), store.dumps(files), secs, run_id),
            )
            step = c.execute("SELECT step FROM runs WHERE id=%s", (run_id,)).fetchone()[0]
        if step:
            try:
                project.export_run(step, run_id, code, outputs, files, secs, status)
            except Exception:  # noqa: BLE001  (disk export must never break a run)
                pass


@app.on_event("startup")
def startup():
    store.init()
    project.ensure_steps()
    with store.pg() as c:  # runs interrupted by a shutdown
        c.execute("UPDATE runs SET status='interrupted' WHERE status IN ('queued','running')")
    threading.Thread(target=worker, daemon=True).start()


@app.get("/steps")
def steps():
    return project.STEPS


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/notebooks")
def create_notebook(body: NewNotebook):
    with store.pg() as c:
        r = c.execute("INSERT INTO notebooks (name) VALUES (%s) RETURNING id, name, created_at", (body.name,)).fetchone()
    return {"id": r[0], "name": r[1], "created_at": r[2]}


@app.get("/notebooks")
def list_notebooks():
    with store.pg() as c:
        rows = c.execute("""SELECT n.id, n.name, n.created_at, COUNT(r.id), COALESCE(SUM(r.seconds),0)
                            FROM notebooks n LEFT JOIN runs r ON r.notebook_id=n.id
                            GROUP BY n.id ORDER BY n.id DESC""").fetchall()
    return [{"id": r[0], "name": r[1], "created_at": r[2], "runs": r[3], "total_seconds": r[4]} for r in rows]


@app.post("/notebooks/{nb_id}/run")
def run(nb_id: int, body: RunReq):
    with store.pg() as c:
        if not c.execute("SELECT 1 FROM notebooks WHERE id=%s", (nb_id,)).fetchone():
            raise HTTPException(404, "notebook not found")
        run_id = c.execute("INSERT INTO runs (notebook_id, code, step) VALUES (%s,%s,%s) RETURNING id", (nb_id, body.code, body.step)).fetchone()[0]
    jobs.put((nb_id, run_id))
    return {"run_id": run_id, "status": "queued"}


def _run_row(r):
    return {"id": r[0], "notebook_id": r[1], "code": r[2], "status": r[3], "outputs": r[4], "files": r[5],
            "created_at": r[6], "started_at": r[7], "finished_at": r[8], "seconds": r[9], "step": r[10]}


RUN_COLS = "id, notebook_id, code, status, outputs, files, created_at, started_at, finished_at, seconds, step"


@app.get("/notebooks/{nb_id}/runs")
def list_runs(nb_id: int):
    with store.pg() as c:
        rows = c.execute(f"SELECT {RUN_COLS} FROM runs WHERE notebook_id=%s ORDER BY id", (nb_id,)).fetchall()
    return [_run_row(r) for r in rows]


@app.get("/runs/{run_id}")
def get_run(run_id: int):
    with store.pg() as c:
        r = c.execute(f"SELECT {RUN_COLS} FROM runs WHERE id=%s", (run_id,)).fetchone()
    if not r:
        raise HTTPException(404, "run not found")
    return _run_row(r)


@app.post("/notebooks/{nb_id}/interrupt")
def interrupt(nb_id: int):
    if nb_id in kernels:
        kernels[nb_id].interrupt()
    return {"ok": True}


@app.post("/notebooks/{nb_id}/restart")
def restart(nb_id: int):
    k = kernels.pop(nb_id, None)
    if k:
        k.shutdown()
    return {"ok": True}


@app.get("/files/{key:path}")
def get_file(key: str, download: Optional[bool] = False):
    try:
        obj = store.minio().get_object(store.BUCKET, key)
        data, ctype = obj.read(), obj.headers.get("Content-Type", "application/octet-stream")
    except Exception:  # noqa: BLE001
        raise HTTPException(404, "file not found")
    headers = {"Content-Disposition": f'attachment; filename="{key.split("/")[-1]}"'} if download else {}
    return Response(data, media_type=ctype, headers=headers)

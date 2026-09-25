"""Import a step run made outside the lab (e.g. on Kaggle) so it appears in the UI, Postgres, MinIO and thesis_project/.

Usage (from backend/, with the lab's venv):
    .venv/bin/python import_kaggle_run.py ~/Downloads/Step_07c_TabFM_Full.zip
The zip/folder holds output.txt, metrics.json, predictions.csv, confusion_matrix.png (code.py optional).
Stop any local run of the same step first (its result would overwrite this one).
"""
import json
import pprint
import shutil
import sys
import tempfile
from pathlib import Path

from app import project, store

src = Path(sys.argv[1]).expanduser()
if src.suffix == ".zip":
    tmp = Path(tempfile.mkdtemp())
    shutil.unpack_archive(src, tmp)
    src = tmp
step = sys.argv[2] if len(sys.argv) > 2 else "Step_07c_TabFM_Full"
assert step in project.step_ids(), f"unknown step {step}"

metrics = json.loads((src / "metrics.json").read_text())
seconds = round(metrics["fit_seconds"] + metrics["predict_seconds"], 1)
code = (src / "code.py").read_text() if (src / "code.py").exists() else \
    (project.STEPS_DIR / f"{step}.py").read_text()

store.init()
with store.pg() as c:
    rid = c.execute("INSERT INTO runs (step, code, status, started_at, finished_at, seconds) "
                    "VALUES (%s,%s,'ok', now(), now(), %s) RETURNING id", (step, code, seconds)).fetchone()[0]

outputs = [{"type": "stream", "name": "stdout", "text": (src / "output.txt").read_text()}]
img = src / "confusion_matrix.png"
if img.exists():
    key = f"runs/{rid}/image_1.png"
    store.put_file(key, str(img))
    outputs.append({"type": "image", "key": key})
outputs.append({"type": "result", "text": pprint.pformat(metrics, sort_dicts=False), "html": None})

files = []
for name in ("confusion_matrix.png", "metrics.json", "predictions.csv"):
    p = src / name
    if p.exists():
        key = f"runs/{rid}/files/{name}"
        store.put_file(key, str(p))
        files.append({"key": key, "name": name, "type": {"png": "image/png", "json": "application/json",
                                                         "csv": "text/csv"}[name.rsplit(".", 1)[1]]})

with store.pg() as c:
    c.execute("UPDATE runs SET outputs=%s, files=%s WHERE id=%s", (store.dumps(outputs), store.dumps(files), rid))
project.export_run(step, rid, code, outputs, files, seconds)
print(f"Imported {step} as run #{rid} -> thesis_project/{step}/  ({metrics['accuracy']=}, {metrics['macro_f1']=})")

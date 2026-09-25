"""Rebuild the lab's run history (Postgres + MinIO) from the exported thesis_project/<Step>/ folders.

Use after backend/data/ was lost (it is git-ignored). Read-only on thesis_project/: nothing there is rewritten.
Steps that already have a run in the DB are skipped.
    .venv/bin/python restore_history.py
"""
import json
import mimetypes
import pprint
import re

from app import project, store

store.init()
with store.pg() as c:
    have = {r[0] for r in c.execute("SELECT DISTINCT step FROM runs").fetchall()}

for step in project.step_ids():
    d = project.ROOT / step
    if step in have or not (d / "output.txt").exists() or not (d / "code.py").exists():
        continue
    text = (d / "output.txt").read_text()
    m = re.search(r"time: ([\d.]+)s", text)
    seconds = float(m.group(1)) if m else 0.0
    with store.pg() as c:
        rid = c.execute("INSERT INTO runs (step, code, status, started_at, finished_at, seconds) "
                        "VALUES (%s,%s,'ok', now(), now(), %s) RETURNING id", (step, (d / "code.py").read_text(), seconds)).fetchone()[0]
    outputs = [{"type": "stream", "name": "stdout", "text": text}]
    files, n = [], 0
    for p in sorted(d.iterdir()):
        if not p.is_file() or p.name in ("code.py", "output.txt", "run_id.txt"):
            continue
        key = f"runs/{rid}/files/{p.name}"
        store.put_file(key, str(p))
        files.append({"key": key, "name": p.name, "type": mimetypes.guess_type(p.name)[0] or "application/octet-stream"})
        if p.suffix == ".png":
            n += 1
            store.put_file(f"runs/{rid}/image_{n}.png", str(p))
            outputs.append({"type": "image", "key": f"runs/{rid}/image_{n}.png"})
    if (d / "metrics.json").exists():
        outputs.append({"type": "result", "text": pprint.pformat(json.loads((d / "metrics.json").read_text()), sort_dicts=False), "html": None})
    with store.pg() as c:
        c.execute("UPDATE runs SET outputs=%s, files=%s WHERE id=%s", (store.dumps(outputs), store.dumps(files), rid))
    print(f"restored {step} -> run #{rid}")

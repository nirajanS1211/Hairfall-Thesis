"""Import step runs made outside the lab (e.g. on Kaggle) so they appear in the UI, Postgres, MinIO and thesis_project/.

Usage (from backend/, with the lab's venv):
    .venv/bin/python import_kaggle_run.py ~/Downloads/Step_07c_TabFM_Full.zip [Step_07c_TabFM_Full]
    .venv/bin/python import_kaggle_run.py ~/Downloads/Step_08_SHAP_kaggle.zip     # one sub-folder per step
A step folder holds output.txt plus its result files (metrics.json / shap_summary.json, csv, png ...); code.py optional.
Stop any local run of the same step first (its result would overwrite this one).
"""
import json
import mimetypes
import pprint
import re
import shutil
import sys
import tempfile
from pathlib import Path

from app import project, store

KAGGLE_DIR = Path(__file__).parent / "kaggle"


def import_step(step: str, src: Path):
    assert step in project.step_ids(), f"unknown step {step}"
    summary_file = next((src / n for n in ("metrics.json", "shap_summary.json") if (src / n).exists()), None)
    summary = json.loads(summary_file.read_text()) if summary_file else {}
    text = (src / "output.txt").read_text()
    took = re.search(r"\n?\[finished OK \| time: ([\d.]+)s\]\n?", text)  # wall time written by the Kaggle file
    if took:
        seconds, text = float(took.group(1)), text.replace(took.group(0), "")
    else:
        seconds = round(summary["fit_seconds"] + summary["predict_seconds"], 1) if "fit_seconds" in summary \
            else round(summary.get("seconds", 0), 1)
    kaggle_code = KAGGLE_DIR / f"{step}_kaggle.py"
    code = (src / "code.py").read_text() if (src / "code.py").exists() else \
        (kaggle_code if kaggle_code.exists() else project.STEPS_DIR / f"{step}.py").read_text()

    with store.pg() as c:
        rid = c.execute("INSERT INTO runs (step, code, status, started_at, finished_at, seconds) "
                        "VALUES (%s,%s,'ok', now(), now(), %s) RETURNING id", (step, code, seconds)).fetchone()[0]

    outputs = [{"type": "stream", "name": "stdout", "text": text}]
    files, n = [], 0
    for p in sorted(src.iterdir()):
        if p.name in ("code.py", "output.txt") or not p.is_file():
            continue
        key = f"runs/{rid}/files/{p.name}"
        store.put_file(key, str(p))
        files.append({"key": key, "name": p.name, "type": mimetypes.guess_type(p.name)[0] or "application/octet-stream"})
        if p.suffix == ".png":
            n += 1
            store.put_file(f"runs/{rid}/image_{n}.png", str(p))
            outputs.append({"type": "image", "key": f"runs/{rid}/image_{n}.png"})
    outputs.append({"type": "result", "text": pprint.pformat(summary, sort_dicts=False), "html": None})

    with store.pg() as c:
        c.execute("UPDATE runs SET outputs=%s, files=%s WHERE id=%s", (store.dumps(outputs), store.dumps(files), rid))
    project.export_run(step, rid, code, outputs, files, seconds)
    print(f"Imported {step} as run #{rid} -> thesis_project/{step}/")


store.init()
src = Path(sys.argv[1]).expanduser()
if src.suffix == ".zip":
    tmp = Path(tempfile.mkdtemp())
    shutil.unpack_archive(src, tmp)
    src = tmp
if len(sys.argv) > 2:
    import_step(sys.argv[2], src)
elif (src / "output.txt").exists():
    import_step("Step_07c_TabFM_Full", src)
else:
    for d in sorted(src.glob("Step_*")):
        if d.is_dir():
            import_step(d.name, d)

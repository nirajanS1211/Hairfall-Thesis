"""Import step runs made on Kaggle so they appear in the UI, Postgres, MinIO and thesis_project/.

Usage (from backend/, with the lab's venv):
    .venv/bin/python import_kaggle_run.py ~/Downloads/Step_07c_TabFM_Full.zip
    .venv/bin/python import_kaggle_run.py ~/Downloads/some_folder/        # one sub-folder per step
A step folder holds output.txt plus its result files (metrics.json / shap_summary.json, csv, png ...).
The run is stored with the step's local code (backend/steps/), so it can be re-run here; the Kaggle
version of the code stays in backend/kaggle/.
"""
import mimetypes
import re
import shutil
import sys
import tempfile
from pathlib import Path

from app import project, store


def import_step(step: str, src: Path):
    if step not in project.step_ids():
        raise SystemExit(f"unknown step {step}")
    text = (src / "output.txt").read_text()
    took = re.search(r"\n?\[finished OK \| time: ([\d.]+)s\]\n?", text)  # wall time written by the Kaggle file
    seconds = float(took.group(1)) if took else None
    if took:
        text = text.replace(took.group(0), "")
    code = (project.STEPS_DIR / f"{step}.py").read_text()

    with store.pg() as c:
        rid = c.execute("INSERT INTO runs (step, code, status, started_at, finished_at, seconds, source) "
                        "VALUES (%s,%s,'ok', now(), now(), %s, 'kaggle') RETURNING id", (step, code, seconds)).fetchone()[0]

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

    with store.pg() as c:
        c.execute("UPDATE runs SET outputs=%s, files=%s WHERE id=%s", (store.dumps(outputs), store.dumps(files), rid))
    project.export_run(step, rid, code, outputs, files, seconds or 0)
    print(f"Imported {step} as run #{rid} -> thesis_project/{step}/")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    store.init()
    src = Path(sys.argv[1]).expanduser()
    if src.suffix == ".zip":
        tmp = Path(tempfile.mkdtemp())
        shutil.unpack_archive(src, tmp)
        src = tmp
    if (src / "output.txt").exists():
        import_step(src.name, src)
    else:
        dirs = [d for d in sorted(src.glob("Step_*")) if d.is_dir() and (d / "output.txt").exists()]
        if not dirs:
            raise SystemExit(f"no step folders with output.txt in {src}")
        for d in dirs:
            import_step(d.name, d)


if __name__ == "__main__":
    main()

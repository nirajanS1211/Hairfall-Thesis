"""Thesis steps (code in backend/steps/) and the on-disk project folder thesis_project/<Step>/.

After a step finishes successfully its code, output, images and files are written to
thesis_project/<Step>/. The previous successful run of that step is moved to <Step>/history/run_<id>/.
"""
import re
import shutil
from pathlib import Path

from . import store

BACKEND = Path(__file__).resolve().parent.parent
STEPS_DIR = BACKEND / "steps"
ROOT = BACKEND.parent / "thesis_project"

GROUPS = [("01", "Setup & data"), ("02", "Setup & data"), ("03", "Setup & data"), ("04", "Setup & data"),
          ("05", "CatBoost"), ("06", "TabPFN"), ("07", "TabFM"), ("08", "SHAP explainability"),
          ("09", "Evaluation"), ("10", "Evaluation")]


def steps() -> list[dict]:
    out = []
    for f in sorted(STEPS_DIR.glob("Step_*.py")):
        code = f.read_text()
        first = code.splitlines()[0].lstrip("# ").strip()
        m = re.match(r"Step (\w+) - (.*)", first)
        num = f.stem.split("_")[1][:2]
        out.append({"id": f.stem, "label": m.group(1) if m else f.stem, "title": m.group(2) if m else first,
                    "group": dict(GROUPS).get(num, "Other"), "default_code": code})
    return out


def step_ids() -> list[str]:
    return [s["id"] for s in steps()]


def ensure_steps():
    for s in step_ids():
        (ROOT / s).mkdir(parents=True, exist_ok=True)


def export_run(step: str, run_id: int, code: str, outputs: list, files: list, seconds: float):
    step_dir = ROOT / step
    step_dir.mkdir(parents=True, exist_ok=True)
    prev = [p for p in step_dir.iterdir() if p.name != "history"]
    if prev:
        tag = (step_dir / "run_id.txt").read_text().strip() if (step_dir / "run_id.txt").exists() else "old"
        dest = step_dir / "history" / f"run_{tag}"
        shutil.rmtree(dest, ignore_errors=True)
        dest.mkdir(parents=True)
        for p in prev:
            shutil.move(str(p), dest / p.name)

    (step_dir / "code.py").write_text(code)
    (step_dir / "run_id.txt").write_text(str(run_id))
    text, n = [], 0
    has_png = any(f["name"].endswith(".png") for f in files)  # step saved its own figures
    for o in outputs:
        if o["type"] in ("stream", "result", "error"):
            text.append(o["text"] if o["text"].endswith("\n") else o["text"] + "\n")
        elif o["type"] == "image":
            n += 1
            if not has_png:
                (step_dir / f"figure_{n}.png").write_bytes(store.minio().get_object(store.BUCKET, o["key"]).read())
    text.append(f"\n[finished OK | time: {seconds}s | run #{run_id}]\n")
    (step_dir / "output.txt").write_text("".join(text))
    for f in files:
        target = step_dir / f["name"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(store.minio().get_object(store.BUCKET, f["key"]).read())

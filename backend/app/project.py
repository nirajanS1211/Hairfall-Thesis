"""Thesis project on disk: backend/thesis_project/<Step>/ holds the latest code, output and files
(same layout as the old 'Colab Work' folder). Older runs of a step go to <Step>/history/run_<id>/."""
import shutil
from pathlib import Path

from . import store

ROOT = Path(__file__).resolve().parent.parent.parent / "thesis_project"

STEPS = [
    "Step_01_Install", "Step_02_LoadData", "Step_03_CleanEncode", "Step_04_TrainTestSplit",
    "Step_05_CatBoost", "Step_06_TabPFN", "Step_07_TabFM",
    "Step_08a_CatBoost_SHAP", "Step_08b_TabPFN_SHAP", "Step_08c_TabFM_SHAP",
    "Step_08d_MatchedContextComparison", "Step_09_McNemarsTests", "Step_10_FinalResults",
    "Step_11_ScalingResults",
]


def ensure_steps():
    for s in STEPS:
        (ROOT / s).mkdir(parents=True, exist_ok=True)


def export_run(step: str, run_id: int, code: str, outputs: list, files: list, seconds: float, status: str):
    step_dir = ROOT / step
    step_dir.mkdir(parents=True, exist_ok=True)
    # archive the previous latest into history/
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
    text = []
    n = 0
    for o in outputs:
        if o["type"] in ("stream", "result"):
            text.append(o["text"])
        elif o["type"] == "error":
            text.append(o["text"])
        elif o["type"] == "image":
            n += 1
            data = store.minio().get_object(store.BUCKET, o["key"]).read()
            (step_dir / f"image_{n}.png").write_bytes(data)
    text.append(f"\n[status: {status} | train time: {seconds}s | run #{run_id}]\n")
    (step_dir / "output.txt").write_text("".join(text))
    for f in files:
        data = store.minio().get_object(store.BUCKET, f["key"]).read()
        (step_dir / f["name"]).parent.mkdir(parents=True, exist_ok=True)
        (step_dir / f["name"]).write_bytes(data)

"""Single-patient prediction with the thesis models, saved as history in Postgres + MinIO.

- CatBoost: the trained Full model saved by Step 5c (thesis_project/Step_05c_CatBoost_Full/catboost.cbm),
  plus per-feature SHAP contributions for this patient (exact TreeSHAP, instant).
- TabPFN / TabFM: pretrained foundation models; the Step 4 training rows are given as context
  (same stratified sample and seed as Steps 6/7). Fitted once per context size, then kept in memory.

Input limits are the min/max of the training data, so a patient can never be outside what the models saw.
"""
import logging
import os
import sys
import threading
import time

import numpy as np
import pandas as pd

from . import kernel as kmod
from . import project, store

log = logging.getLogger("lab.predict")
SEED = 42
CLASSES = ["Low", "Moderate", "High"]
SPLIT = project.ROOT / "Step_04_TrainTestSplit"
CATBOOST_MODEL = project.ROOT / "Step_05c_CatBoost_Full" / "catboost.cbm"

# (name, label, unit, group, kind, clinical normal range or None, help)
FIELDS = [
    ("age", "Age", "years", "About you", "int", None, ""),
    ("gender", "Gender", "", "About you", "choice", None, ""),
    ("total_protein", "Total protein", "g/dL", "Blood test results", "float", (6.0, 8.3), "Serum total protein"),
    ("calcium", "Calcium", "mg/dL", "Blood test results", "float", (8.5, 10.5), "Serum calcium"),
    ("iron", "Iron", "µg/dL", "Blood test results", "int", (60, 170), "Serum iron"),
    ("vitamin_d", "Vitamin D", "ng/mL", "Blood test results", "float", (25, 80), "25-OH vitamin D"),
    ("alt_liver", "ALT (liver)", "U/L", "Blood test results", "int", (7, 56), "Alanine aminotransferase"),
    ("manganese", "Manganese", "µg/L", "Blood test results", "float", (4, 15), "Whole-blood manganese"),
    ("body_water_content", "Body water", "%", "Blood test results", "float", (45, 65), "Total body water"),
    ("stress_level", "Stress level", "0–40", "Other scores", "int", None, "How stressed you are, 0 = none, 40 = extreme"),
    ("total_keratine", "Keratin", "0–100", "Other scores", "int", None, "Total keratin score"),
    ("hair_texture", "Hair texture", "0–100", "Other scores", "int", None, "Hair texture score"),
    ("family_hair_fall_history", "Family history of hair fall", "", "Health & lifestyle", "bool", None, ""),
    ("chronic_illness", "Chronic illness", "", "Health & lifestyle", "bool", None, ""),
    ("late_night_sleep", "Sleep late at night", "", "Health & lifestyle", "bool", None, ""),
    ("sleep_disturbance", "Disturbed sleep", "", "Health & lifestyle", "bool", None, ""),
    ("water_reason", "Poor water quality", "", "Health & lifestyle", "bool", None, ""),
    ("chemical_use", "Use chemical hair products", "", "Health & lifestyle", "bool", None, ""),
    ("anemia", "Anemia", "", "Health & lifestyle", "bool", None, ""),
    ("stress", "Often feel stressed", "", "Health & lifestyle", "bool", None, ""),
]
GENDERS = {0: "Female", 1: "Male", 2: "Other"}
MODELS = {"catboost": ["Full"], "tabpfn": ["500", "2000", "Full"], "tabfm": ["500", "2000"]}
SIZES = {"500": 500, "2000": 2000, "Full": None}

_train = None
_cache: dict = {}
_lock = threading.Lock()      # one prediction at a time (models share the GPU / memory)
_load_lock = threading.Lock()


def _env():
    for k, v in kmod._dotenv().items():  # TABPFN_TOKEN / HF_TOKEN from backend/.env
        os.environ.setdefault(k, v)


def train():
    global _train
    if _train is None:
        tr = pd.read_csv(SPLIT / "train.csv")
        _train = (tr.drop(columns="hair_fall"), tr["hair_fall"])
    return _train


def schema():
    X, y = train()
    fields = []
    for name, label, unit, group, kind, normal, help_ in FIELDS:
        s = X[name]
        f = {"name": name, "label": label, "unit": unit, "group": group, "kind": kind, "help": help_,
             "min": float(s.min()), "max": float(s.max()), "normal": list(normal) if normal else None,
             "default": float(s.median()) if kind in ("int", "float") else int(s.mode()[0])}
        if kind == "float":
            dec = max(len(f"{v:.6g}".split(".")[1]) if "." in f"{v:.6g}" else 0 for v in s.unique()[:2000])
            f["step"] = 10 ** -min(dec, 2)
        elif kind == "int":
            f["step"] = 1
        if kind == "choice":
            f["options"] = [{"value": k, "label": v} for k, v in GENDERS.items()]
        fields.append(f)
    return {"fields": fields, "classes": CLASSES, "models": MODELS, "context_rows": len(X),
            "catboost_ready": CATBOOST_MODEL.exists()}


def validate(inputs: dict) -> dict:
    X, _ = train()
    clean, errors = {}, {}
    for name, _label, _, _, kind, _, _ in FIELDS:
        v = inputs.get(name)
        if v is None or v == "":
            errors[name] = "required"
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            errors[name] = "not a number"
            continue
        lo, hi = float(X[name].min()), float(X[name].max())
        if kind in ("int", "choice", "bool") and v != int(v):
            errors[name] = "must be a whole number"
        elif not lo <= v <= hi:
            errors[name] = f"must be between {lo:g} and {hi:g}"
        else:
            clean[name] = int(v) if kind in ("int", "choice", "bool") else v
    if errors:
        raise ValueError(errors)
    return clean


# ---------- models ----------

def _context(size):
    from sklearn.model_selection import train_test_split
    X, y = train()
    n = SIZES[size]
    if n is None or n >= len(X):
        return X, y
    Xc, _, yc, _ = train_test_split(X, y, train_size=n, stratify=y, random_state=SEED)
    return Xc, yc


def _device():
    import torch
    return "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"


def _model(kind, size):
    key = (kind, size)
    with _load_lock:
        if key in _cache:
            return _cache[key]
        _env()
        if kind == "catboost":
            from catboost import CatBoostClassifier
            m = CatBoostClassifier()
            m.load_model(str(CATBOOST_MODEL))
        elif kind == "tabpfn":
            from tabpfn import TabPFNClassifier
            m = TabPFNClassifier(device=_device(), random_state=SEED, ignore_pretraining_limits=True)
            m.fit(*_context(size))
        elif kind == "tabfm":
            sys.modules.setdefault("flax", None)  # tabfm's optional JAX backend is not used
            from tabfm import TabFMClassifier
            from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1
            # default bf16 weights, as on Kaggle (float32 doubles the memory and does not fit next to TabPFN on a Mac)
            m = TabFMClassifier(model=tabfm_v1.load(device=_device()), n_estimators=1)
            m.fit(*_context(size))
        else:
            raise ValueError(kind)
        _cache[key] = m
        return m


def _free_gpu(keep=None):
    """Drop cached TabPFN/TabFM models (except `keep`) and release GPU memory."""
    import gc

    import torch
    for k in [k for k in _cache if k[0] != "catboost" and k != keep]:
        del _cache[k]
    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    elif torch.cuda.is_available():
        torch.cuda.empty_cache()


def _is_oom(exc):
    return "out of memory" in str(exc).lower()


def _predict_one(kind, size, row: pd.DataFrame):
    """Predict; if the GPU is full, unload the other foundation models and try again."""
    try:
        return _predict_raw(kind, size, row)
    except Exception as exc:  # noqa: BLE001
        if not _is_oom(exc):
            raise
        log.warning("%s %s: GPU out of memory - unloading other models and retrying", kind, size)
        _free_gpu(keep=None)
        return _predict_raw(kind, size, row)


def _predict_raw(kind, size, row: pd.DataFrame):
    m = _model(kind, size)
    t = time.time()
    if kind == "tabfm":  # TabFM needs at least 2 rows
        p = m.predict_proba(pd.concat([row, row]))[:1]
    else:
        p = m.predict_proba(row)
    out = {"proba": [round(float(x), 4) for x in np.asarray(p)[0]], "predict_seconds": round(time.time() - t, 2)}
    out["pred"] = int(np.argmax(out["proba"]))
    if kind == "catboost":
        from catboost import Pool
        sv = m.get_feature_importance(Pool(row), type="ShapValues")[0]  # [class, feature + bias]
        c = out["pred"]
        contrib = sorted(({"feature": f, "value": round(float(sv[c][i]), 4)} for i, f in enumerate(row.columns)),
                         key=lambda d: -abs(d["value"]))
        # risk direction per feature: SHAP(High) - SHAP(Low) in log-odds; > 0 raises the hair-fall risk
        risk = sorted(({"feature": f, "value": round(float(sv[2][i] - sv[0][i]), 4)} for i, f in enumerate(row.columns)),
                      key=lambda d: -abs(d["value"]))
        out["shap"] = {"class": c, "base": round(float(sv[c][-1]), 4), "top": contrib[:8], "risk": risk,
                       "all": {CLASSES[k]: [round(float(x), 4) for x in sv[k][:-1]] for k in range(len(CLASSES))},
                       "features": list(row.columns)}
    return out


def run(pid: int, inputs: dict, models: dict):
    """Background job: predict with each chosen model, saving results to Postgres as they arrive."""
    X, _ = train()
    row = pd.DataFrame([inputs])[list(X.columns)]
    results, t0 = {}, time.time()

    def save(status, extra_sql="", extra=()):
        with store.pg() as c:
            c.execute(f"UPDATE predictions SET results=%s, status=%s, seconds=%s {extra_sql} WHERE id=%s",
                      (store.dumps(results), status, round(time.time() - t0, 1), *extra, pid))

    with _lock:
        for kind, size in models.items():
            results[kind] = {"size": size, "status": "running"}
            save("running")
            try:
                ts = time.time()
                r = _predict_one(kind, size, row)
                results[kind] = {"size": size, "status": "ok", "seconds": round(time.time() - ts, 2), **r}
            except Exception as exc:  # noqa: BLE001
                log.exception("prediction %s %s failed", pid, kind)
                results[kind] = {"size": size, "status": "error", "error": f"{type(exc).__name__}: {exc}"}
        ok = [r for r in results.values() if r["status"] == "ok"]
        consensus = None
        if ok:
            p = np.mean([r["proba"] for r in ok], axis=0)
            consensus = {"proba": [round(float(x), 4) for x in p], "pred": int(np.argmax(p)),
                         "agree": len({r["pred"] for r in ok}) == 1, "n": len(ok)}
        results["_consensus"] = consensus
        status = "ok" if ok else "error"
        save(status, ", pred=%s", (consensus["pred"] if consensus else None,))
    # full record to MinIO (inputs + results) so the history is also browsable as files
    with store.pg() as c:
        r = c.execute("SELECT id, label, inputs, models, results, status, created_at, seconds, true_class "
                      "FROM predictions WHERE id=%s", (pid,)).fetchone()
    rec = dict(zip(["id", "label", "inputs", "models", "results", "status", "created_at", "seconds", "true_class"], r, strict=True))
    key = f"predictions/{pid}/record.json"
    store.put_bytes(key, store.dumps(rec).encode(), "application/json")
    with store.pg() as c:
        c.execute("UPDATE predictions SET minio_key=%s WHERE id=%s", (key, pid))


def init_table():
    with store.pg() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY, created_at TIMESTAMPTZ DEFAULT now(), label TEXT,
            inputs JSONB NOT NULL, models JSONB NOT NULL, results JSONB NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'queued', pred INT, seconds REAL, true_class INT, minio_key TEXT)""")


DEFAULT_MODELS = {"catboost": "Full", "tabpfn": "2000", "tabfm": "2000"}
_warming = threading.Event()


def warm():
    """Load the default models in the background so the first patient does not wait ~30 s."""
    if _warming.is_set():
        return
    _warming.set()

    def go():
        for k, v in DEFAULT_MODELS.items():
            try:
                _model(k, v)
            except Exception:  # noqa: BLE001
                log.exception("warm-up of %s failed", k)
    threading.Thread(target=go, daemon=True).start()


def loaded():
    return [f"{k}·{s}" for k, s in _cache]

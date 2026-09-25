import base64, glob, io, os, shutil, subprocess, sys, time, types
from pathlib import Path

STEP = "Step_09_McNemarsTests"
NEEDS = []
GPU = False


def _pip(*a):
    subprocess.run([sys.executable, "-m", "pip", *a], check=True)


if NEEDS:
    _pip("install", "-q", *NEEDS)
if any(n.startswith("tabfm") for n in NEEDS):
    _pip("uninstall", "-y", "-q", "flax")
    for k in [k for k in sys.modules if k == "tabfm" or k.startswith(("tabfm.", "flax"))]:
        del sys.modules[k]
    sys.modules["flax"] = None

import numpy as np
import pandas as pd
import torch
from IPython.display import display

if GPU:
    assert torch.cuda.is_available(), "No GPU - Notebook settings > Accelerator > GPU"

try:
    from kaggle_secrets import UserSecretsClient
    os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
except Exception:
    pass

PROJECT = Path("/kaggle/working/thesis_project")
OUT = PROJECT / STEP
OUT.mkdir(parents=True, exist_ok=True)
for d in glob.glob("/kaggle/input/**/Step_*", recursive=True):
    if os.path.isdir(d) and not (PROJECT / os.path.basename(d)).exists() and os.path.basename(d) != STEP:
        shutil.copytree(d, PROJECT / os.path.basename(d))

LAB_SRC = r'''
import json
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, classification_report,
                             f1_score, roc_auc_score)
from sklearn.model_selection import train_test_split

DSN = "postgresql://lab:lab@127.0.0.1:5432/lab"
PROJECT = Path(__file__).resolve().parent.parent.parent / "thesis_project"
OUT = Path(__file__).resolve().parent / "outputs"
SEED = 42
CLASS_NAMES = ["Low", "Moderate", "High"]
SIZES = {"500": 500, "2000": 2000, "Full": None}


def load_df(table: str) -> pd.DataFrame:
    with psycopg.connect(DSN) as conn:
        return pd.read_sql(f'SELECT * FROM "{table}"', conn)


def step_file(step: str, name: str) -> Path:
    p = PROJECT / step / name
    if not p.exists():
        raise FileNotFoundError(f"{name} not found - run {step} first.")
    return p


def test_rows():
    v = (OUT.parent / "test_rows.txt").read_text().strip().lower()
    return None if v in ("all", "none", "") else int(v)


def load_split():
    tr = pd.read_csv(step_file("Step_04_TrainTestSplit", "train.csv"))
    te = pd.read_csv(step_file("Step_04_TrainTestSplit", "test.csv"))
    X_train, y_train = tr.drop(columns="hair_fall"), tr["hair_fall"]
    X_test, y_test = te.drop(columns="hair_fall"), te["hair_fall"]
    n = test_rows()
    if n and n < len(X_test):
        X_test, y_test = context(X_test, y_test, n)
    print(f"[test set] {len(X_test):,} rows (change in backend/workspace/test_rows.txt)")
    return X_train, X_test, y_train, y_test


def context(X_train, y_train, size):
    if size is None or size >= len(X_train):
        return X_train, y_train
    X_ctx, _, y_ctx, _ = train_test_split(X_train, y_train, train_size=size, stratify=y_train,
                                          random_state=SEED)
    return X_ctx, y_ctx


def device() -> str:
    import torch
    if torch.cuda.is_available():
        return "cuda"
    return "mps" if torch.backends.mps.is_available() else "cpu"


def predict_proba_batched(model, X, batch=500, tag=None):
    ckpt = OUT.parent / "checkpoints" / f"{tag}.npy" if tag else None
    done_parts = []
    if ckpt is not None:
        ckpt.parent.mkdir(exist_ok=True)
        if ckpt.exists():
            saved = np.load(ckpt)
            if len(saved) <= len(X):
                done_parts = [saved]
                print(f"  resuming: {len(saved):,}/{len(X):,} rows already predicted", flush=True)
    start = sum(len(p) for p in done_parts)
    t0 = time.time()
    for i in range(start, len(X), batch):
        done_parts.append(model.predict_proba(X.iloc[i:i + batch]))
        done = min(i + batch, len(X))
        rate = (time.time() - t0) / (done - start)
        print(f"  predicted {done:,}/{len(X):,} rows | elapsed {time.time() - t0:,.0f}s | "
              f"ETA {rate * (len(X) - done):,.0f}s", flush=True)
        if ckpt is not None:
            np.save(ckpt, np.vstack(done_parts))
    return np.vstack(done_parts)


def evaluate(model_name, size_label, n_context, y_true, proba, fit_seconds, predict_seconds, extra=None):
    rows = y_true.index if hasattr(y_true, "index") else np.arange(len(y_true))
    y_true = np.asarray(y_true)
    y_pred = proba.argmax(axis=1)
    m = {
        "model": model_name, "size": size_label, "context_rows": int(n_context), "test_rows": int(len(y_true)),
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "macro_f1": round(f1_score(y_true, y_pred, average="macro"), 4),
        "weighted_f1": round(f1_score(y_true, y_pred, average="weighted"), 4),
        "roc_auc_ovr": round(roc_auc_score(y_true, proba, multi_class="ovr", average="macro"), 4),
        "fit_seconds": round(fit_seconds, 1), "predict_seconds": round(predict_seconds, 1),
        **(extra or {}),
    }
    print(json.dumps(m, indent=2))
    print(classification_report(y_true, y_pred, target_names=CLASS_NAMES, digits=4))

    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_predictions(y_true, y_pred, display_labels=CLASS_NAMES, cmap="Blues", ax=ax,
                                            colorbar=False)
    ax.set_title(f"{model_name} ({size_label}) - confusion matrix")
    fig.tight_layout()
    fig.savefig(OUT / "confusion_matrix.png", dpi=150)
    plt.show()

    (OUT / "metrics.json").write_text(json.dumps(m, indent=2))
    pd.DataFrame({"row": rows, "y_true": y_true, "y_pred": y_pred, **{f"p_{c}": proba[:, i] for i, c in enumerate(CLASS_NAMES)}}) \
        .to_csv(OUT / "predictions.csv", index=False)
    return m


def shap_report(model_name, size_label, shap_values, X_explained, seconds, extra=None):
    import shap
    sv = np.stack(shap_values, axis=-1) if isinstance(shap_values, list) else np.asarray(shap_values)
    if sv.ndim == 2:
        sv = sv[..., None]
    feats = list(X_explained.columns)
    imp = pd.DataFrame({"feature": feats, **{f"mean_abs_{c}": np.abs(sv[:, :, i]).mean(0) for i, c in enumerate(CLASS_NAMES)}})
    imp["mean_abs_all"] = imp[[f"mean_abs_{c}" for c in CLASS_NAMES]].mean(1)
    imp = imp.sort_values("mean_abs_all", ascending=False).reset_index(drop=True)
    imp.to_csv(OUT / "shap_importance.csv", index=False)
    print(imp.round(4).to_string(index=False))

    fig, ax = plt.subplots(figsize=(7, 6))
    top = imp.head(15)[::-1]
    ax.barh(top["feature"], top["mean_abs_all"], color="#2563eb")
    ax.set_xlabel("mean |SHAP| (averaged over classes)")
    ax.set_title(f"{model_name} ({size_label}) - global feature importance")
    fig.tight_layout(); fig.savefig(OUT / "shap_global_importance.png", dpi=150); plt.show()

    plt.figure()
    shap.summary_plot(sv[:, :, 2], X_explained, show=False, max_display=15)
    plt.title(f"{model_name} ({size_label}) - SHAP for High risk")
    plt.tight_layout(); plt.savefig(OUT / "shap_beeswarm_high.png", dpi=150); plt.show()

    summary = {"model": model_name, "size": size_label, "rows_explained": int(len(X_explained)),
               "seconds": round(seconds, 1), "top_5": imp["feature"].head(5).tolist(), **(extra or {})}
    (OUT / "shap_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return imp
'''
sys.modules.setdefault("psycopg", types.ModuleType("psycopg"))
lab = types.ModuleType("lab")
lab.__file__ = "/kaggle/working/lab.py"
exec(compile(LAB_SRC, "lab.py", "exec"), lab.__dict__)
sys.modules["lab"] = lab
lab.PROJECT, lab.OUT = PROJECT, OUT
lab.test_rows = lambda: None
lab.device = lambda: "cuda" if torch.cuda.is_available() else "cpu"


def _load_df(table):
    hits = glob.glob("/kaggle/input/**/data.csv", recursive=True)
    assert hits, "data.csv not found under /kaggle/input - add a dataset containing data.csv"
    return pd.read_csv(hits[0])


lab.load_df = _load_df

def _chunk_predict(cls, chunk):
    orig = cls.predict_proba

    def predict_proba(self, X, *a, **k):
        parts, i, b = [], 0, chunk
        while i < len(X):
            try:
                parts.append(orig(self, X.iloc[i:i + b] if hasattr(X, "iloc") else X[i:i + b], *a, **k))
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                if b == 1:
                    raise
                b = max(1, b // 2)
                print(f"  GPU out of memory -> batch size {b}", flush=True)
                continue
            i += b
        return np.vstack(parts)

    cls.predict_proba = predict_proba


if any(n.startswith("tabpfn") for n in NEEDS):
    from tabpfn import TabPFNClassifier
    _chunk_predict(TabPFNClassifier, 500)

if any(n.startswith("tabfm") for n in NEEDS):
    from tabfm import TabFMClassifier
    from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1
    _chunk_predict(TabFMClassifier, 100)
    _sdpa = torch.nn.functional.scaled_dot_product_attention

    def _chunked_sdpa(q, k, v, attn_mask=None, **kw):
        n, Q = q.shape[-2], 1024
        if n <= Q:
            return _sdpa(q, k, v, attn_mask=attn_mask, **kw)
        out = []
        for s in range(0, n, Q):
            m = attn_mask[..., s:s + Q, :] if attn_mask is not None and attn_mask.shape[-2] == n else attn_mask
            out.append(_sdpa(q[..., s:s + Q, :], k, v, attn_mask=m, **kw))
        return torch.cat(out, dim=-2)

    torch.nn.functional.scaled_dot_product_attention = _chunked_sdpa
    _tabfm_load = tabfm_v1.load

    def _load(*a, **k):
        k.setdefault("device", "cuda")
        net = _tabfm_load(*a, **k)
        for mod in net.modules():
            if hasattr(mod, "col_chunk_size"):
                mod.col_chunk_size = 4
        return net

    tabfm_v1.load = _load


import builtins

_LOG, _NB_STDOUT, _print = io.StringIO(), sys.stdout, builtins.print


def _logged_print(*a, **k):
    _print(*a, **k)
    if k.get("file") is None:
        _print(*a, **{**k, "file": _LOG, "flush": False})


builtins.print = _logged_print
if GPU:
    print(f"GPU: {torch.cuda.get_device_name(0)}")

_display = display


def display(obj, *a, **k):
    _display(obj, *a, **k)
    _LOG.write(repr(obj) + "\n")


_T0 = time.time()
import itertools

import pandas as pd
from lab import OUT, PROJECT
from statsmodels.stats.contingency_tables import mcnemar

MODELS = {"CatBoost": "Step_05", "TabPFN": "Step_06", "TabFM": "Step_07"}
LETTERS = {"500": "a", "2000": "b", "Full": "c"}

rows = []
for size, letter in LETTERS.items():
    preds = {}
    for name, prefix in MODELS.items():
        f = PROJECT / f"{prefix}{letter}_{name}_{size}" / "predictions.csv"
        if f.exists():
            d = pd.read_csv(f)
            preds[name] = d.set_index("row").assign(correct=lambda x: x.y_true == x.y_pred)["correct"]
        else:
            print(f"[skip] {name} {size}: not trained yet")
    for a, b in itertools.combinations(preds, 2):
        common = preds[a].index.intersection(preds[b].index)
        ca, cb = preds[a].loc[common], preds[b].loc[common]
        table = [[int((ca & cb).sum()), int((ca & ~cb).sum())], [int((~ca & cb).sum()), int((~ca & ~cb).sum())]]
        res = mcnemar(table, exact=False, correction=True)
        rows.append({"size": size, "comparison": f"{a} vs {b}", "test_rows": len(common),
                     f"only_{a}_correct": table[0][1], "only_other_correct": table[1][0],
                     "chi2": round(float(res.statistic), 4), "p_value": round(float(res.pvalue), 4),
                     "significant_0.05": bool(res.pvalue < 0.05)})

results = pd.DataFrame(rows)
display(results)
results.to_csv(OUT / "mcnemar_results.csv", index=False)

builtins.print = _print
(OUT / "output.txt").write_text(_LOG.getvalue() + f"\n[finished OK | time: {round(time.time() - _T0, 1)}s]\n")
shutil.make_archive(f"/kaggle/working/{STEP}", "zip", root_dir=PROJECT, base_dir=STEP)
ZIP = f"/kaggle/working/{STEP}.zip"
print(f"Done -> {ZIP}   (import on the Mac: cd backend && .venv/bin/python import_kaggle_run.py ~/Downloads/{STEP}.zip)")

from IPython.display import HTML, FileLink, display
import html
display(HTML("<pre style='white-space:pre-wrap;font-size:12px'>" + html.escape(_LOG.getvalue()) + "</pre>"))
b64 = base64.b64encode(open(ZIP, "rb").read()).decode()
display(HTML(f'<a id="dl_{STEP}" download="{STEP}.zip" href="data:application/zip;base64,{b64}">Download {STEP}.zip</a>'
             f'<script>try{{var k="dl_{STEP}_{_T0}";if(!localStorage.getItem(k)){{localStorage.setItem(k,1);document.getElementById("dl_{STEP}").click()}}}}catch(e){{document.getElementById("dl_{STEP}").click()}}</script>'))
display(FileLink(ZIP))

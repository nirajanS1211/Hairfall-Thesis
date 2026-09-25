# Step 7c - TabFM · Full  (Kaggle GPU version)
# Same logic as backend/steps/Step_07c_TabFM_Full.py + backend/workspace/lab.py, but standalone and on a CUDA GPU.
# Paste into ONE Kaggle notebook cell. Settings: Accelerator = GPU, Internet = On. Add HF_TOKEN under Add-ons > Secrets (optional).
# Add a dataset containing train.csv and test.csv (from thesis_project/Step_04_TrainTestSplit/).
# Result: /kaggle/working/Step_07c_TabFM_Full/  (+ Step_07c_TabFM_Full.zip)  ->  download the zip.
import glob, io, json, os, shutil, subprocess, sys, time
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "tabfm[pytorch]==1.0.1"], check=True)
# Kaggle ships an old JAX/Flax that crashes tabfm's import (it expects ImportError, gets AttributeError).
# Removing flax makes tabfm use its PyTorch backend, exactly like the Mac.
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "flax"], check=True)
for k in [k for k in sys.modules if k == "tabfm" or k.startswith(("tabfm.", "flax"))]:
    del sys.modules[k]  # drop a half-imported copy left by an earlier failed run in this session
sys.modules["flax"] = None  # any `import flax` now raises ImportError -> tabfm falls back to PyTorch

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, classification_report,
                             f1_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from tabfm import TabFMClassifier
from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1

try:
    from kaggle_secrets import UserSecretsClient
    os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
except Exception:
    pass

STEP = "Step_07c_TabFM_Full"
OUT = f"/kaggle/working/{STEP}"
CKPT = "/kaggle/working/checkpoints"
os.makedirs(OUT, exist_ok=True); os.makedirs(CKPT, exist_ok=True)
SEED = 42
CLASS_NAMES = ["Low", "Moderate", "High"]
SIZE = "Full"
BATCH = 100        # test rows per prediction batch (halved automatically if the GPU runs out of memory)
TEST_ROWS = None   # None = whole test set (4,322 rows, same as 7a/7b)

assert torch.cuda.is_available(), "No GPU - Notebook settings > Accelerator > GPU"


class Tee(io.TextIOBase):  # everything printed is also saved to output.txt
    def __init__(self, *s): self.s = s
    def write(self, t):
        for x in self.s: x.write(t)
        return len(t)
    def flush(self):
        for x in self.s: x.flush()


LOG = io.StringIO()
sys.stdout = Tee(sys.__stdout__, LOG)
print(f"GPU: {torch.cuda.get_device_name(0)}")


def context(X, y, size):
    if size is None or size >= len(X):
        return X, y
    Xc, _, yc, _ = train_test_split(X, y, train_size=size, stratify=y, random_state=SEED)
    return Xc, yc


def predict_proba_batched(model, X, batch, tag):
    ckpt = f"{CKPT}/{tag}.npy"
    parts = [np.load(ckpt)] if os.path.exists(ckpt) else []
    start = sum(len(p) for p in parts)
    if start:
        print(f"  resuming: {start:,}/{len(X):,} rows already predicted", flush=True)
    t0, i = time.time(), start
    while i < len(X):
        try:
            parts.append(model.predict_proba(X.iloc[i:i + batch]))
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            batch = max(1, batch // 2)
            print(f"  GPU out of memory -> batch size {batch}", flush=True)
            continue
        i = min(i + batch, len(X))
        rate = (time.time() - t0) / max(i - start, 1)
        print(f"  predicted {i:,}/{len(X):,} rows | elapsed {time.time() - t0:,.0f}s | "
              f"ETA {rate * (len(X) - i):,.0f}s", flush=True)
        np.save(ckpt, np.vstack(parts))
    return np.vstack(parts)


def evaluate(model_name, size_label, n_context, y_true, proba, fit_seconds, predict_seconds):
    rows = y_true.index
    y_true = np.asarray(y_true)
    y_pred = proba.argmax(axis=1)
    m = {
        "model": model_name, "size": size_label, "context_rows": int(n_context), "test_rows": int(len(y_true)),
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "macro_f1": round(f1_score(y_true, y_pred, average="macro"), 4),
        "weighted_f1": round(f1_score(y_true, y_pred, average="weighted"), 4),
        "roc_auc_ovr": round(roc_auc_score(y_true, proba, multi_class="ovr", average="macro"), 4),
        "fit_seconds": round(fit_seconds, 1), "predict_seconds": round(predict_seconds, 1),
    }
    print(json.dumps(m, indent=2))
    print(classification_report(y_true, y_pred, target_names=CLASS_NAMES, digits=4))
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_predictions(y_true, y_pred, display_labels=CLASS_NAMES, cmap="Blues", ax=ax,
                                            colorbar=False)
    ax.set_title(f"{model_name} ({size_label}) - confusion matrix")
    fig.tight_layout()
    fig.savefig(f"{OUT}/confusion_matrix.png", dpi=150)
    plt.show()
    open(f"{OUT}/metrics.json", "w").write(json.dumps(m, indent=2))
    pd.DataFrame({"row": rows, "y_true": y_true, "y_pred": y_pred,
                  **{f"p_{c}": proba[:, i] for i, c in enumerate(CLASS_NAMES)}}).to_csv(f"{OUT}/predictions.csv", index=False)
    return m


def find(name):
    hits = glob.glob(f"/kaggle/input/**/{name}", recursive=True)
    assert hits, f"{name} not found under /kaggle/input - add the dataset with train.csv and test.csv"
    return hits[0]


tr, te = pd.read_csv(find("train.csv")), pd.read_csv(find("test.csv"))
X_train, y_train = tr.drop(columns="hair_fall"), tr["hair_fall"]
X_test, y_test = te.drop(columns="hair_fall"), te["hair_fall"]
if TEST_ROWS and TEST_ROWS < len(X_test):
    X_test, y_test = context(X_test, y_test, TEST_ROWS)
print(f"[test set] {len(X_test):,} rows")
X_ctx, y_ctx = context(X_train, y_train, None)
print(f"Context rows: {len(X_ctx):,} | Test rows: {len(X_test):,}")

t = time.time()
model = TabFMClassifier(model=tabfm_v1.load(device="cuda"), n_estimators=1)  # load() defaults to CPU!
model.fit(X_ctx, y_ctx)
fit_s = time.time() - t

t = time.time()
proba = predict_proba_batched(model, X_test, BATCH, tag=f"tabfm_{SIZE}_{len(X_test)}")
pred_s = time.time() - t
m = evaluate("TabFM", SIZE, len(X_ctx), y_test, proba, fit_s, pred_s)
print(m)

sys.stdout = sys.__stdout__
open(f"{OUT}/output.txt", "w").write(LOG.getvalue())
shutil.make_archive(f"/kaggle/working/{STEP}", "zip", OUT)
print(f"Done -> download /kaggle/working/{STEP}.zip")

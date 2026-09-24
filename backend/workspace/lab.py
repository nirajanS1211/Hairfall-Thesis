"""Shared helpers for the thesis steps.

The dataset is loaded into Postgres automatically when the backend starts, so steps
only ever *read* it. Every file a step writes to outputs/ is saved into
thesis_project/<Step>/ once the step finishes successfully.
"""
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
SIZES = {"500": 500, "2000": 2000, "Full": None}  # training-context sizes used in steps 5-8


def load_df(table: str) -> pd.DataFrame:
    """Read a table from the local Postgres (read-only use)."""
    with psycopg.connect(DSN) as conn:
        return pd.read_sql(f'SELECT * FROM "{table}"', conn)


def step_file(step: str, name: str) -> Path:
    """Path of a file saved by an earlier step, with a clear error if that step hasn't run."""
    p = PROJECT / step / name
    if not p.exists():
        raise FileNotFoundError(f"{name} not found - run {step} first.")
    return p


def load_split():
    """Train/test split written by Step 4."""
    tr = pd.read_csv(step_file("Step_04_TrainTestSplit", "train.csv"))
    te = pd.read_csv(step_file("Step_04_TrainTestSplit", "test.csv"))
    return tr.drop(columns="hair_fall"), te.drop(columns="hair_fall"), tr["hair_fall"], te["hair_fall"]


def context(X_train, y_train, size):
    """Stratified training subset of `size` rows (None = all). Same rows for every model."""
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


def predict_proba_batched(model, X, batch=500):
    """predict_proba in batches with progress + ETA (foundation models are slow on big test sets)."""
    parts, t0 = [], time.time()
    for i in range(0, len(X), batch):
        parts.append(model.predict_proba(X.iloc[i:i + batch]))
        done = min(i + batch, len(X))
        eta = (time.time() - t0) / done * (len(X) - done)
        print(f"  predicted {done:,}/{len(X):,} rows | elapsed {time.time() - t0:,.0f}s | ETA {eta:,.0f}s",
              flush=True)
    return np.vstack(parts)


def evaluate(model_name, size_label, n_context, y_true, proba, fit_seconds, predict_seconds, extra=None):
    """Metrics + confusion matrix; saves metrics.json and predictions.csv to outputs/."""
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
    pd.DataFrame({"y_true": y_true, "y_pred": y_pred, **{f"p_{c}": proba[:, i] for i, c in enumerate(CLASS_NAMES)}}) \
        .to_csv(OUT / "predictions.csv", index=False)
    return m

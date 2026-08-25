"""Run a TabFM hair-fall-risk prediction locally.

TabFM needs more RAM than Render's free tier provides, so the hosted API
doesn't serve it. This script reuses the same model-loading and prediction
logic to run on your own machine instead.

Usage:
    cd backend
    pip install -r requirements.txt
    python scripts/predict_tabfm_local.py scripts/sample_patient.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from schemas import CLASS_NAMES, FEATURE_COLUMNS, PatientInput, compute_warnings, to_dataframe

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python predict_tabfm_local.py <patient.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        raw = json.load(f)
    data = PatientInput(**raw)

    print("Loading TabFM (downloads weights from Hugging Face on first run)...")
    from tabfm import TabFMClassifier
    from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1_0_0

    X_train = pd.read_csv(MODELS_DIR / "tabfm_500row_context_X.csv")[FEATURE_COLUMNS]
    y_train = pd.read_csv(MODELS_DIR / "tabfm_500row_context_y.csv").iloc[:, 0]

    base_model = tabfm_v1_0_0.load()
    model = TabFMClassifier(model=base_model, n_estimators=1)
    model.fit(X_train, y_train)

    X = to_dataframe(data)
    pred_idx = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]

    print(f"\nPrediction: {CLASS_NAMES[pred_idx]}")
    for i, p in enumerate(proba):
        print(f"  {CLASS_NAMES[i]}: {round(float(p), 4)}")
    for w in compute_warnings(data):
        print(f"Warning: {w}")


if __name__ == "__main__":
    main()

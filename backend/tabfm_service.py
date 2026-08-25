import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool

from schemas import CLASS_NAMES, FEATURE_COLUMNS, PatientInput, compute_warnings, to_dataframe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hairfall.tabfm")

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

app = FastAPI(title="Hair Fall Risk Prediction API - TabFM")

X_train_tabfm: Optional[pd.DataFrame] = None
y_train_tabfm = None
tabfm_model = None
tabfm_error: Optional[str] = None


def _load_model() -> None:
    """Runs after uvicorn has bound $PORT, so Render's port scan succeeds immediately."""
    global X_train_tabfm, y_train_tabfm, tabfm_model, tabfm_error

    X_train_tabfm = pd.read_csv(MODELS_DIR / "tabfm_500row_context_X.csv")[FEATURE_COLUMNS]
    y_train_tabfm = pd.read_csv(MODELS_DIR / "tabfm_500row_context_y.csv").iloc[:, 0]

    try:
        from tabfm import TabFMClassifier
        from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1_0_0

        tabfm_base_model = tabfm_v1_0_0.load()
        tabfm_model = TabFMClassifier(model=tabfm_base_model, n_estimators=1)
        tabfm_model.fit(X_train_tabfm, y_train_tabfm)
        tabfm_model.predict(X_train_tabfm.iloc[[0]])
        logger.info("TabFM loaded, fit on 500-row context, and warmed up.")
    except Exception as exc:  # noqa: BLE001
        tabfm_error = f"Failed to initialize TabFM: {exc}"
        logger.exception(tabfm_error)
        tabfm_model = None


@app.on_event("startup")
async def on_startup():
    await run_in_threadpool(_load_model)


def predict_tabfm(data: PatientInput) -> dict:
    if tabfm_model is None:
        raise HTTPException(status_code=503, detail=tabfm_error or "TabFM is not available on this server.")
    X = to_dataframe(data)
    pred_idx = int(tabfm_model.predict(X)[0])
    proba = tabfm_model.predict_proba(X)[0]
    return {
        "prediction": CLASS_NAMES[pred_idx],
        "confidence": {CLASS_NAMES[i]: round(float(p), 4) for i, p in enumerate(proba)},
        "warnings": compute_warnings(data),
    }


@app.get("/")
async def root():
    return {"service": "Hair Fall Risk Prediction API - TabFM", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "tabfm": tabfm_model is not None, "tabfm_error": tabfm_error}


@app.post("/api/predict/tabfm")
async def api_predict_tabfm(data: PatientInput):
    try:
        return await run_in_threadpool(predict_tabfm, data)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("TabFM prediction failed")
        raise HTTPException(status_code=502, detail=f"TabFM prediction failed: {exc}") from exc

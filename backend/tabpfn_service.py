import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool

from schemas import CLASS_NAMES, FEATURE_COLUMNS, PatientInput, compute_warnings, to_dataframe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hairfall.tabpfn")

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

app = FastAPI(title="Hair Fall Risk Prediction API - TabPFN")

X_train_context: Optional[pd.DataFrame] = None
y_train_context = None
tabpfn_model = None
tabpfn_error: Optional[str] = None


def _load_model() -> None:
    """Runs after uvicorn has bound $PORT, so Render's port scan succeeds immediately."""
    global X_train_context, y_train_context, tabpfn_model, tabpfn_error

    X_train_context = pd.read_csv(MODELS_DIR / "tabpfn_context_X_full.csv")[FEATURE_COLUMNS]
    y_train_context = pd.read_csv(MODELS_DIR / "tabpfn_context_y_full.csv").iloc[:, 0]

    token = os.environ.get("TABPFN_TOKEN")
    if not token:
        tabpfn_error = "TABPFN_TOKEN environment variable is not set."
        logger.warning(tabpfn_error)
        return

    try:
        import tabpfn_client

        tabpfn_client.set_access_token(token)
        from tabpfn_client import TabPFNClassifier

        tabpfn_model = TabPFNClassifier()
        tabpfn_model.fit(X_train_context, y_train_context)
        logger.info("TabPFN client configured and fit on full-dataset context.")
    except Exception as exc:  # noqa: BLE001
        tabpfn_error = f"Failed to initialize TabPFN client: {exc}"
        logger.exception(tabpfn_error)
        tabpfn_model = None


@app.on_event("startup")
async def on_startup():
    await run_in_threadpool(_load_model)


def predict_tabpfn(data: PatientInput) -> dict:
    if tabpfn_model is None:
        raise HTTPException(status_code=503, detail=tabpfn_error or "TabPFN is not available on this server.")
    X = to_dataframe(data)
    pred_idx = int(tabpfn_model.predict(X)[0])
    proba = tabpfn_model.predict_proba(X)[0]
    return {
        "prediction": CLASS_NAMES[pred_idx],
        "confidence": {CLASS_NAMES[i]: round(float(p), 4) for i, p in enumerate(proba)},
        "warnings": compute_warnings(data),
    }


@app.get("/")
async def root():
    return {"service": "Hair Fall Risk Prediction API - TabPFN", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "tabpfn": tabpfn_model is not None, "tabpfn_error": tabpfn_error}


@app.post("/api/predict/tabpfn")
async def api_predict_tabpfn(data: PatientInput):
    try:
        return await run_in_threadpool(predict_tabpfn, data)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("TabPFN prediction failed")
        raise HTTPException(status_code=502, detail=f"TabPFN cloud request failed: {exc}") from exc

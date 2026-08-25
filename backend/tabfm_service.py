import json
import logging
from pathlib import Path
from typing import Literal, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from features import FEATURE_META

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hairfall.tabfm")

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

app = FastAPI(title="Hair Fall Risk Prediction API - TabFM")

with open(MODELS_DIR / "feature_columns.json") as f:
    FEATURE_COLUMNS: list[str] = json.load(f)
with open(MODELS_DIR / "class_names.json") as f:
    CLASS_NAMES: list[str] = json.load(f)

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


def _bounds(name: str) -> tuple[float, float]:
    meta = FEATURE_META[name]
    return meta["hard_min"], meta["hard_max"]


class PatientInput(BaseModel):
    age: float = Field(..., ge=_bounds("age")[0], le=_bounds("age")[1])
    gender: Literal[0, 1, 2]
    total_protein: float = Field(..., ge=_bounds("total_protein")[0], le=_bounds("total_protein")[1])
    calcium: float = Field(..., ge=_bounds("calcium")[0], le=_bounds("calcium")[1])
    iron: float = Field(..., ge=_bounds("iron")[0], le=_bounds("iron")[1])
    vitamin_d: float = Field(..., ge=_bounds("vitamin_d")[0], le=_bounds("vitamin_d")[1])
    alt_liver: float = Field(..., ge=_bounds("alt_liver")[0], le=_bounds("alt_liver")[1])
    manganese: float = Field(..., ge=_bounds("manganese")[0], le=_bounds("manganese")[1])
    body_water_content: float = Field(..., ge=_bounds("body_water_content")[0], le=_bounds("body_water_content")[1])
    stress_level: float = Field(..., ge=_bounds("stress_level")[0], le=_bounds("stress_level")[1])
    total_keratine: float = Field(..., ge=_bounds("total_keratine")[0], le=_bounds("total_keratine")[1])
    hair_texture: float = Field(..., ge=_bounds("hair_texture")[0], le=_bounds("hair_texture")[1])
    family_hair_fall_history: Literal[0, 1]
    chronic_illness: Literal[0, 1]
    late_night_sleep: Literal[0, 1]
    sleep_disturbance: Literal[0, 1]
    water_reason: Literal[0, 1]
    chemical_use: Literal[0, 1]
    anemia: Literal[0, 1]
    stress: Literal[0, 1]


def to_dataframe(data: PatientInput) -> pd.DataFrame:
    row = data.model_dump()
    return pd.DataFrame([row])[FEATURE_COLUMNS]


def compute_warnings(data: PatientInput) -> list[str]:
    warnings = []
    row = data.model_dump()
    for name, meta in FEATURE_META.items():
        if meta["type"] != "number":
            continue
        value = row[name]
        lo, hi = meta["train_min"], meta["train_max"]
        if value < lo or value > hi:
            warnings.append(
                f"{meta['label']} = {value} is outside the training data range "
                f"({lo}–{hi}); this prediction may be less reliable."
            )
    return warnings


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

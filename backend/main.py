import json
import logging
import os
from pathlib import Path
from typing import Literal, Optional

import pandas as pd
from catboost import CatBoostClassifier
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import db
from features import FEATURE_GROUPS, FEATURE_META
from results import EVALUATION_RESULTS
from scripts.clean_dataset import load_clean_dataset

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hairfall")

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
SHAP_DIR = BASE_DIR / "static" / "shap_reference"

app = FastAPI(title="Hair Fall Risk Prediction API")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

_default_origins = ",".join(
    f"http://{host}:{port}"
    for host in ("localhost", "127.0.0.1")
    for port in (5173, 5174, 5175)
)
allowed_origins = os.environ.get("FRONTEND_ORIGINS", _default_origins).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open(MODELS_DIR / "feature_columns.json") as f:
    FEATURE_COLUMNS: list[str] = json.load(f)
with open(MODELS_DIR / "class_names.json") as f:
    CLASS_NAMES: list[str] = json.load(f)

cb_model = CatBoostClassifier()
cb_model.load_model(str(MODELS_DIR / "catboost_model_production.cbm"))

import shap  # noqa: E402

cb_explainer = shap.TreeExplainer(cb_model)

X_train_context = pd.read_csv(MODELS_DIR / "tabpfn_context_X_full.csv")[FEATURE_COLUMNS]
y_train_context = pd.read_csv(MODELS_DIR / "tabpfn_context_y_full.csv").iloc[:, 0]

tabpfn_model = None
tabpfn_error: Optional[str] = None

token = os.environ.get("TABPFN_TOKEN")
if not token:
    tabpfn_error = "TABPFN_TOKEN environment variable is not set."
    logger.warning(tabpfn_error)
else:
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

X_train_tabfm = pd.read_csv(MODELS_DIR / "tabfm_500row_context_X.csv")[FEATURE_COLUMNS]
y_train_tabfm = pd.read_csv(MODELS_DIR / "tabfm_500row_context_y.csv").iloc[:, 0]

tabfm_model = None
tabfm_error: Optional[str] = None

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

SHAP_IMAGES = {
    "catboost_shap_global": "catboost_shap_global_importance.png",
    "catboost_shap_beeswarm": "catboost_shap_beeswarm_high.png",
    "catboost_shap_waterfall": "catboost_shap_waterfall_patient.png",
    "catboost_confusion_matrix": "catboost_confusion_matrix.png",
    "catboost_training_curve": "catboost_training_curve.png",
    "tabpfn_shap_global": "tabpfn_shap_global_importance.png",
    "tabpfn_shap_beeswarm": "tabpfn_shap_beeswarm_high.png",
    "tabpfn_shap_waterfall": "tabpfn_shap_waterfall_patient.png",
    "tabpfn_confusion_matrix": "tabpfn_confusion_matrix.png",
    "tabfm_shap_global": "tabfm_shap_global_importance.png",
    "tabfm_shap_beeswarm": "tabfm_shap_beeswarm_high.png",
    "tabfm_shap_waterfall": "tabfm_shap_waterfall_patient.png",
    "tabfm_confusion_matrix": "tabfm_confusion_matrix.png",
    "catboost_confusion_matrix_2000ctx": "catboost_confusion_matrix_2000ctx.png",
    "tabpfn_confusion_matrix_2000ctx": "tabpfn_confusion_matrix_2000ctx.png",
    "tabfm_confusion_matrix_2000ctx": "tabfm_confusion_matrix_2000ctx.png",
    "matched_2000ctx_chart": "matched_2000ctx_chart.png",
}
SHAP_IMAGES_AVAILABLE = {key: (SHAP_DIR / name).exists() for key, name in SHAP_IMAGES.items()}

_dataset_cache: Optional[pd.DataFrame] = None


@app.on_event("startup")
async def on_startup():
    db.init_db()


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


class PredictionLogRequest(BaseModel):
    input: PatientInput
    catboost_result: Optional[dict] = None
    tabpfn_result: Optional[dict] = None
    tabfm_result: Optional[dict] = None


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


def predict_catboost(data: PatientInput) -> dict:
    X = to_dataframe(data)
    pred_idx = int(cb_model.predict(X)[0][0])
    proba = cb_model.predict_proba(X)[0]

    shap_vals = cb_explainer.shap_values(X)
    class_shap = shap_vals[0, :, pred_idx]
    ranked = sorted(zip(FEATURE_COLUMNS, class_shap), key=lambda x: abs(x[1]), reverse=True)[:5]
    top_features = [
        {
            "feature": name,
            "label": FEATURE_META[name]["label"],
            "shap": round(float(val), 4),
            "direction": "increases" if val > 0 else "decreases",
        }
        for name, val in ranked
    ]

    return {
        "prediction": CLASS_NAMES[pred_idx],
        "confidence": {CLASS_NAMES[i]: round(float(p), 4) for i, p in enumerate(proba)},
        "top_features": top_features,
        "warnings": compute_warnings(data),
    }


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
    return {"service": "Hair Fall Risk Prediction API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "catboost": True,
        "tabpfn": tabpfn_model is not None,
        "tabpfn_error": tabpfn_error,
        "tabfm": tabfm_model is not None,
        "tabfm_error": tabfm_error,
        "mongodb": db.get_db() is not None,
        "mongodb_error": db.connection_error,
    }


@app.get("/api/meta")
async def api_meta():
    return {
        "feature_groups": FEATURE_GROUPS,
        "feature_meta": FEATURE_META,
        "class_names": CLASS_NAMES,
        "tabpfn_available": tabpfn_model is not None,
        "tabpfn_error": tabpfn_error,
        "tabfm_available": tabfm_model is not None,
        "tabfm_error": tabfm_error,
        "shap_images": {k: f"/static/shap_reference/{v}" for k, v in SHAP_IMAGES.items()},
        "shap_images_available": SHAP_IMAGES_AVAILABLE,
    }


@app.post("/api/predict/catboost")
async def api_predict_catboost(data: PatientInput):
    try:
        return await run_in_threadpool(predict_catboost, data)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("CatBoost prediction failed")
        raise HTTPException(status_code=500, detail=f"CatBoost prediction failed: {exc}") from exc


@app.post("/api/predict/tabpfn")
async def api_predict_tabpfn(data: PatientInput):
    try:
        return await run_in_threadpool(predict_tabpfn, data)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("TabPFN prediction failed")
        raise HTTPException(status_code=502, detail=f"TabPFN cloud request failed: {exc}") from exc


@app.post("/api/predict/tabfm")
async def api_predict_tabfm(data: PatientInput):
    try:
        return await run_in_threadpool(predict_tabfm, data)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("TabFM prediction failed")
        raise HTTPException(status_code=502, detail=f"TabFM prediction failed: {exc}") from exc


@app.post("/api/predictions/log")
async def api_log_prediction(payload: PredictionLogRequest):
    record = {
        "input": payload.input.model_dump(),
        "catboost_result": payload.catboost_result,
        "tabpfn_result": payload.tabpfn_result,
        "tabfm_result": payload.tabfm_result,
    }
    inserted_id = await run_in_threadpool(db.log_prediction, record)
    if inserted_id is None:
        return {"logged": False, "reason": db.connection_error or "MongoDB not configured."}
    return {"logged": True, "id": inserted_id}


@app.get("/api/predictions/history")
async def api_prediction_history(limit: int = 20, skip: int = 0):
    if db.get_db() is None:
        raise HTTPException(status_code=503, detail=db.connection_error or "MongoDB is not configured.")
    limit = max(1, min(limit, 100))
    items = await run_in_threadpool(db.get_prediction_history, limit, skip)
    total = await run_in_threadpool(db.get_prediction_count)
    for item in items:
        if "timestamp" in item and item["timestamp"] is not None:
            item["timestamp"] = item["timestamp"].isoformat()
    return {"items": items, "total": total, "limit": limit, "skip": skip}


def _dataset_summary_from_csv() -> dict:
    global _dataset_cache
    if _dataset_cache is None:
        _dataset_cache = load_clean_dataset()
    df = _dataset_cache
    counts = df["hair_fall"].value_counts().to_dict()
    numeric_fields = [
        "age", "total_protein", "calcium", "iron", "vitamin_d", "alt_liver",
        "manganese", "body_water_content", "stress_level", "total_keratine", "hair_texture",
    ]
    stats = {}
    for field in numeric_fields:
        stats[f"{field}_mean"] = round(float(df[field].mean()), 3)
        stats[f"{field}_min"] = round(float(df[field].min()), 3)
        stats[f"{field}_max"] = round(float(df[field].max()), 3)
    corr = df[numeric_fields].corr().round(3)
    return {
        "row_count": len(df),
        "class_distribution": {
            "Low": int(counts.get(0, 0)),
            "Moderate": int(counts.get(1, 0)),
            "High": int(counts.get(2, 0)),
        },
        "feature_stats": stats,
        "correlation": {row: corr.loc[row].to_dict() for row in corr.index},
        "correlation_fields": numeric_fields,
        "source": "local CSV (MongoDB dataset collection not yet seeded)",
    }


@app.get("/api/analysis/dataset-summary")
async def api_dataset_summary():
    summary = await run_in_threadpool(db.get_dataset_summary)
    if summary is not None:
        summary["source"] = "mongodb"
        return summary
    return await run_in_threadpool(_dataset_summary_from_csv)


@app.get("/api/analysis/results")
async def api_analysis_results():
    return EVALUATION_RESULTS

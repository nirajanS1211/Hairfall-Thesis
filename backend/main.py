import logging
import os
from pathlib import Path
from typing import Optional

import httpx
import pandas as pd
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import auth
import db
from features import FEATURE_GROUPS, FEATURE_META
from results import EVALUATION_RESULTS
from schemas import CLASS_NAMES, PatientInput, PredictionLogRequest
from scripts.clean_dataset import load_clean_dataset

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hairfall")

BASE_DIR = Path(__file__).resolve().parent
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

CATBOOST_SERVICE_URL = os.environ.get("CATBOOST_SERVICE_URL", "").rstrip("/")
TABPFN_SERVICE_URL = os.environ.get("TABPFN_SERVICE_URL", "").rstrip("/")
TABFM_SERVICE_URL = os.environ.get("TABFM_SERVICE_URL", "").rstrip("/")

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

DEFAULT_SITE_SETTINGS = {
    "university_line": "Tribhuvan University · Central Department of CSIT · M.Sc. CSIT Dissertation",
    "submitted_by": "Nirajan Shahi · Roll No. 49/079",
    "supervised_by": "Asst. Prof. Jagadish Bhatta",
}


class LoginRequest(BaseModel):
    email: str
    password: str


class SiteSettingsPayload(BaseModel):
    university_line: str
    submitted_by: str
    supervised_by: str


def _require_auth(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    email = auth.verify_token(authorization.removeprefix("Bearer ").strip())
    if email is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid, please log in again.")
    return email


@app.on_event("startup")
async def on_startup():
    db.init_db()


async def _proxy_predict(service_url: str, service_name: str, path: str, data: PatientInput) -> dict:
    if not service_url:
        raise HTTPException(status_code=503, detail=f"{service_name} service is not configured.")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(f"{service_url}{path}", json=data.model_dump())
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"{service_name} service unreachable: {exc}") from exc
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", f"{service_name} service error.")
        except ValueError:
            detail = f"{service_name} service error."
        raise HTTPException(status_code=resp.status_code, detail=detail)
    return resp.json()


@app.get("/")
async def root():
    return {"service": "Hair Fall Risk Prediction API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "catboost_configured": bool(CATBOOST_SERVICE_URL),
        "tabpfn_configured": bool(TABPFN_SERVICE_URL),
        "tabfm_configured": bool(TABFM_SERVICE_URL),
        "mongodb": db.get_db() is not None,
        "mongodb_error": db.connection_error,
    }


@app.get("/api/meta")
async def api_meta():
    return {
        "feature_groups": FEATURE_GROUPS,
        "feature_meta": FEATURE_META,
        "class_names": CLASS_NAMES,
        "tabpfn_available": bool(TABPFN_SERVICE_URL),
        "tabpfn_error": None if TABPFN_SERVICE_URL else "TABPFN_SERVICE_URL is not configured.",
        "tabfm_available": bool(TABFM_SERVICE_URL),
        "tabfm_error": None if TABFM_SERVICE_URL else "TABFM_SERVICE_URL is not configured.",
        "shap_images": {k: f"/static/shap_reference/{v}" for k, v in SHAP_IMAGES.items()},
        "shap_images_available": SHAP_IMAGES_AVAILABLE,
    }


@app.post("/api/auth/login")
async def api_login(payload: LoginRequest):
    user = await run_in_threadpool(db.get_user_by_email, payload.email)
    if user is None or not auth.verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {"token": auth.create_token(user["email"]), "email": user["email"]}


@app.get("/api/site-settings")
async def api_get_site_settings():
    stored = await run_in_threadpool(db.get_site_settings)
    return {**DEFAULT_SITE_SETTINGS, **(stored or {})}


@app.put("/api/site-settings")
async def api_update_site_settings(payload: SiteSettingsPayload, _email: str = Depends(_require_auth)):
    await run_in_threadpool(db.update_site_settings, payload.model_dump())
    return {**DEFAULT_SITE_SETTINGS, **payload.model_dump()}


@app.post("/api/predict/catboost")
async def api_predict_catboost(data: PatientInput):
    return await _proxy_predict(CATBOOST_SERVICE_URL, "CatBoost", "/api/predict/catboost", data)


@app.post("/api/predict/tabpfn")
async def api_predict_tabpfn(data: PatientInput):
    return await _proxy_predict(TABPFN_SERVICE_URL, "TabPFN", "/api/predict/tabpfn", data)


@app.post("/api/predict/tabfm")
async def api_predict_tabfm(data: PatientInput):
    return await _proxy_predict(TABFM_SERVICE_URL, "TabFM", "/api/predict/tabfm", data)


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
    limit = max(1, min(limit, 500))
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

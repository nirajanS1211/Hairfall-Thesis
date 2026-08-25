import logging
from pathlib import Path
from typing import Optional

from catboost import CatBoostClassifier
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool

from features import FEATURE_META
from schemas import CLASS_NAMES, FEATURE_COLUMNS, PatientInput, compute_warnings, to_dataframe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hairfall.catboost")

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

app = FastAPI(title="Hair Fall Risk Prediction API - CatBoost")

cb_model: Optional[CatBoostClassifier] = None
cb_explainer = None


def _load_model() -> None:
    """Runs after uvicorn has bound $PORT, so Render's port scan succeeds immediately."""
    global cb_model, cb_explainer

    cb_model = CatBoostClassifier()
    cb_model.load_model(str(MODELS_DIR / "catboost_model_production.cbm"))

    import shap

    cb_explainer = shap.TreeExplainer(cb_model)
    logger.info("CatBoost model and SHAP explainer loaded.")


@app.on_event("startup")
async def on_startup():
    await run_in_threadpool(_load_model)


def predict_catboost(data: PatientInput) -> dict:
    if cb_model is None or cb_explainer is None:
        raise HTTPException(status_code=503, detail="CatBoost model is still loading, try again shortly.")
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


@app.get("/")
async def root():
    return {"service": "Hair Fall Risk Prediction API - CatBoost", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "catboost": cb_model is not None}


@app.post("/api/predict/catboost")
async def api_predict_catboost(data: PatientInput):
    try:
        return await run_in_threadpool(predict_catboost, data)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("CatBoost prediction failed")
        raise HTTPException(status_code=500, detail=f"CatBoost prediction failed: {exc}") from exc

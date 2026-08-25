import json
from pathlib import Path
from typing import Literal, Optional

import pandas as pd
from pydantic import BaseModel, Field

from features import FEATURE_META

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

with open(MODELS_DIR / "feature_columns.json") as f:
    FEATURE_COLUMNS: list[str] = json.load(f)
with open(MODELS_DIR / "class_names.json") as f:
    CLASS_NAMES: list[str] = json.load(f)


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

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = BASE_DIR / "data" / "raw_dataset.csv"

GENDER_MAP = {"Female": 0, "F": 0, "Male": 1, "M": 1, "Other": 2, "O": 2}


def load_clean_dataset() -> pd.DataFrame:
    with open(BASE_DIR / "models" / "feature_columns.json") as f:
        feature_columns = json.load(f)

    df = pd.read_csv(RAW_CSV)
    df["gender"] = df["gender"].map(GENDER_MAP)

    if df["gender"].isnull().any():
        bad = df[df["gender"].isnull()]
        raise ValueError(f"Unmapped gender values found in {len(bad)} rows: {bad['gender'].unique()}")

    return df[feature_columns + ["hair_fall"]].reset_index(drop=True)


if __name__ == "__main__":
    clean = load_clean_dataset()
    print(clean.shape)
    print(clean["hair_fall"].value_counts().sort_index())
    print(clean.head())

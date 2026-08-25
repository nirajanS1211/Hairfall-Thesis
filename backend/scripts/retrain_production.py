import json
from pathlib import Path

from catboost import CatBoostClassifier

from clean_dataset import load_clean_dataset

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

PARAMS = dict(
    iterations=295,
    depth=4,
    learning_rate=0.1,
    loss_function="MultiClass",
    eval_metric="TotalF1",
    l2_leaf_reg=3,
    random_strength=1,
    bootstrap_type="Bayesian",
    border_count=254,
    random_seed=42,
    verbose=50,
)


def main():
    with open(MODELS_DIR / "feature_columns.json") as f:
        feature_columns = json.load(f)

    df = load_clean_dataset()
    X = df[feature_columns]
    y = df["hair_fall"]

    print(f"Training production CatBoost on {len(df)} rows...")
    model = CatBoostClassifier(**PARAMS)
    model.fit(X, y)
    out_path = MODELS_DIR / "catboost_model_production.cbm"
    model.save_model(str(out_path))
    print(f"Saved {out_path}")

    X.to_csv(MODELS_DIR / "tabpfn_context_X_full.csv", index=False)
    y.to_csv(MODELS_DIR / "tabpfn_context_y_full.csv", index=False)
    print(f"Saved tabpfn_context_X_full.csv / tabpfn_context_y_full.csv ({len(df)} rows each)")


if __name__ == "__main__":
    main()
